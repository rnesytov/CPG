from datetime import datetime
from gateway.repositories.repository import Repository
from gateway.structs import Notification


class NotificationsRepository(Repository):
    structclass = Notification
    collection_name = 'notifications'

    def for_send(self, max_attempts):
        return self.collection.aggregate(
            [
                {
                    '$match': {
                        'failed': False,
                        'sent': False,
                        'attempts': {
                            '$lte': max_attempts
                        },
                        'next_send': {
                            '$lte': datetime.utcnow()
                        }
                    }
                }, {
                    '$sort': {
                        'code': 1
                    }
                }, {
                    '$group': {
                        '_id': '$tx_id',
                        'id': {
                            '$first': '$_id'
                        }
                    }
                }
            ])
