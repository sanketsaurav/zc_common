import os
import unittest
import django
import datetime
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
    ZEROCATER_HOLIDAYS = {
        datetime.date(2014, 7, 4),  # USA Independence Day
    },
    USE_TZ=True,
    TIME_ZONE = "America/Los_Angeles",
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
