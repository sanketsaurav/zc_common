from django.db.models import DateTimeField, OneToOneField, ManyToManyField, ForeignKey


def model_to_dict(instance, follow_relations=True, excludes=[], relation_excludes=[], includes=[],
                  relation_includes=[]):
    """
    Returns a native python dict corresponding to the model's attributes. You can optionally specify fields to
    ignore by using excludes and relation_excludes. You can also specify which attributes to
    specifically return by using includes and relation_includes.

    Note: this function is written to support django v1.6 in legacy. Since most of the APIs used have been
          dropped out in v1.10, services should be careful not to upgrade without changing this function.

    Todo: handle RemoteForeignKey and GenericRemoteForeignKey.
    """
    data = {}
    attributes = []

    if includes:
        attributes = includes

    if excludes:
        attributes = [name for name in instance._meta.get_all_field_names() if name not in excludes]

    if not attributes:
        attributes = [name for name in instance._meta.get_all_field_names()]

    fields = [instance._meta.get_field_by_name(name) for name in attributes]

    for item in fields:
        is_local = item[2]
        field_obj = item[0]

        if not is_local:
            continue

        field_value = getattr(instance, field_obj.name)

        if isinstance(field_obj, OneToOneField) or isinstance(field_obj, ForeignKey):
            if field_value:
                if follow_relations:
                    field_value = model_to_dict(field_value, follow_relations=False, excludes=relation_excludes,
                                                includes=relation_includes)
                else:
                    field_value = field_value.pk

        if isinstance(field_obj, ManyToManyField):
            new_field_value = []

            for value in field_value.all():
                if follow_relations:
                    new_value = model_to_dict(value, follow_relations=False, excludes=relation_excludes,
                                              includes=relation_includes)
                else:
                    new_value = value.pk
                new_field_value.append(new_value)

            field_value = new_field_value

        # DateTimeField is not JSON serializable. Convert it to it's string version.
        if isinstance(field_obj, DateTimeField):
            field_value = unicode(field_value) if field_value else None

        data.setdefault(field_obj.name, field_value)

    return data


def event_payload(resource_type, resource_id, user_id, meta):
    return {
        'resource_type': resource_type,
        'resource_id': resource_id,
        'user_id': user_id,
        'meta': meta
    }
