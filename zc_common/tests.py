from django.test.runner import DiscoverRunner


class DatabaseLessRunner(DiscoverRunner):
    """A test suite runner that does not set up and tear down a database."""

    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass
