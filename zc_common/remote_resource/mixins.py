"""
Class Mixins.
"""
from django.http import Http404


class MultipleIDMixin(object):
    """
    Override get_queryset for multiple id support
    """
    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        if hasattr(self.request, 'query_params'):
            ids = dict(self.request.query_params).getlist('ids[]')
            if ids:
                try:
                    [int(item) for item in ids]
                except ValueError:
                    raise Http404

                self.queryset = self.queryset.filter(id__in=ids)
        return self.queryset
