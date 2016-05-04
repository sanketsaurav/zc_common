from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer

from zc_common.remote_resource.models import RemoteResource


class RemoteResourceSerializer(ResourceIdentifierObjectSerializer):
    def to_representation(self, instance):
        return {'type': instance.type, 'id': instance.id}

    def to_internal_value(self, data):
        return RemoteResource(data['type'], data['id'])
