from gateway.repositories.repository import Repository
from gateway.structs import TxOutput


class TxOutputsRepository(Repository):
    structclass = TxOutput
    collection_name = 'tx_outputs'

    async def is_processed(self, tx_id):
        return await self.find_one({
            'tx_id': tx_id,
            'confirmations': {'$gte': self.app.config.confirmations_required}
        }) is not None
