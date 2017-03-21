from __future__ import unicode_literals

import re

from django.db import models
from django.core.validators import RegexValidator


US_PHONE_FORMAT = r'^(\+1\s?)?\(?(\d{3})\)?[\s-]?(\d{3})[\s-]?(\d{4})$'


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
