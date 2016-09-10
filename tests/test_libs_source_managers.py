import pytest

from rStream.libs import source_managers


class TestDirectLink():
    @pytest.fixture()
    def manager(self):
        return source_managers.DirectLinkManager()

    def test_is_configured(self, manager):
        assert manager._config

    def test_accepted_extensions_exists(self, manager):
        assert manager.accepted_extensions
