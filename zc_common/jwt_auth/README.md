# Service Authorization

This document serves to explain how microservices can handle authorization of incoming requests.

## JWTs

Example:
```javascript
{
  "id": "356",
  "roles": ["user", "staff"]
}
```

The mechanism for authorization is the JWT that will be provided with each authenticated request. This JWT contains details about the user, which services will need for the purposes of authorization.

## Django Rest Framework

### Authentication class

A prerequisite to any permissions is the `JWTAuthentication` class. You'll need to include this class as a default authentication class in order for any of the below permissions to function properly. The `JWTAuthentication` class assists by handling the decoding of incoming JWTs, as well as verifying the signature.

First, install [`zc_common`](https://github.com/ZeroCater/zc_common) if you haven't already, along with `restframework_jwt`:
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

# Set a default authentication class.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'zc_common.jwt_auth.authentication.JWTAuthentication',
    )
}
```

### Permissions

You'll usually need to write your own permissions, based on the needs of your view. But here are some example permissions to show you how:

```python
from rest_framework.permissions import BasePermission
    
    
class IsStaff(BasePermission):
  '''
  A permission to verify the user is staff
  '''
  
  def has_permission(self, request, view):
    return 'staff' in request.user.roles
    
    
class IsOrderOwner(BasePermission):
  '''
  A permission to verify the user is the author of the order.
  '''
  def has_object_permission(self, request, view, obj):
    # In this case, `obj` is the Order instance
    return request.user.id == obj.owner.id
```

Here's some example views to show how the permissions could be used:

```python
from rest_framework import generics

class MealDetailView(generics.RetrieveAPIView):
  '''
  A staff-only view for viewing the details of a meal.
  '''
  permission_classes = (IsStaff,)
  queryset = Meal.objects.all()


class OrderDetailView(generics.RetrieveAPIView):
  '''
  A simple detail view that requires the user to be authenticated, and the
  owner of the specific order.
  '''
 
  permission_classes = (IsOrderOwner,)
  queryset = Order.objects.all()
```

## Testing

An `AuthenticationMixin` class has been created to make testing easier.

```python
from rest_framework.test import APITestCase
from zc_common.jwt_auth.tests import AuthenticationMixin

class UserTests(APITestCase, AuthenticationMixin):
    def setUp(self):
      self.authorize_as('anonymous')
      ...
```

There are several options for `self.authorize_as`. Each option will attach a signed JWT to outgoing test client requests:
* 'anonymous'
* 'guest'
* 'user'
* 'staff'

For 'guest', 'user', and 'staff', you may pass an additional parameter to specify the ID of the user: `self.authorize_as('staff', user_id=123)`

You may also test service requests: `self.authorize_as('service', service_name='Users')`

## Authorization Explanations

For implementing authorization outside of Django Rest Framework, follow these
rules.

At minimum, all requests must include a JWT via the `Authorization` header. The JWT's signature must be signed with the secret key. Missing JWTs or invalid signatures must be rejected.

### Public

If a service wishes to make a route public, it must only check for the presence of a JWT, with valid signature.

### Authentication-required

For routes which require the user to simply be logged in, services simply need to check that the JWT payload contains role `user`.

### Staff Only

In addition to the `user` role, staff can be distinguished with the `staff` role.
