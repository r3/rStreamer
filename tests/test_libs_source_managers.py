from rStream.libs import source_managers


class TestDirectLink():
    def test_configured(self):
        expected_keys = ['AcceptedExtensions']

        manager = source_managers.DirectLinkManager()
        assert manager.accepted_extensions == expected_keys
