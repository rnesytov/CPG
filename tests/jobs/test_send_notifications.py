# pylint: disable=redefined-outer-name
import asyncio
import pytest
from collections import namedtuple
from aiohttp.web_response import Response
from datetime import datetime, timedelta
from freezegun import freeze_time

from gateway.jobs import SendNotifications
from gateway.structs import Notification


NotificationStub = namedtuple('NotificationStub',
                              ['signature', 'data', 'response_status', 'response_body', 'timeout'])


class NotificationHandler:
    def __init__(self):
        self._stubs = []
        self.requests_received = 0

    def stub_post_notification(self, signature, data, response_status, response_body, timeout=None):
        self._stubs.append(NotificationStub(signature, data, response_status, response_body, timeout))

    async def _find_stub(self, request):
        data = await request.post()
        signature = request.headers.get('CPG_SIGN')

        for stub in self._stubs:
            if data and data == stub.data and signature and signature == stub.signature:
                self._stubs.remove(stub)

                return stub

    async def __call__(self, request):
        self.requests_received += 1
        stub = await self._find_stub(request)

        if stub:
            if stub.timeout:
                await asyncio.sleep(stub.timeout)

            return Response(status=stub.response_status, body=stub.response_body)
        else:
            raise RuntimeError(f'Leaked request {request}')


@pytest.fixture
def notifications_handler():
    return NotificationHandler()


@pytest.fixture
async def notifications_receiver(notifications_handler, aiohttp_raw_server):
    server = await aiohttp_raw_server(handler=notifications_handler)

    return server


@pytest.fixture
def notifications_url(notifications_receiver):
    return str(notifications_receiver.make_url(''))


@pytest.fixture
@freeze_time('2018-09-01')
async def notification(app, notifications_url):
    notification = Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': []
    })
    await app.notifications_repo.save(notification)

    return notification


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('notification')
async def test_successful_send(app, notifications_handler, notifications_url):
    notifications_handler.stub_post_notification(
        data={
            'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
            'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
            'code': '100',
            'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
            'confirmations': '6',
            'value': '0.39654376'
        },
        signature='e9d9b8dd920acb8bc3cb6878f15e178569aff0e66b9545bd6d64f77e3ff27568'
                  '0a6462f93ef8b5bbf1ea06fba9b68f6d8d97de3a3218049ae0236daff52a5e0f',
        response_status=200,
        response_body='OK')

    await SendNotifications(app=app)()

    assert notifications_handler.requests_received == 1

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': True,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': []
    }


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('notification')
async def test_invalid_status_code(app, notifications_handler, notifications_url):
    notifications_handler.stub_post_notification(
        data={
            'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
            'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
            'code': '100',
            'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
            'confirmations': '6',
            'value': '0.39654376'
        },
        signature='e9d9b8dd920acb8bc3cb6878f15e178569aff0e66b9545bd6d64f77e3ff27568'
                  '0a6462f93ef8b5bbf1ea06fba9b68f6d8d97de3a3218049ae0236daff52a5e0f',
        response_status=500,
        response_body='Server error')

    await SendNotifications(app=app)()

    assert notifications_handler.requests_received == 1

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow() + timedelta(seconds=15),
        'attempts': 1,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': [
            {
                'created_at': datetime.utcnow(),
                'data': {'status': 500, 'text': 'Server error'},
                'failure_type': 'invalid_response'
            }
        ]
    }


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('notification')
async def test_request_timeout(app, notifications_handler, notifications_url):
    notifications_handler.stub_post_notification(
        data={
            'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
            'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
            'code': '100',
            'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
            'confirmations': '6',
            'value': '0.39654376'
        },
        signature='e9d9b8dd920acb8bc3cb6878f15e178569aff0e66b9545bd6d64f77e3ff27568'
                  '0a6462f93ef8b5bbf1ea06fba9b68f6d8d97de3a3218049ae0236daff52a5e0f',
        response_status=200,
        response_body='OK',
        timeout=5)

    await SendNotifications(app=app)()

    assert notifications_handler.requests_received == 1

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow() + timedelta(seconds=15),
        'attempts': 1,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': [
            {
                'created_at': datetime.utcnow(),
                'failure_type': 'request_timeout'
            }
        ]
    }


@freeze_time('2018-09-01')
async def test_connection_error(app, aiohttp_unused_port):
    port = aiohttp_unused_port()
    url = f'http://localhost:{port}'
    notification = Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': url,
        'failures': []
    })
    await app.notifications_repo.save(notification)

    await SendNotifications(app=app)()

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow() + timedelta(seconds=15),
        'attempts': 1,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': url,
        'failures': [
            {
                'created_at': datetime.utcnow(),
                'failure_type': 'client_error',
                'data': f"Cannot connect to host localhost:{port} ssl:None [Connect call failed ('127.0.0.1', {port})]"
            }
        ]
    }


@freeze_time('2018-09-01')
async def test_mark_failed(app, aiohttp_unused_port):
    port = aiohttp_unused_port()
    url = f'http://localhost:{port}'
    notification = Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 10,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': url,
        'failures': [
            {
                'created_at': datetime.utcnow(),
                'failure_type': 'request_timeout'
            }
        ]
    })
    await app.notifications_repo.save(notification)

    await SendNotifications(app=app)()

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': True,
        'next_send': datetime.utcnow(),
        'attempts': 10,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': url,
        'failures': [
            {
                'created_at': datetime.utcnow(),
                'failure_type': 'request_timeout'
            },
            {
                'created_at': datetime.utcnow(),
                'failure_type': 'client_error',
                'data': f"Cannot connect to host localhost:{port} ssl:None [Connect call failed ('127.0.0.1', {port})]"
            }
        ]
    }


@freeze_time('2018-09-01')
async def test_dont_resend_failed(app, notifications_handler, notifications_url):
    notification = Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': True,
        'next_send': datetime.utcnow(),
        'attempts': 10,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': []
    })
    await app.notifications_repo.save(notification)

    notifications_handler.stub_post_notification(
        data={
            'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
            'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
            'code': '100',
            'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
            'confirmations': '6',
            'value': '0.39654376'
        },
        signature='683024d5df432da32291bd5ded2e38cf9bc803e54566c6154269845ed960c564'
                  '342e1b8b9c9131542143d497655d8d98c5b37c20b759907bec0841e1c1017e3e',
        response_status=200,
        response_body='OK')

    await SendNotifications(app=app)()

    assert notifications_handler.requests_received == 0

    assert await app.notifications_repo.count() == 1
    assert await app.notifications_repo.find_one() == notification


@freeze_time('2018-09-01')
async def test_check_next_send(app, notifications_handler, notifications_url):
    notification = Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow() + timedelta(seconds=1),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': notifications_url,
        'failures': []
    })
    await app.notifications_repo.save(notification)

    notifications_handler.stub_post_notification(
        data={
            'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
            'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
            'code': '100',
            'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
            'confirmations': '6',
            'value': '0.39654376'
        },
        signature='683024d5df432da32291bd5ded2e38cf9bc803e54566c6154269845ed960c564'
        '342e1b8b9c9131542143d497655d8d98c5b37c20b759907bec0841e1c1017e3e',
        response_status=200,
        response_body='OK')

    await SendNotifications(app=app)()

    assert notifications_handler.requests_received == 0

    assert await app.notifications_repo.count() == 1
    assert await app.notifications_repo.find_one() == notification
