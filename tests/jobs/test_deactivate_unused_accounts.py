import pytest
from freezegun import freeze_time

from gateway.structs import Account
from gateway.jobs import DeactivateUnusedAccounts


@pytest.fixture
async def new_account(app):
    acc = Account.from_kwargs(address='mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                              notify_url='localhost:8080/notify')

    await app.accounts_repo.save(acc)

    return acc


@pytest.fixture
@freeze_time('2018-09-01')
async def old_account(app):
    acc = Account.from_kwargs(address='owHHRbLcC394T7vsLQZVh8FsB3QkDNRLK9',
                              notify_url='localhost:8080/notify/fs')

    await app.accounts_repo.save(acc)

    return acc


async def test_account_datetime_filter(app, new_account, old_account):
    assert new_account.sync and old_account.sync

    await DeactivateUnusedAccounts(app=app)()

    old_account = await app.accounts_repo.find_one({'_id': old_account.id})
    new_account = await app.accounts_repo.find_one({'_id': new_account.id})
    assert new_account.sync
    assert not old_account.sync
