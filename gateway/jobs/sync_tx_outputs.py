from hashlib import sha256

import paco

from gateway.jobs.job import Job
from gateway.electrumx_session import create_electrumx_session
from gateway.structs import Account
from gateway.utils import flatten
from gateway.services import ProcessTransaction


class SyncTxOutputs(Job):
    def __init__(self, app):
        super().__init__(app)

        self.coin = app.config.coin_class
        self.tx_processor = ProcessTransaction(app)

    def build_script_hash(self, address):
        script = self.coin.pay_to_address_script(address)

        script_hash = sha256(script).digest()

        return script_hash[::-1].hex()

    async def get_listunspent(self, script_hash, ex_session):
        return await ex_session.send_request('blockchain.scripthash.listunspent', [script_hash])

    async def get_transaction(self, tx_hash, ex_session):
        return await ex_session.send_request('blockchain.transaction.get', [tx_hash, True])

    def check_vout(self, vout, address):
        script = vout['scriptPubKey']

        return script['type'] == 'pubkeyhash' and script['addresses'] == [address]

    async def process_unspent(self, unspent, account, ex_session):
        tx_id = unspent['tx_hash']

        if await self.app.tx_outputs_repo.is_processed(tx_id):
            return

        transaction = await self.get_transaction(tx_id, ex_session)

        for vout in transaction['vout']:
            if self.check_vout(vout, account.address):
                return await self.tx_processor(vout, transaction, account)

    async def process_account(self, raw_account, ex_session):
        account = Account(raw_account)
        script_hash = self.build_script_hash(account.address)

        list_unspent = await self.get_listunspent(script_hash, ex_session)

        return await paco.map(self.process_unspent, list_unspent,
                              return_exceptions=True, account=account, ex_session=ex_session)

    def log_results(self, results):
        count = 0
        for result in flatten(results):
            if result:
                if isinstance(result, Exception):
                    self.logger.error('Error while syncing transactions', exc_info=result)
                else:
                    count += 1

        if count > 0:
            self.logger.info(f'Synced {count} transaction(s)')

    async def __call__(self):
        accounts_cursor = self.app.accounts_repo.for_sync()
        results = []

        async with create_electrumx_session(self.app) as ex_session:
            await self.set_protocol_version(ex_session)

            accounts = await accounts_cursor.to_list(self.job_settings.accounts_batch_size)
            while accounts:
                results.append(await paco.map(self.process_account, accounts,
                                              return_exceptions=True, ex_session=ex_session))

                accounts = await accounts_cursor.to_list(self.job_settings.accounts_batch_size)

        self.log_results(results)
