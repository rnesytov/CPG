# pylint: disable=redefined-outer-name
import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time
from tests.jobs.conftest import ElectrumxSessionStub
from gateway.jobs import SyncTxOutputs
from gateway.structs import Account, TxOutput, Notification


@pytest.fixture
async def account(app):
    acc = Account.from_kwargs(address='mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                              notify_url='localhost:8080/notify')

    await app.accounts_repo.save(acc)

    return acc


@pytest.fixture
def list_unspent_response():
    return [
        {
            "height": 1412996,
            "tx_hash": "25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60",
            "tx_pos": 1,
            "value": 39654376
        }
    ]


@pytest.fixture
def transaction_response():
    return {
        "blockhash": "000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e",
        "blocktime": 1536681241,
        "confirmations": 6,
        "hash": "5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46",
        "hex": "02000000000101a91e5a421c45b5a54c913aaa31c7c76f26d7248c43bfc9f11761d081d4aea52b0000000017160014a3ac74"
               "1d09f029cd640507924ee3ee791e1f6a65feffffff028a8616107100000017a914ebfff6b6a7a9539ae1cf919a395c20d978"
               "407e5c87e8135d02000000001976a914acec2871455b964ddb2a5c37bb771ecb4272d61288ac02483045022100921a849de0"
               "7a8f97b6927d52181f52707f42fc1850097d6d5ff8ea23dfdb3bfc02200a42f558cf9125dffcafba3b840625275c3d0520c4"
               "132eb306c790ce0f40b95d01210291a22c0b778a05a5878ef99f99b9a15d89ba6e38137e0ca6a7d9606827e79aec7b8f1500",
        "locktime": 1412987,
        "size": 250,
        "time": 1536681241,
        "txid": "25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60",
        "version": 2,
        "vin": [
            {
                "scriptSig": {
                    "asm": "0014a3ac741d09f029cd640507924ee3ee791e1f6a65",
                    "hex": "160014a3ac741d09f029cd640507924ee3ee791e1f6a65"
                },
                "sequence": 4294967294,
                "txid": "2ba5aed481d06117f1c9bf438c24d7266fc7c731aa3a914ca5b5451c425a1ea9",
                "txinwitness": [
                    "3045022100921a849de07a8f97b6927d52181f52707f42fc1850097d6d5ff8ea23dfdb3bfc022"
                    "00a42f558cf9125dffcafba3b840625275c3d0520c4132eb306c790ce0f40b95d01",
                    "0291a22c0b778a05a5878ef99f99b9a15d89ba6e38137e0ca6a7d9606827e79aec"
                ],
                "vout": 0
            }
        ],
        "vout": [
            {
                "n": 0,
                "scriptPubKey": {
                    "addresses": [
                        "2NEm5R31aeZgeAC1YYM5MnGSHvn37fumjGL"
                    ],
                    "asm": "OP_HASH160 ebfff6b6a7a9539ae1cf919a395c20d978407e5c OP_EQUAL",
                    "hex": "a914ebfff6b6a7a9539ae1cf919a395c20d978407e5c87",
                    "reqSigs": 1,
                    "type": "scripthash"
                },
                "value": 4856.01216138
            },
            {
                "n": 1,
                "scriptPubKey": {
                    "addresses": [
                        "mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9"
                    ],
                    "asm": "OP_DUP OP_HASH160 acec2871455b964ddb2a5c37bb771ecb4272d612 OP_EQUALVERIFY OP_CHECKSIG",
                    "hex": "76a914acec2871455b964ddb2a5c37bb771ecb4272d61288ac",
                    "reqSigs": 1,
                    "type": "pubkeyhash"
                },
                "value": 0.39654376
            }
        ],
        "vsize": 168
    }


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server', 'account')
async def test_successful_sync(app, list_unspent_response, transaction_response):
    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1
    tx_output = await app.tx_outputs_repo.find_one()
    assert tx_output.serialize() == {
        '_id': tx_output.id,
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 6,
        'created_at': datetime.utcnow(),
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': 'localhost:8080/notify',
        'failures': []
    }


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server', 'account')
async def test_already_processed_tx_output(app, list_unspent_response, transaction_response):
    tx_output = await app.tx_outputs_repo.save(TxOutput({
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 6,
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }))
    notification = await app.notifications_repo.save(Notification({
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 6,
                     'value': 0.39654376},
        'url': 'localhost:8080/notify',
        'failures': []
    }))

    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1
    assert await app.tx_outputs_repo.find_one() == tx_output
    assert await app.notifications_repo.count() == 1
    assert await app.notifications_repo.find_one() == notification


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server', 'account')
async def test_update_tx_output(app, list_unspent_response, transaction_response):
    tx_output = await app.tx_outputs_repo.save(TxOutput({
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 2,
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }))
    await app.notifications_repo.save(Notification({
        'code': 22,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 2,
                     'value': 0.39654376},
        'url': 'localhost:8080/notify',
        'failures': []
    }))

    transaction_response['confirmations'] = 4

    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1
    tx_output = await app.tx_outputs_repo.find_one()
    assert tx_output.serialize() == {
        '_id': tx_output.id,
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 4,
        'created_at': datetime.utcnow(),
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }

    assert await app.notifications_repo.count() == 2


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server', 'account')
async def test_unexpected_error(app, list_unspent_response, transaction_response):
    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    with mock.patch('gateway.services.process_transaction.ProcessTransaction.create_notification') as find_one_mock:
        find_one_mock.side_effect = Exception()
        await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1  # should be zero
    assert await app.notifications_repo.count() == 0


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server', 'account')
async def test_hundred_confirmations(app, list_unspent_response, transaction_response):
    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    transaction_response['confirmations'] = 100
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1
    tx_output = await app.tx_outputs_repo.find_one()
    assert tx_output.serialize() == {
        '_id': tx_output.id,
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 100,
        'created_at': datetime.utcnow(),
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }

    assert await app.notifications_repo.count() == 1
    notification = await app.notifications_repo.find_one()

    assert notification.serialize() == {
        '_id': notification.id,
        'code': 100,
        'created_at': datetime.utcnow(),
        'failed': False,
        'next_send': datetime.utcnow(),
        'attempts': 0,
        'sent': False,
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'txn_data': {'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                     'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
                     'confirmations': 100,
                     'value': 0.39654376},
        'url': 'localhost:8080/notify',
        'failures': []
    }


