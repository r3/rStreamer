import configparser

import pytest

from rStream.libs import source_managers


@pytest.mark.parametrize('test_url,expected_extension', [
    ('http://test.com/', ''),
    ('http://test.com/foo', ''),
    ('http://test.com/foo.bar', 'bar'),
])
def test_ext_from_url(test_url, expected_extension):
    assert source_managers.ext_from_url(test_url) == expected_extension


class TestDirectLink():
    @pytest.fixture()
    def manager(self):
        return source_managers.DirectLinkManager()

    @pytest.fixture()
    def config(self):
        parser = configparser.ConfigParser()
        with open(source_managers.CONFIG_FILE) as source:
            parser.read_file(source)
        return parser

    def test_config_on_instantiation(self, mocker):
        mocker.spy(source_managers.DirectLinkManager, 'configure')
        source_managers.DirectLinkManager()
        assert source_managers.DirectLinkManager.configure.call_count == 1

    def test_is_configured(self, manager):
        assert source_managers.DirectLinkManager._config

    def test_accepted_extensions_exists(self, manager):
        assert manager.accepted_extensions

    @pytest.mark.xfail  # TODO: Remove this once you implement the match meth
    def test_match_extensions_from_config(self, manager, config):
        extensions = config.get('directlink', 'AcceptedExtensions').split(',')
        for ext in extensions:
            test_url = 'http://test.com/file{}'.format(ext)
            assert manager.match(test_url)
