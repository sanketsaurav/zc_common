# zc_common/remote\_resource

This is a collection of common resources that can be used by anyone working on a Django Rest Framework/JSON API project with the need to store references to objects that exist in different projects.

This package uses Django Rest Framework and the Django REST Framework JSON API package ([Github](https://github.com/django-json-api/django-rest-framework-json-api) and [Docs](http://django-rest-framework-json-api.readthedocs.io/en/latest/)).

Specifically, this package contains helpers for extending the JSON API package's handling of relationship fields to account for our custom handling of remote resources.

**Note: There's some uncertainty about polymorphic model handling by the JSON API module that still needs to be investigated (Although there is an [open pull request](https://github.com/django-json-api/django-rest-framework-json-api/pull/211) to address this).**

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
        related_link_view_name='address-detail',
        related_link_url_kwarg='pk',
        self_link_view_name='company-relationships',
    )
    pickup_address = RemoteResourceRelatedField(
        related_link_view_name='address-detail',
        related_link_url_kwarg='pk',
        self_link_view_name='company-relationships',
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


def remote_resource(request):
	"""
	Dummy route that will never be hit.
	"""
    pass
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
	url(  # This is a dummy route to the remote resource
		regex=r'^addresses/(?P<pk>[^/.]+)/$',
		view=company_views.remote_resource,
		name='address-detail'
	),
]
```

**Note: To get the 'self' URL for objects in your JSON API response, specify the `url` field in your model serializer's `fields` on the Meta class.**

## ResponseTestCase (tests)

`ResponseTestCase` is a test case class that inherits from the Django Rest Framework's `APITestCase` class to make working with responses in the format of the JSON API more manageable by providing a few helper functions.

It also defines a `load_json(response)` method to use when converting the response back to json for further verification.

## ToDo/Known Issues

* Following the relationship `self` link from within the service (e.g. `/companies/1/relationships/billing_addres`) currently throws an error.
* GET requests to collections do not currently provide a `self` link of where the collection resource can be fetched from. (e.g. a GET request to `/companies` needs to return a top level 'links' object that contains a self link to `/companies`.
* Investigate how JSON API package deals with polymorphic models and whether the open PR will address the issue.