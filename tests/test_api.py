import json

import pytest

from rStream.api import app


@pytest.fixture
def client():
    return app.test_client()


def test_root_response_is_200(client):
    response = client.get('/')
    assert '200' in response.status


def test_subreddit_selection(client):
    test_subs = ['1', '2', '3']
    url = '/' + '+'.join(test_subs)
    response = client.get(url)
    raw = response.data.decode('utf8')
    results = json.loads(raw)
    assert results['SubsSelected'] == test_subs
