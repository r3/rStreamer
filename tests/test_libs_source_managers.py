import pytest

from rStream.libs import source_managers


@pytest.mark.parametrize('test_url,expected_extension', [
    ('http://test.com/', ''),
    ('http://test.com/foo', ''),
    ('http://test.com/foo.bar', '.bar'),
    ('http://test.com/foo.bar?baz', '.bar'),
    ('http://test.com/foo.bar?baz=qux', '.bar'),
    ('http://test.com/foo.bar?baz=qux&lorem=ipsem', '.bar'),
])
def test_ext_from_url(test_url, expected_extension):
    assert source_managers.ext_from_url(test_url) == expected_extension


class TestDirectLink():
    @pytest.fixture()
    def manager(self):
        return source_managers.DirectLinkManager()

    def test_config_on_instantiation(self, mocker):
        mocker.spy(source_managers.DirectLinkManager, 'configure')
        source_managers.DirectLinkManager()
        assert source_managers.DirectLinkManager.configure.call_count == 1

    def test_is_configured(self, manager):
        assert source_managers.DirectLinkManager._config

    def test_accepted_extensions_exists(self, manager):
        assert manager.accepted_extensions

    @pytest.mark.parametrize('url,is_match', [
        ('http://test.com', False),
        ('http://test.com/', False),
        ('http://test.com/test.foo', True),
        ('http://test.com/test.bar', False),
        ('http://test.com/test.foo?bar=baz', True),
        ('http://test.com/test.foo?bar=baz&qux', True),
    ])
    def test_match_extensions_from_config(self, monkeypatch, url, is_match):
        monkeypatch.setattr(source_managers.DirectLinkManager,
                            'accepted_extensions',
                            ['.foo'])
        assert source_managers.DirectLinkManager.match(url) == is_match
