from unittest import TestCase

from zc_common.fields import PhoneNumberField
from django.db import models
from django.core.exceptions import ValidationError


class PhoneNumberModel(models.Model):
    phone = PhoneNumberField()

    class Meta:
        app_label = 'tests'


class TestPhoneNumberField(TestCase):

    valid = [
        '+1 222 222 2222',
        '+1 (223) 345-7687',
        '+1 3333333333',
        '+13333333333',
        '(234) 345-3333',
        '5676786666',
        '666 889 9990',
        '234456 9090',
    ]

    invalid = [
        '889898988',
        '+11 22 222 2222',
        '(34)5 444 4444',
        '9999-999-999',
        '999.909.444',
    ]

    def test_valid_phone_numbers(self):
        for number in self.valid:
            model = PhoneNumberModel(phone=number)
            model.full_clean()

    def test_invalid_phone_numbers(self):
        for number in self.invalid:
            model = PhoneNumberModel(phone=number)
            with self.assertRaises(ValidationError):
                model.full_clean()
