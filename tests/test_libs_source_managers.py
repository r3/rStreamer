import configparser

import pytest

from rStream.libs import source_managers


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

    def test_is_configured(self, manager):
        assert manager._config

    def test_accepted_extensions_exists(self, manager):
        assert manager.accepted_extensions

    def test_match_extensions_from_config(self, manager, config):
        extensions = config.get('directlink', 'AcceptedExtensions').split(',')
        for ext in extensions:
            test_url = 'http://test.com/file{}'.format(ext)
            assert manager.match(test_url)
