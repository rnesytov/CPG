import asyncio
import hmac
import hashlib
import aiohttp
import paco

from datetime import timedelta, datetime
from urllib.parse import urlencode

from gateway.jobs.job import Job
from gateway.structs.notification import NotificationFailure


class SendNotifications(Job):
    RESPONSE_TEXT_SLICE = 300

    def build_payload(self, notification):
        data = dict(tx_id=notification.tx_id, code=notification.code, **notification.txn_data)

        return urlencode(data).encode('utf8')

    def build_signature(self, payload):
        secret = self.app.config.notifications_secret.encode('utf8')
        signature = hmac.new(secret, payload, hashlib.sha512)

        return signature.hexdigest()

    async def mark_as_sent(self, notification):
        notification.sent = True

        await self.app.notifications_repo.save(notification)

        self.logger.info(f'{notification} successfully sent')

    async def mark_as_failed(self, notification, failure):
        notification.failures.append(failure.as_dict())

        if notification.attempts >= self.job_settings.max_attempts:
            notification.failed = True
        else:
            notification.attempts = notification.attempts + 1
            notification.next_send = datetime.utcnow() + timedelta(seconds=self.job_settings.retry_after)

        await self.app.notifications_repo.save(notification)

        self.logger.info(f'{notification} was not sent due to {failure}')

    async def is_response_valid(self, response):
        return response.status == 200 and await response.text() == 'OK'

    async def _build_response_failure(self, response):
        text = await response.text()

        return NotificationFailure(failure_type='invalid_response',
                                   data={
                                       'status': response.status,
                                       'text': text[:self.RESPONSE_TEXT_SLICE]
                                   })

    async def send_notification(self, raw_notification):
        notification = await self.app.notifications_repo.find_one({'_id': raw_notification['id']})

        payload = self.build_payload(notification)
        headers = {'CPG_SIGN': self.build_signature(payload),
                   'Content-Type': 'application/x-www-form-urlencoded'}
        timeout = aiohttp.ClientTimeout(total=self.job_settings.request_timeout)

        async with aiohttp.ClientSession(timeout=timeout,
                                         headers=headers) as session:
            try:
                response = await session.post(notification.url, data=payload)

                if await self.is_response_valid(response):
                    await self.mark_as_sent(notification)
                else:
                    failure = await self._build_response_failure(response)
                    await self.mark_as_failed(notification, failure)

            except aiohttp.ClientError as e:
                failure = NotificationFailure(failure_type='client_error',
                                              data=str(e))
                await self.mark_as_failed(notification, failure)
            except asyncio.TimeoutError as e:
                failure = NotificationFailure(failure_type='request_timeout')
                await self.mark_as_failed(notification, failure)

    async def __call__(self):
        notifications_cursor = self.app.notifications_repo.for_send(self.job_settings.max_attempts)

        notifications = await notifications_cursor.to_list(self.job_settings.notifications_batch_size)
        while notifications:
            await paco.map(self.send_notification, notifications)

            notifications = await notifications_cursor.to_list(self.job_settings.notifications_batch_size)
