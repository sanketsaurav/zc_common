from collections import OrderedDict

import inflection

from django.conf import settings


def format_keys(obj, format_type=None):
    if format_type is None:
        format_type = getattr(settings, 'JSON_API_FORMAT_FIELD_NAMES', False)

    if format_type in ('dasherize', 'camelize', 'underscore', 'capitalize'):
        if isinstance(obj, dict):
            formatted = OrderedDict()
            for key, value in obj.items():
                if format_type == 'dasherize':
                    # inflection can't dasherize camelCase
                    key = inflection.underscore(key)
                    formatted[inflection.dasherize(key)] \
                        = format_keys(value, format_type)
                elif format_type == 'camelize':
                    formatted[inflection.camelize(key, False)] \
                        = format_keys(value, format_type)
                elif format_type == 'capitalize':
                    formatted[inflection.camelize(key)] \
                        = format_keys(value, format_type)
                elif format_type == 'underscore':
                    formatted[inflection.underscore(key)] \
                        = format_keys(value, format_type)
            return formatted
        if isinstance(obj, list):
            return [format_keys(item, format_type) for item in obj]
        else:
            return obj
    else:
        return obj
