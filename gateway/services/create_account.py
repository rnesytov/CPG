from gateway.utils import bip32
from gateway.structs import Account


class MaxBlockHeightNotFound(Exception):
    pass


class CreateAccount:
    CHILD_ID_INCREMENT = 1

    def __init__(self, app):
        self.app = app

    async def get_child_id(self):
        max_child_id = await self.app.accounts_repo.find_max('child_id', default=0)

        return max_child_id + self.CHILD_ID_INCREMENT

    def get_address(self, child_id):
        pub_key, _ = bip32.from_extended_key_string(self.app.config.wallet_pubkey)
        coin = self.app.config.coin_class

        derived_pub_key = pub_key.child(child_id)

        return derived_pub_key.address(coin)

    async def __call__(self, notify_url):
        child_id = await self.get_child_id()
        address = self.get_address(child_id)

        account = Account.from_kwargs(notify_url=notify_url,
                                      address=address,
                                      child_id=child_id)

        await self.app.accounts_repo.save(account)

        return account
