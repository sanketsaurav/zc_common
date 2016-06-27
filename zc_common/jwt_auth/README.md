# Service Authorization

This document serves to explain how microservices can handle authorization of
incoming requests.

## JWTs

Example:
```javascript
{
  "id": "356",
  "roles": ["staff"]
}
```

The mechanism for authorization is the JWT that will be provided with each
authenticated request. This JWT contains details about the user, which services
will need for the purposes of authorization.

## Django Rest Framework

### Authentication class

A prerequisite to any permissions is the `JWTAuthentication` class. You'll
need to include this class in your view's `authentication_classes` in order for
any of the below permissions to function properly. The `JWTAuthentication` class
assists by handling the decoding of incoming JWTs.

First, install [`zc_common`](https://github.com/ZeroCater/zc_common) if you
haven't already, along with `restframework_jwt`:
```bash
pip install djangorestframework_jwt
```

Next, you'll need to add the following lines to your `settings.py`:
```python
JWT_AUTH = {
    'JWT_SECRECT_KEY': os.environ.get('JWT_SECRET_KEY', None)
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': False
}

# Update the REST_FRAMEWORK settings with these values.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'zc_common.jwt_auth.authentication.JWTAuthentication',
    )
    'DEFAULT_PERMISSION_CLASSES': (
        'zc_common.jwt_auth.permissions.DefaultPermission',
    )
}
```

### Permissions

You'll usually need to write your own permissions, based on the needs of your
view. But here are some example permissions to show you how:

```python
from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
    
    
class IsStaff(BasePermission):
  '''
  A permission to verify the user is staff
  '''
  
  def has_permission(self, request, view):
    is_auth = request.user.is_authenticated()
    if not is_auth:
      return False
    return 'staff' in request.user.roles
    
    
class IsOrderOwner(BasePermission):
  '''
  A permission to verify the user is the author of the order.
  '''
  def has_object_permission(self, request, view, obj):
    is_auth = request.user.is_authenticated()
    if not is_auth:
      return False
    # In this case, `obj` is the Order instance
    return request.user.id == obj.owner.id
```

Here's some example views to show how the permissions could be used:

```python
from rest_framework import generics
from zc_common.jwt_auth import JWTAuthentication

class MealDetailView(generics.RetrieveAPIView):
  '''
  A simple public view for viewing the details of a meal.
  '''
  
  queryset = Meal.objects.all()


class OrderDetailView(generics.RetrieveAPIView):
  '''
  A simple detail view that requires the user to be authenticated, and the
  owner of the specific order.
  '''
 
  permission_classes = (IsOrderOwner,)
  queryset = Order.objects.all()
```

### Testing with Authentication

To test an endpoint that requires auth, you can force authentication like so:

```python
from rest_framework.test import APITestCase


class MyTestCase(ApiTestCase):
  def force_authenticate(self):
    from zc_common.jwt_auth.authentication import User
    user = User(id=1, roles=['staff'])
    self.client.force_authenticate(user=user)
    
  def test_auth_endpoint(self):
    self.force_authenticate()
    self.client.get('/my_endpoint')
    # The view's `request.user` will be the above `User` instance
```

## Authorization Explanations

For implementing authorization outside of Django Rest Framework, follow these
rules.

### Public

If a service wishes to make a route public, no work is required.

### Authentication-required

For routes which require the user to simply be logged in, services simply need
to check for the presence of the JWT. The gateway validates any provided JWTs,
and rejects those that are invalid, so if a service gets a request with a JWT,
they can trust that it is valid, and that user is authenticated.

### Staff Only

Routes that are only accessible to staff will need to check the `roles`
key of the JWT. Staff can be distinguished with the `staff` role.
