import re

from django.db.models.fields.related import ManyToManyField
from rest_framework import filters


class JSONAPIFilterBackend(filters.DjangoFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        primary_key = queryset.model._meta.pk.name

        query_params = {}

        for param, value in request.query_params.iteritems():
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
                if 'id' in field_name:
                    query_params['{0}__{1}'.format(primary_key, extra)] = value
                if isinstance(getattr(queryset.model, field_name).field, ManyToManyField):
                    value = value.split(',')
                query_params[field_name] = value

        if filter_class:
            return filter_class(query_params, queryset=queryset).qs

        return queryset
