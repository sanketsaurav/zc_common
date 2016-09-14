from __future__ import unicode_literals

from django.db import models
from django.db.models import signals


class RemoteResource(object):

    def __init__(self, type_name, pk):

        self.type = str(type_name) if type_name else None
        self.id = str(pk) if pk else None


class RemoteForeignKey(models.CharField):
    description = "A foreign key pointing to an external resource"

    def __init__(self, type_name, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 50

        if 'db_index' not in kwargs:
            kwargs['db_index'] = True

        if 'db_column' not in kwargs:
            kwargs['db_column'] = "%s_id" % type_name.lower()

        self.type = type_name

        super(RemoteForeignKey, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, context):
        return RemoteResource(self.type, value)

    def to_python(self, value):
        if isinstance(value, RemoteResource):
            return value.id

        if isinstance(value, basestring):
            return value

        if value is None:
            return value

        raise ValueError("Can not convert value to a RemoteResource properly")

    def deconstruct(self):
        name, path, args, kwargs = super(RemoteForeignKey, self).deconstruct()

        args = tuple([self.type] + list(args))

        del kwargs['max_length']

        return name, path, args, kwargs


class GenericRemoteForeignKey(object):
    """
    Provide a generic many-to-one relation through the ``resource_type`` and
    ``resource_id`` fields.

    This class also doubles as an accessor to the related object (similar to
    Django ForeignKeys) by adding itself as a model attribute.
    """

    # Field flags
    auto_created = False
    concrete = False
    editable = False
    hidden = False

    is_relation = True
    many_to_many = False
    many_to_one = True
    one_to_many = False
    one_to_one = False
    related_model = None
    remote_field = None

    def __init__(self, rt_field='resource_type', id_field='resource_id'):
        self.rt_field = rt_field
        self.id_field = id_field
        self.editable = False
        self.rel = None
        self.column = None

    def contribute_to_class(self, cls, name, **kwargs):
        self.name = name
        self.model = cls
        self.cache_attr = "_%s_cache" % name
        cls._meta.add_field(self, virtual=True)

        # Only run pre-initialization field assignment on non-abstract models
        if not cls._meta.abstract:
            signals.pre_init.connect(self.instance_pre_init, sender=cls)

        setattr(cls, name, self)

    def is_cached(self, instance):
        return hasattr(instance, self.cache_attr)

    def instance_pre_init(self, signal, sender, args, kwargs, **_kwargs):
        """
        Handle initializing an object with the generic FK instead of
        content_type and object_id fields.
        """
        if self.name in kwargs:
            value = kwargs.pop(self.name)
            if value is not None:
                if not isinstance(value, RemoteResource):
                    raise ValueError(
                        'GenericRemoteForeignKey only accepts RemoteResource objects as values'
                    )
                kwargs[self.rt_field] = value.type
                kwargs[self.id_field] = value.id
            else:
                kwargs[self.rt_field] = None
                kwargs[self.id_field] = None

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        try:
            return getattr(instance, self.cache_attr)
        except AttributeError:
            resource_type = getattr(instance, self.rt_field)
            resource_id = getattr(instance, self.id_field)
            rel_obj = RemoteResource(resource_type, resource_id)
            setattr(instance, self.cache_attr, rel_obj)
            return rel_obj

    def __set__(self, instance, value):
        rt = None
        pk = None
        if value is not None:
            if not isinstance(value, RemoteResource):
                raise ValueError(
                    'GenericRemoteForeignKey only accepts RemoteResource objects as values'
                )
            rt = value.type
            pk = value.id

        setattr(instance, self.rt_field, rt)
        setattr(instance, self.id_field, pk)
        setattr(instance, self.cache_attr, value)
