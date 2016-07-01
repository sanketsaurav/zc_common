from __future__ import unicode_literals

from django.db import models


class RemoteResource(object):
    def __init__(self, type_name, pk):
        self.type = type_name
        self.id = pk


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
