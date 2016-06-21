import requests

def emit_event(event_type, event_name, resource_type, resource_id, user_id, meta_data=None):
    create_event_url = get_route_from_fk(event_type)  # TBD
    headers = get_interservice_headers()  # TBD

    event_data = generate_event_data(event_type,
                                     event_name,
                                     resource_type,
                                     resource_id,
                                     user_id,
                                     meta_data=meta_data)

    response = requests.post(create_event_url, data=event_data, headers=headers)
    return response


def generate_event_data(event_type, event_name, resource_type, resource_id, user_id, meta_data=None):
    data = {
        'data': {
            'type': event_type,
            'attributes': {
                'eventType': event_name,
                'resourceType': resource_type,
                'resourceId': resource_id,
                'userId': user_id
            }
        }
    }

    if meta_data and isinstance(meta_data, dict):
        data.update({
            'meta': meta_data
        })

    return json.dumps(data)
