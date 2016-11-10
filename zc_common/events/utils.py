from django.db.models import DateTimeField


def model_to_dict(instance, follow_relations=True, excludes=[], relation_excludes=[]):
    """
    This function returns a native python dict corresponding to the model's attributes. I included
    attributes that are only defined on the model to avoid infinite recursion and redundant
    data. It will also follow relations up to only one level by default.

    Todo: handle RemoteForeignKey and GenericRemoteForeignKey.
    """
    data = {}

    for field in instance._meta.get_fields():
        if not field.concrete or field.name in excludes:
            continue

        field_value = field.value_from_object(instance)

        if field.one_to_one or field.many_to_one:
            if follow_relations:
                field_value = model_to_dict(field_value, follow_relations=False, excludes=relation_excludes)
            else:
                field_value = field_value.pk

        if field.many_to_many:
            new_field_value = []

            for value in field_value:
                if follow_relations:
                    new_value = model_to_dict(value, follow_relations=False, excludes=relation_excludes)
                else:
                    new_value = value.pk
                new_field_value.append(new_value)

            field_value = new_field_value

        # DateTimeField is not JSON serializable. Convert it to it's string version.
        if isinstance(field, DateTimeField):
            field_value = unicode(field_value)

        data.setdefault(field.name, field_value)

    return data
