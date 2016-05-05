"""
Pagination fields

hamedahmadi 05/02/2016:
Had to create this custom pagination to include self link

see:
https://github.com/django-json-api/django-rest-framework-json-api/blob/develop/rest_framework_json_api/pagination.py
"""
from collections import OrderedDict
from rest_framework import serializers
from rest_framework.views import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.utils.urls import remove_query_param, replace_query_param


class PageNumberPagination(PageNumberPagination):
    """
    A json-api compatible pagination format
    """

    page_size_query_param = 'page_size'
    max_page_size = 100

    def build_link(self, index):
        if not index:
            return None
        url = self.request and self.request.build_absolute_uri() or ''
        return replace_query_param(url, 'page', index)

    def get_paginated_response(self, data):
        next = None
        previous = None

        if self.page.has_next():
            next = self.page.next_page_number()
        if self.page.has_previous():
            previous = self.page.previous_page_number()

        # hamedahmadi 05/02/2016 -- Adding this to include self link
        self_url = remove_query_param(self.request.build_absolute_uri(), self.page_query_param)
        return Response({
            'results': data,
            'meta': {
                'pagination': OrderedDict([
                    ('page', self.page.number),
                    ('pages', self.page.paginator.num_pages),
                    ('count', self.page.paginator.count),
                ])
            },
            'links': OrderedDict([
                ('self', self_url),
                ('first', self.build_link(1)),
                ('last', self.build_link(self.page.paginator.num_pages)),
                ('next', self.build_link(next)),
                ('prev', self.build_link(previous))
            ])
        })
