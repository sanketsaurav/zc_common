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
    query parameters in the format of /collection?ids[]=1&ids[]=3&ids[]=5.

    Inheriting from this class will, with no extra action required, properly
    handle requests made to /collection/ as well as /collection?ids[]=1&ids[]=3.
    """
    def list(self, request, *args, **kwargs):
        if hasattr(request, 'query_params'):
            ids = self.request.query_params.getlist('ids[]')
            if ids:
                try:
                    [int(item) for item in ids]
                except ValueError:
                    raise Http404

                queryset = self.filter_queryset(self.get_queryset().filter(id__in=ids))

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
