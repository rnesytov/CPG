from datetime import datetime
from gateway.structs.struct import Struct
from bson.objectid import ObjectId


class TxOutput(Struct):
    _id: ObjectId
    address: str
    tx_hash: str
    value: int
    tx_id: str
    locktime: int
    position: int
    block_hash: str
    confirmations: int
    blocktime: int
    created_at: datetime

    @classmethod
    def from_kwargs(cls, **kwargs):
        attributes = {
            'address': None,
            'tx_hash': None,
            'value': None,
            'tx_id': None,
            'locktime': None,
            'position': None,
            'block_hash': None,
            'confirmations': 0,
            'blocktime': None,
            'created_at': datetime.utcnow(),
        }

        attributes.update(kwargs)

        return cls(attributes=attributes)
