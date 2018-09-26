import asyncio

from aiohttp import web
from gateway.app import create_app

DEFAULT_PORT = 8080


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app())

    web.run_app(app, port=DEFAULT_PORT)


if __name__ == '__main__':
    main()
