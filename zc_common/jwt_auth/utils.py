import jwt
from rest_framework_jwt.settings import api_settings


def jwt_payload_handler(user):
    '''Constructs a payload for a user JWT. This is a slimmed down version of 
    https://github.com/GetBlimp/django-rest-framework-jwt/blob/master/rest_framework_jwt/utils.py#L11
    
    :param User: an object with `pk` and `get_roles()`
    :return: A dictionary that can be passed into `jwt_encode_handler`
    '''

    payload = {
        'id': user.pk,
        'roles': user.get_roles(),
    }

    return payload


def jwt_encode_handler(payload):
    '''
    Encodes a payload into a valid JWT.

    :param payload: a dictionary
    :return: an encoded JWT string
    '''

    return jwt.encode(
        payload,
        api_settings.JWT_SECRET_KEY,
        api_settings.JWT_ALGORITHM
    ).decode('utf-8')
