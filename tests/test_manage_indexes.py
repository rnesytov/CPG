from gateway.services import ManageIndexes


async def test_manage_indexes(app):
    await ManageIndexes(app)()

    assert await app.mongo.accounts.index_information() == {
        '_id_': {
            'v': 2,
            'key': [('_id', 1)],
            'ns': 'bpg_test.accounts'
        },
        'address_1': {
            'v': 2,
            'key': [('address', 1)],
            'ns': 'bpg_test.accounts',
        }
    }

    assert await app.mongo.notifications.index_information() == {
        '_id_': {
            'key': [('_id', 1)],
            'ns': 'bpg_test.notifications',
            'v': 2,
        },
        'created_at_1': {
            'key': [('created_at', 1)],
            'ns': 'bpg_test.notifications',
            'v': 2,
            'sparse': True
        },
        'tx_id_1': {
            'key': [('tx_id', 1)],
            'ns': 'bpg_test.notifications',
            'v': 2,
        }
    }

    assert await app.mongo.tx_outputs.index_information() == {
        '_id_': {
            'key': [('_id', 1)],
            'ns': 'bpg_test.tx_outputs',
            'v': 2,
        },
        'tx_id_1_tx_hash_1': {
            'key': [('tx_id', 1), ('tx_hash', 1)],
            'ns': 'bpg_test.tx_outputs',
            'v': 2,
            'unique': True
        }
    }
