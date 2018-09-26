from gateway.structs import Notification, TxOutput


class ProcessTransaction:
    def __init__(self, app):
        self.app = app

    async def create_or_update_tx_output(self, vout, transaction, account):
        tx_output = TxOutput.from_kwargs(address=account.address,
                                         tx_hash=transaction['hash'],
                                         value=vout['value'],
                                         tx_id=transaction['txid'],
                                         locktime=transaction['locktime'],
                                         position=vout['n'],
                                         block_hash=transaction.get('blockhash'),
                                         confirmations=transaction.get('confirmations'),
                                         blocktime=transaction.get('blocktime'))

        tx_output, result = await self.app.tx_outputs_repo.replace_one(
            {'tx_id': transaction['txid']}, tx_output, upsert=True
        )

        return tx_output, result.upserted_id or result.modified_count == 1

    async def create_notification(self, tx_output, account):
        if tx_output.confirmations is not None:
            if tx_output.confirmations >= self.app.config.confirmations_required:
                notify_code = Notification.NOTIFICATION_TYPES['TX_CONFIRMED']
            else:
                notify_code = Notification.NOTIFICATION_TYPES['TX_MINED'] + tx_output.confirmations
        else:
            notify_code = Notification.NOTIFICATION_TYPES['TX_IN_POOL']

        if await self.app.notifications_repo.find_one({'tx_id': tx_output.tx_id,
                                                       'code': notify_code}) is None:
            notification = Notification.from_kwargs(tx_id=tx_output.tx_id,
                                                    url=account.notify_url,
                                                    code=notify_code,
                                                    txn_data={'value': tx_output.value,
                                                              'address': account.address,
                                                              'block_hash': tx_output.block_hash,
                                                              'confirmations': tx_output.confirmations})

            await self.app.notifications_repo.save(notification)

    async def __call__(self, vout, transaction, account):
        tx_output, new_or_modified = await self.create_or_update_tx_output(vout, transaction, account)

        if new_or_modified:
            notification = await self.create_notification(tx_output, account)

            return {'tx_output': tx_output, 'notification': notification}
