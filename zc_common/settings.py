from django.conf import settings
from rest_framework.settings import APISettings
import os

DEFAULTS = {
    'GATEWAY_ROOT_PATH': getattr(
        settings, 'GATEWAY_ROOT_PATH', os.environ.get('GATEWAY_ROOT_PATH', 'https://mp-gateway.herokuapp.com/'))
}

api_settings = APISettings(None, DEFAULTS, None)