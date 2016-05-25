"""
Class Mixins.
"""
from django.db import IntegrityError
from django.http import Http404


class MultipleIDMixin(object):
    """
    Override get_queryset for multiple id support
    """
    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        if hasattr(self.request, 'query_params') and 'ids' in self.request.query_params:
            query_param_ids = self.request.query_params.get('ids')
            ids = [] if not query_param_ids else query_param_ids.split(',')

            try:
                self.queryset = self.queryset.filter(pk__in=ids)
            except (ValueError, IntegrityError):
                raise Http404
        return self.queryset
