import re
from distutils.util import strtobool

from django.db.models import BooleanField, FieldDoesNotExist
from django.db.models.fields.related import ManyToManyField
from django.utils import six

# DjangoFilterBackend was moved to django-filter and deprecated/moved from DRF in version 3.6
try:
    from rest_framework.filters import DjangoFilterBackend
except ImportError:
    from django_filters.rest_framework import DjangoFilterBackend


class JSONAPIFilterBackend(DjangoFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        primary_key = queryset.model._meta.pk.name

        query_params = {}

        for param, value in six.iteritems(request.query_params):
            match = re.search(r'^filter\[(\w+)\]$', param)
            if match:
                field_name = match.group(1)
                try:
                    name, extra = field_name.split('__')
                except ValueError:
                    name = field_name
                    extra = None
                if name not in view.filter_fields.keys():
                    return queryset.none()
                if len(field_name) > 1 and field_name[:2] == 'id':
                    query_params['{0}__{1}'.format(primary_key, extra)] = value
                if hasattr(queryset.model, field_name)\
                        and isinstance(getattr(queryset.model, field_name).field, ManyToManyField):
                    value = value.split(',')

                # Allow 'true' or 'false' as values for boolean fields
                try:
                    if isinstance(queryset.model._meta.get_field(field_name), BooleanField):
                        value = bool(strtobool(value))
                except FieldDoesNotExist:
                    pass

                query_params[field_name] = value

        if filter_class:
            return filter_class(query_params, queryset=queryset).qs

        return queryset
