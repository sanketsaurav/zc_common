from rest_framework_json_api.views import RelationshipView

from zc_common.remote_resource.models import RemoteResource
from zc_common.remote_resource.serializers import RemoteResourceSerializer


class RelationshipView(RelationshipView):
    serializer_class = RemoteResourceSerializer

    def _instantiate_serializer(self, instance):
        if isinstance(instance, RemoteResource):
            return RemoteResourceSerializer(instance=instance)

        if isinstance(instance, Model) or instance is None:
            return self.get_serializer(instance=instance)
        else:
            if isinstance(instance, (QuerySet, Manager)):
                instance = instance.all()

            return self.get_serializer(instance=instance, many=True)
