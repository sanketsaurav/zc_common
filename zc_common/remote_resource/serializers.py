from rest_framework.serializers import Serializer


class RemoteResourceSerializer(Serializer):
    def to_representation(self, instance):
        return { 'type': instance.type, 'id': instance.id}
