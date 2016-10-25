from datetime import date
import time
import uuid

import boto
from boto.s3.key import Key
from django.conf import settings
from raven.contrib.django.raven_compat.models import client
from zc_common.events.emit import emit_microservice_event


S3_BUCKET_NAME = 'zc-mp-email'
EMAIL_EVENT_TYPE = 'send_email'
ATTACHMENT_PREFIX = 'attachment_'


class MissingCredentialsError(Exception):
    pass


def send_error_to_sentry():
    try:
        client.captureException()
    except:
        pass


def get_s3_email_bucket():
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    if not (aws_access_key_id and aws_secret_access_key):
        msg = 'You need to set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your settings file.'
        raise MissingCredentialsError(msg)

    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(S3_BUCKET_NAME)
    return bucket


def generate_s3_folder_name(email_uuid):
    email_date = date.today().isoformat()
    email_timestamp = int(time.time())
    return "{}/{}_{}".format(email_date, email_timestamp, email_uuid)


def upload_to_s3(bucket, s3_folder_name, content, content_type, content_name=''):
    if content:
        content_key = "{}/{}".format(s3_folder_name, content_type)
        if content_name:
            content_key += '_{}'.format(content_name)

        k = Key(bucket)
        k.key = content_key
        k.set_contents_from_string(content)
        return content_key
    return None


def send_email(from_email=None, to=None, cc=None, bcc=None, reply_to=None,
               subject=None, plaintext_body=None, html_body=None, headers=None,
               files=None, attachments=None, user_id=None, resource_type=None, resource_id=None,
               logger=None):
    """
    files:       A list of file paths
    attachments: A list of tuples of the format (filename, content_type, content)
    """
    email_uuid = uuid.uuid4()
    bucket = get_s3_email_bucket()
    s3_folder_name = generate_s3_folder_name(email_uuid)

    html_body_key = upload_to_s3(bucket, s3_folder_name, html_body, 'html')
    plaintext_body_key = upload_to_s3(bucket, s3_folder_name, plaintext_body, 'plaintext')

    attachments_keys = []
    if attachments:
        for filename, mimetype, attachment in attachments:
            attachment_key = upload_to_s3(bucket, s3_folder_name,
                                          attachment, 'attachment', filename)
            attachments_keys.append(attachment_key)
    if files:
        for filepath in files:
            filename = filepath.split('/')[-1]
            attachment_key = upload_to_s3(bucket, s3_folder_name,
                                          attachment, 'attachment', filename)
            attachments_keys.append(attachment_key)

    email_data = {
        'from_email': from_email,
        'to': to,
        'cc': cc,
        'bcc': bcc,
        'reply_to': reply_to,
        'subject': subject,
        'plaintext_body_key': plaintext_body_key,
        'html_body_key': html_body_key,
        'attachments_keys': attachments_keys,
        'headers': headers,
    }
    if logger:
        logger.info('SEND_EMAIL: Sent email with UUID {} and data {}'.format(
            email_uuid, email_data
        ))

    event_data = {
        'user_id': user_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
    }
    event_data.update(email_data)

    emit_microservice_event(EMAIL_EVENT_TYPE, **event_data)
