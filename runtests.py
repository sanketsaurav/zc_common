import pytest
import os
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

pytest.main()

# Delete test_db
os.remove(os.curdir.join([test_db]))