@freeze_time('2018-09-01')
@pytest.mark.usefixtures('electrumx_server')
async def test_update_accounts_last_txn_at(app, list_unspent_response, transaction_response):
    await app.tx_outputs_repo.save(TxOutput({
        'block_hash': '000000004c3604d758cba41c30c1f2be2ffa3e730a3017ded08078dc422a614e',
        'blocktime': 1536681241,
        'confirmations': 0,
        'locktime': 1412987,
        'position': 1,
        'tx_hash': '5f7d66d9f36dacf150320bedd35d2f601754a31be78ccc7b6be795ed8a518b46',
        'tx_id': '25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60',
        'address': 'mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
        'value': 0.39654376
    }))
    acc = Account.from_kwargs(address='mwHHRbLcC394T7vsLQZVh8FsB3QkDNRKK9',
                              notify_url='localhost:8080/notify',
                              last_txn_at=datetime.now() - timedelta(days=6))

    account = await app.accounts_repo.save(acc)

    ElectrumxSessionStub.stub_server_version()
    ElectrumxSessionStub.stub_request('blockchain.scripthash.listunspent',
                                      ['da22c9488b0d4828b4bc96ad6ff41c274bc9e1632482673cc4c07a0a1a8fcebc'],
                                      list_unspent_response)
    ElectrumxSessionStub.stub_request('blockchain.transaction.get',
                                      ['25705000a564b7852947faa1fea2987143410bb3ada53458b6eead67e7469d60', True],
                                      transaction_response)

    await SyncTxOutputs(app=app)()

    assert await app.tx_outputs_repo.count() == 1
    assert await app.accounts_repo.count() == 1

    account = await app.accounts_repo.find_one({'_id': account.id})
    assert account.last_txn_at == datetime.now()
