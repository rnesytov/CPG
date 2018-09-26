from gateway.repositories.accounts import AccountsRepository
from gateway.repositories.tx_outputs import TxOutputsRepository
from gateway.repositories.notifications import NotificationsRepository


async def setup_repositories(app):
    app.accounts_repo = AccountsRepository(app)
    app.tx_outputs_repo = TxOutputsRepository(app)
    app.notifications_repo = NotificationsRepository(app)

    yield
