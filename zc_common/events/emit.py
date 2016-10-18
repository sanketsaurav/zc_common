import pika
import ujson
import uuid

from django.conf import settings


class EmitEventException(Exception):
    pass


def emit_microservice_event(event_type, *args, **kwargs):
    url = settings.BROKER_URL

    params = pika.URLParameters(url)
    params.socket_timeout = 5

    event_queue_name = '{}-events'.format(settings.SERVICE_NAME)

    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue=event_queue_name, durable=True)

    task_id = uuid.uuid4()
    # task_name = 'ms-events.{}'.format(task_id)

    keyword_args = {'uuid': task_id}
    keyword_args.update(kwargs)

    message = {
        'task': 'ms-events.microservice_event',
        'id': task_id,
        'args': [event_type] + args,
        'kwargs': keyword_args
    }

    event_body = ujson.dumps(message)

    response = channel.basic_publish('mp-events', '', event_body, pika.BasicProperties(
        content_type='application/json', content_encoding='utf-8'))

    if not response:
        raise EmitEventException("Message may have failed to deliver")

    return response
