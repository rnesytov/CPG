from aiorpcx import ClientSession, JSONRPCv2, JSONRPCConnection


def create_electrumx_session(app):
    connection = JSONRPCConnection(JSONRPCv2)
    electrum_config = app.config.electrum

    return ClientSession(host=electrum_config.host, port=electrum_config.port, connection=connection)
