import os
import unittest
import django
from django.conf import settings

test_db = 'zc_common_test_db'

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'NAME': test_db,
            'ENGINE': 'django.db.backends.sqlite3'
        }
    },
    INSTALLED_APPS=[
        'zc_common',
        'tests',
    ]

)

django.setup()

suite = unittest.TestLoader().discover('tests')
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)

# Delete test_db
try:
    os.remove(os.curdir.join([test_db]))
except Exception:
    pass
