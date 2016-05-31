import jwt
from rest_framework_jwt.settings import api_settings


def jwt_payload_handler(user):
    # The handler from rest_framework_jwt removed user_id, so this is a fork
    payload = {
        'id': user.pk,
        'roles': user.get_roles(),
    }

    return payload


def jwt_encode_handler(payload):
    return jwt.encode(
        payload,
        api_settings.JWT_SECRET_KEY,
        api_settings.JWT_ALGORITHM
    ).decode('utf-8')
