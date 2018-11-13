from datetime import datetime

from gateway.jobs.job import Job
from gateway.structs import Account


class DeactivateUnusedAccounts(Job):
    async def get_accounts(self, accounts_batch_size, max_unused_days):
        accounts_cursor = self.app.accounts_repo.for_sync()
        accounts = await accounts_cursor.to_list(accounts_batch_size)

        count = 0
        for account in accounts:
            account = Account.from_kwargs(**account)
            days_unused = (datetime.now() - account.last_txn_at).days

            if days_unused > max_unused_days:
                account.sync = False
                await self.app.accounts_repo.save(account)
                count += 1

        return count

    async def __call__(self):
        try:
            count = await self.get_accounts(
                self.job_settings.accounts_batch_size,
                self.job_settings.days_for_unused_accounts_to_exist,
            )
            self.logger.info(f'Marked as deactivated {count} account(s)')
        except Exception as e:
            self.logger.error('Error while deactivating unused accounts', exc_info=e)
