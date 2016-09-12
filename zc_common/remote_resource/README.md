# zc_common/remote\_resource

This is a collection of common resources that can be used by anyone working on a Django Rest Framework/JSON API project with the need to store references to objects that exist in different projects.

This package uses Django Rest Framework and the Django REST Framework JSON API package ([Github](https://github.com/django-json-api/django-rest-framework-json-api) and [Docs](http://django-rest-framework-json-api.readthedocs.io/en/latest/)).

Specifically, this package contains helpers for extending the JSON API package's handling of relationship fields to account for our custom handling of remote resources.

**Note: There's some uncertainty about polymorphic model handling by the JSON API module that still needs to be investigated (Although there is an [open pull request](https://github.com/django-json-api/django-rest-framework-json-api/pull/211) to address this).**

## Using JSON API with Django Rest Framework

In order to use this remote_resources package, you must install the dependencies:
```bash
pip install django, djangorestframework, djangorestframework-jsonapi, django-filter
```

Follow the installation instructions for `zc_common` in the base README. You may need to add the following line to your Dockerfile:

```
RUN pip install --src=/pip-install -r requirements.txt
```

In order to get the Rest Framework and JSON API working properly, add the following to the bottom of your `settings.py` file:

```python
REST_FRAMEWORK = {
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS':
        'zc_common.remote_resource.pagination.PageNumberPagination',
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'zc_common.remote_resource.filters.JSONAPIFilterBackend',
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
}

JSON_API_FORMAT_KEYS = 'camelize'

```

You can optionally add `'rest_framework'` to your list of `INSTALLED_APPS` in your Django settings to get access to the Django Rest Framework's browsable API during development.

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

## GenericRemoteForeignKey (models)

This class provides support for generic remote relations. It is based on Django's GenericForeignKey, documented [here](https://docs.djangoproject.com/en/1.10/ref/contrib/contenttypes/#generic-relations).

Example model:
```python
class CartItem(models.Model):
  resource_type = models.CharField()
  resource_id = models.CharField()
  item = GenericRemoteForeignKey('resource_type', 'resource_id')
```

In this example, `item` is not a field, but an accessor to the remote object via the `resource_type` and `resource_id` fields. Let's look at how this might be used.

```python
ci = CartItem()

item = RemoteResource(type='CustomMenu', id='abc1234')
ci.item = item
# ci.resource_type = 'CustomMenu'
# ci.resource_id = 'abc1234'
ci.save()

ci.item
# <RemoteResource: 'CustomMenu' 'abc1234'>
```

## RelationshipView (views)

To handle the relationship view for each resource we have created a view to facilitate the extra handling needed to work properly with remote relationships. This view is a complete drop in for the JSON API package's RelationshipView, so all you need to do is import it from `zc_common.remote_resource.views` to have a relationship view that handles remote resources and there should be no extra work required aside from setting the queryset.

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
from zc_common.remote_resource.views import RelationshipView

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

## Making HTTP requests to other services

* Service-to-service communication requires a valid JWT token. You can make your requests have a proper token by using functions provided in `zc_common.remote_resource.request.py` module.
* If you want to retrieve a remote resource, you can use the shortcut method `zc_common.remote_resource.request.get_remote_resource`. Basically, it parses response content to an instance of `zc_common.remote_resource.request.RemoteResourceWrapper` or `zc_common.remote_resource.request.RemoteResourceListWrapper` based on whether the returned `data` is only one resource or a list of resources, respectively. 
* If you desire to make a request other than a `GET`, or want to manipulate the content of the response, you can use `zc_common.remote_resource.request.make_service_request` function. Currently, supported methods are restricted to `GET` and `POST`.

## TODO/Known Issues

* Following the relationship `self` link from within the service (e.g. `/companies/1/relationships/billing_addres`) does not include a top-level links object.
* Investigate how JSON API package deals with polymorphic models and whether the open PR will address the issue.
 * A GET request to a base model collection will correctly identify the `type` of each object, however only common fields covered by the default serializer will be included in the output.
 * For now, we won't support polymorphic collections, but normal actions with specific polymorphic models should not cause any problems.
* Investigate that JSON API package is handling POST and PATCH requests for related resources according to the spec (currently only tested for non-Remote related items until the relationship link issue above is resolved).
 * PATCH request updating to-many relationships will correctly replace the the entire relationship with the content of the array of resource identifier objects passed in the request (incorrectly returns a 200 response with the representation of the updated relationship).
 * PATCH requests made to the relationship link (such as `/articles/1/relationships/comments`) updating to-one and to-many relationships with an empty data object to clear the relationship (e.g. `{ data: None }` and `{ data: [] }`) are incorrectly rejected by the server with a 400 error for not passing primary data. This is correctly handled for PATCH actions made to the detail object directly (for example, `/comments/1`).
 * POST requests to to-many relationship links work correctly (add relationship items posted in addition to the items already in the relationship instead of replacing as is the case with PATCH); POST requests made to to-one relationship links correctly prohibit the action (PATCH requests are acceptable and work correctly aside from the clearing issue mentioned above).
 * DELETE requests to relationship links are handled correctly.
* A PATCH request made to a remote resource relationship will incorrectly return a 200 as well as a stale version of the relationship (it will not reflect the PATCH data).
