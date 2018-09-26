import asyncio

from aiohttp import web
from aiohttp.web_response import Response
from gateway.services import CreateAccount
from gateway.utils import is_url


API_KEY_HEADER = 'CPG_API_KEY'


class ApiHandler:
    def __init__(self, app):
        self.app = app

    def check_api_key(self, request):
        request_api_key = request.headers.get(API_KEY_HEADER)

        return request_api_key and request_api_key == self.app.config.api_key

    async def get_account(self, request):
        post = await request.post()

        if not self.check_api_key(request):
            return web.json_response({'error': 'invalid api key'}, status=403)

        if 'notify_url' not in post:
            return web.json_response({'error': 'notify_url is not set'}, status=400)

        notify_url = post['notify_url']

        if not is_url(notify_url):
            return web.json_response({'error': 'notify_url is invalid'}, status=400)

        account = await asyncio.shield(CreateAccount(self.app)(notify_url))

        return web.json_response({
            'success': True,
            'account': account.address
        })


async def ping(_):
    return Response(text='pong')
