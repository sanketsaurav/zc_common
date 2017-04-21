from __future__ import unicode_literals

import re
import uuid

from django.db import models
from django.core.validators import RegexValidator


US_PHONE_FORMAT = r'^(\+1\s?)?\(?(\d{3})\)?[\s-]?(\d{3})[\s-]?(\d{4})$'


def numeric_uuid_generator():
    return str(uuid.uuid4().int)[:10]


class PhoneNumberField(models.CharField):
    description = "A field that checks the value be a valid phone number"

    phone_regex = RegexValidator(
        regex=US_PHONE_FORMAT, message="Enter a valid Phone Number.")

    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 20

        if 'validators' not in kwargs:
            kwargs['validators'] = [self.phone_regex]

        super(PhoneNumberField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value

        r = re.match(US_PHONE_FORMAT, value)
        if not r:
            return value

        return "({}) {}-{}".format(r.group(2), r.group(3), r.group(4))


class PKField(models.CharField):
    description = "A primary key field that defaults to a 10 digit random int"

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True

        if 'default' not in kwargs:
            kwargs['default'] = numeric_uuid_generator

        if 'max_length' not in kwargs:
            kwargs['max_length'] = 50

        super(PKField, self).__init__(*args, **kwargs)
