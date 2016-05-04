# zc_common/remote\_resource

This is a collection of common resources that can be used by anyone working on a Django Rest Framework/JSON API project with the need to store references to objects that exist in different projects.

This package uses Django Rest Framework and the Django REST Framework JSON API package ([Github](https://github.com/django-json-api/django-rest-framework-json-api) and [Docs](http://django-rest-framework-json-api.readthedocs.io/en/latest/)).

Specifically, this package contains helpers for extending the JSON API package's handling of relationship fields to account for our custom handling of remote resources.

**Note: There's some uncertainty about polymorphic model handling by the JSON API module that still needs to be investigated (Although there is an [open pull request](https://github.com/django-json-api/django-rest-framework-json-api/pull/211) to address this).**

## Using JSON API with Django Rest Framework

zc_common does not contain any dependencies for the related resources at the package level, so make sure that you have `django`, `djangorestframework`, `djangorestframework-jsonapi` installed.

In order to get the Rest Framework and JSON API working properly, add the following to the bottom of your `settings.py` file:

```python
REST_FRAMEWORK = {
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS':
        'zc_common.remote_resource.pagination.PageNumberPagination',
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
}

JSON_API_FORMAT_KEYS = 'camelize'

```

## RemoteForeignKey (models)

This is a model field that implements the format we have defined for how microservices will store relations to remote services. The `RemoteForeignKey` field overrides the default `CharField` and adds the additional constraints of capping the `max_length` at 50, adds a `db_index`, and uses a database column of `<resource_type>_id` by default (where resource_type is passed in the field declaration).

Example usage:

```python
class Book(models.Model):
	# ...
	author = RemoteForeignKey('Author')
```

Using it in this way will create a database field `author_id` which will store a character string of the remote foreign key.

When you have multiple remote foreign keys to the same resource (e.g. two Addresses), you'll need to be explicit by setting the `db_column` value manually so that it doesn't try to create two `address_id` fields:

```python
class ShippingCompany(models.Model):
	# ...
	billing_address = RemoteForeignKey('Address', db_column='billing_address_id')
    pickup_address = RemoteForeignKey('Address', db_column='pickup_address_id')
```

## RemoteResourceField (serializer field)

The RemoteResourceField is necessary when writing model serializers to specify that it should be treated like a relationship resource that is not local to the django project. To get everything working properly there's a bit of configuration required:

In Serializers (using the RemoteResourceField)

```python
class ShippingCompanyModelSerializer(serializers.ModelSerializer):
    billing_address = RemoteResourceRelatedField(
        self_link_view_name='company-relationships',
        related_resource_path='/addresses/{pk}'
    )
    pickup_address = RemoteResourceRelatedField(
        self_link_view_name='company-relationships',
        related_resource_path='/addresses/{pk}'
    )

    class Meta:
        model = ShippingCompany
        fields = ('name', 'billing_address', 'pickup_address', 'url')
```

In Views:

```python
from rest_framework import viewsets
from rest_framework_json_api.views import RelationshipView

from companies.models import ShippingCompany
from companies.serializers import ShippingCompanyModelSerializer


class CompanyView(viewsets.ModelViewSet):
    queryset = ShippingCompany.objects.all()
    serializer_class = ShippingCompanyModelSerializer


class ShippingCompanyRelationshipView(RelationshipView):
    queryset = ShippingCompany.objects.all()
```
In Urls:

```python
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'companies', company_views.CompanyView)

urlpatterns = [
	url(r'^', include(router.urls)),
	url(
		regex=r'^companies/(?P<pk>[^/.]+)/relationships/(?P<related_field>[^/.]+)$',
		view=company_views.ShippingCompanyRelationshipView.as_view(),
		name='company-relationships'
	),
]
```

**Note: To get the 'self' URL for objects in your JSON API response, specify the `url` field in your model serializer's `fields` on the Meta class.**

## ResponseTestCase (tests)

`ResponseTestCase` is a test case class that inherits from the Django Rest Framework's `APITestCase` class to make working with responses in the format of the JSON API more manageable by providing a few helper functions.

It also defines a `load_json(response)` method to use when converting the response back to json for further verification.

## PageNumberPagination (pagination)

We have created a custom paginator to include the `self` link to GET responses to collections. The default one included in the JSON API package does not include this link. The content of our paginator is nearly a complete copy/paste of the JSON API paginator, with the exception of creating the self_url and adding it to the response.

To use this paginator instead of the default one, modify the `DEFAULT_PAGINATION_CLASS` setting in your `settings.py` file to `'zc_common.remote_resource.pagination.PageNumberPagination',` (this is already the case if you copied the block at the top of this README into your settings file).

## ToDo/Known Issues

* Following the relationship `self` link from within the service (e.g. `/companies/1/relationships/billing_addres`) currently throws an error.
* Investigate how JSON API package deals with polymorphic models and whether the open PR will address the issue.
 * A GET request to a base model collection will correctly identify the `type` of each object, however only common fields covered by the default serializer will be included in the output.
* Investigate that JSON API package is handling POST and PATCH requests for related resources according to the spec (currently only tested for non-Remote related items until the relationship link issue above is resolved).
 * PATCH request updating to-many relationships will correctly replace the the entire relationship with the content of the array of resource identifier objects passed in the request (incorrectly returns a 200 response with the representation of the updated relationship).
 * PATCH requests made to the relationship link (such as `/articles/1/relationships/comments`) updating to-one and to-many relationships with an empty data object to clear the relationship (e.g. `{ data: None }` and `{ data: [] }`) are incorrectly rejected by the server with a 400 error for not passing primary data. This is correctly handled for PATCH actions made to the detail object directly (for example, `/comments/1`).
 * POST requests to to-many relationship links work correctly (add relationship items posted in addition to the items already in the relationship instead of replacing as is the case with PATCH); POST requests made to to-one relationship links correctly prohibit the action (PATCH requests are acceptable and work correctly aside from the clearing issue mentioned above).
 * DELETE requests to relationship links are handled correctly.