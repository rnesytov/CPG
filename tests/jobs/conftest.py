import pytest
from collections import namedtuple
from aiorpcx import ServerSession, Server


ElectrumxRequestStub = namedtuple('ElectrumxRequestStub', ['method', 'args', 'response'])


class ElectrumxSessionStub(ServerSession):
    current_session = None
    _stubs = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ElectrumxSessionStub.current_session = self

    def _find_stub(self, request):
        for stub in self._stubs:
            if stub.method == request.method and stub.args == request.args:
                self._stubs.remove(stub)

                return stub

    async def handle_request(self, request):
        stub = self._find_stub(request)

        if stub:
            return stub.response
        else:
            raise RuntimeError(f'Leaked electrumx {request.method} call with args {request.args}')

    @classmethod
    def stub_request(cls, method, args, response):
        cls._stubs.append(ElectrumxRequestStub(method, args, response))

    @classmethod
    def stub_server_version(cls):
        cls.stub_request('server.version', ['CPG', ['1.4', '1.4']], ["ElectrumX 3.0.6", "1.4"])

    @classmethod
    def clear(cls):
        cls.current_session = None
        cls._stubs = []


def stub_electrum_config(app, server):
    app.config['electrum']['host'] = server.host
    app.config['electrum']['port'] = server.port


@pytest.fixture
def electrumx_server(loop, aiohttp_unused_port, app):
    port = aiohttp_unused_port()

    server = Server(ElectrumxSessionStub, 'localhost', port, loop=loop)
    loop.run_until_complete(server.listen())
    stub_electrum_config(app, server)

    yield server

    ElectrumxSessionStub.clear()
    loop.run_until_complete(server.close())
