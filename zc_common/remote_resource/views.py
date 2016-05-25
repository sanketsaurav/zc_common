from django.db import IntegrityError
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.models.manager import Manager
from django.http import Http404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework_json_api.views import RelationshipView

from zc_common.remote_resource.models import RemoteResource
from zc_common.remote_resource.serializers import ResourceIdentifierObjectSerializer


class ModelViewSet(viewsets.ModelViewSet):
    """
    This class overwrites the ModelViewSet's list method, which handles
    requests made to the collection's base endpoint (/collection/), in
    order to fulfill requests made for multiple resources by chaning together
    query parameters in the format of /collection?ids=1,3,5.

    Inheriting from this class will, with no extra action required, properly
    handle requests made to /collection/ as well as /collection?ids=1,3. A
    request made to /collection?ids= will return an empty data object.
    """
    def has_ids_query_params(self):
        return hasattr(self.request, 'query_params') and 'ids' in self.request.query_params

    def get_ids_query_params(self):
        if hasattr(self.request, 'query_params'):
            query_param_ids = self.request.query_params.get('ids')
            return [] if not query_param_ids else query_param_ids.split(',')

    def list(self, request, *args, **kwargs):
        if self.has_ids_query_params():
            ids = self.get_ids_query_params()

            try:
                queryset = self.filter_queryset(self.get_queryset().filter(pk__in=ids))
            except (ValueError, IntegrityError):
                raise Http404

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super(ModelViewSet, self).list(request, *args, **kwargs)


class RelationshipView(RelationshipView):
    serializer_class = ResourceIdentifierObjectSerializer

    def _instantiate_serializer(self, instance):
        if isinstance(instance, RemoteResource):
            return ResourceIdentifierObjectSerializer(instance=instance)

        if isinstance(instance, Model) or instance is None:
            return self.get_serializer(instance=instance)
        else:
            if isinstance(instance, (QuerySet, Manager)):
                instance = instance.all()

            return self.get_serializer(instance=instance, many=True)
