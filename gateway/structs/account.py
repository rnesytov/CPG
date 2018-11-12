from datetime import datetime
from gateway.structs.struct import Struct
from bson.objectid import ObjectId


class Account(Struct):
    _id: ObjectId
    address: str
    created_at: datetime
    notify_url: str
    child_id: str
    sync: bool
    last_txn_at: datetime

    @classmethod
    def from_kwargs(cls, **kwargs):
        attributes = {
            'address': None,
            'currency': None,
            'created_at': datetime.utcnow(),
            'notify_url': None,
            'path': None,
            'sync': True,
            'last_txn_at': datetime.utcnow()
        }

        attributes.update(kwargs)

        return cls(attributes=attributes)
