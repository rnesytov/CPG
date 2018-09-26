from datetime import datetime
from gateway.structs.struct import Struct
from bson.objectid import ObjectId


class NotificationFailure:
    def __init__(self, failure_type, data=None, created_at=None):
        self.failure_type = failure_type
        self.data = data
        self.created_at = created_at or datetime.utcnow()

    def as_dict(self):
        result = {'failure_type': self.failure_type, 'created_at': self.created_at}

        if self.data:
            result['data'] = self.data

        return result

    def __str__(self):
        return f'{self.__class__.__name__}(failure_type={self.failure_type}, ' \
            'data={self.data}, created_at={self.created_at})'


class Notification(Struct):
    _id: ObjectId
    tx_id: str
    url: str
    txn_data: dict
    attempts: int
    failed: bool
    sent: bool
    code: int
    created_at: datetime
    next_send: datetime
    failures: list

    NOTIFICATION_TYPES = {
        'TX_IN_POOL': 10,
        'TX_MINED': 20,
        'TX_CONFIRMED': 100
    }

    @classmethod
    def from_kwargs(cls, **kwargs):
        attributes = {
            'tx_id': None,
            'url': None,
            'txn_data': {},
            'attempts': 0,
            'sent': False,
            'failed': False,
            'code': None,
            'created_at': datetime.utcnow(),
            'next_send': datetime.utcnow(),
            'failures': []
        }

        attributes.update(kwargs)

        return cls(attributes=attributes)
