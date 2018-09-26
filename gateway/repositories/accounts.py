from gateway.repositories.repository import Repository
from gateway.structs import Account


class AccountsRepository(Repository):
    structclass = Account
    collection_name = 'accounts'

    def for_sync(self):
        return self.collection.find({'sync': True})
