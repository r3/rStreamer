import pytest

from rStream.api import app


@pytest.fixture
def client():
    return app.test_client()


def test_root_response_is_200(client):
    response = client.get('/')
    assert '200' in response.status
