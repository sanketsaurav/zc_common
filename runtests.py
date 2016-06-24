import os
import unittest
from django.conf import settings

test_db = 'zc_common_test_db'

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'NAME': test_db,
            'ENGINE': 'django.db.backends.sqlite3'
        }
    }
)

suite = unittest.TestLoader().discover('tests')
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)

# Delete test_db
try:
    os.remove(os.curdir.join([test_db]))
except Exception:
    pass
