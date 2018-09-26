from gateway.views import ping


def setup_routes(app, handler):
    router = app.router

    router.add_post('/api/get_account/', handler.get_account, name='get_account')
    router.add_get('/ping/', ping, name='ping')
