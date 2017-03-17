from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator


class PhoneNumberField(models.CharField):
    description = "A field that checks the value be a valid phone number"

    def __init__(self, *args, **kwargs):
        phone_regex = RegexValidator(
            regex=r'^(\+\d{1}\s?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}$', message="Enter a valid Phone Number.")

        if 'max_length' not in kwargs:
            kwargs['max_length'] = 20

        if 'validators' not in kwargs:
            kwargs['validators'] = [phone_regex]

        super(PhoneNumberField, self).__init__(*args, **kwargs)
