from datetime import datetime
from freezegun import freeze_time


async def test_invalid_api_key(client):
    response = await client.post('/api/get_account/')

    assert response.status == 403
    assert await response.json() == {'error': 'invalid api key'}


async def test_ping(client):
    response = await client.get('/ping/')

    assert response.status == 200
    assert await response.text() == 'pong'


@freeze_time('2018-09-01')
async def test_get_address(app, client_w_token):
    response = await client_w_token.post('/api/get_account/', data={'notify_url': 'http://localhost:80/notify'})
    assert response.status == 200

    json = await response.json()
    assert json == {'success': True, 'account': 'ms1kWBYg35mCCsfaSEXaGiYegk9JsYkbEJ'}

    assert await app.accounts_repo.count() == 1
    account = await app.accounts_repo.find_one({})
    assert account.serialize() == {
        '_id': account.id,
        'address': 'ms1kWBYg35mCCsfaSEXaGiYegk9JsYkbEJ',
        'created_at': datetime.utcnow(),
        'notify_url': 'http://localhost:80/notify',
        'child_id': 1,
        'sync': True
    }


async def test_invalid_notify_url(app, client_w_token):
    response = await client_w_token.post('/api/get_account/', data={'notify_url': 'foobar'})

    assert response.status == 400
    assert await response.json() == {'error': 'notify_url is invalid'}
    assert await app.accounts_repo.count() == 0
