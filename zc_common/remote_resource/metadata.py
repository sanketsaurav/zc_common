from django.db.models.fields import related
from rest_framework.utils.field_mapping import ClassLookupDict
from rest_framework_json_api.metadata import JSONAPIMetadata
from zc_common.remote_resource.relations import RemoteResourceField
from zc_common.remote_resource.models import GenericRemoteForeignKey, RemoteForeignKey


class RelationshipMetadata(JSONAPIMetadata):
    relation_type_lookup = ClassLookupDict({
        related.ManyToManyDescriptor: 'ManyToMany',
        related.ReverseManyToOneDescriptor: 'OneToMany',
        related.ForwardManyToOneDescriptor: 'ManyToOne',
        RemoteForeignKey: 'ManyToOne',
        GenericRemoteForeignKey: 'ManyToOne'
    })

    def get_field_info(self, field):
        field_info = super(RelationshipMetadata, self).get_field_info(field)
        if isinstance(field, RemoteResourceField):
            model_class = getattr(field.parent.Meta, 'model')
            model_field = getattr(model_class, field.field_name)
            if hasattr(model_field, 'type'):
                field_info['relationship_resource'] = model_field.type
            else:
                # Generic FKs have no resource type
                field_info['relationship_resource'] = None
        return field_info
