from datetime import date
import time
import uuid

import boto
from boto.s3.key import Key
from django.conf import settings
from zc_common.events.emit import emit_microservice_event


S3_BUCKET_NAME = 'zc-mp-email'
EMAIL_EVENT_TYPE = 'send_email'
ATTACHMENT_PREFIX = 'attachment_'


class MissingCredentialsError(Exception):
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


def generate_s3_content_key(s3_folder_name, content_type, content_name=''):
    content_key = "{}/{}".format(s3_folder_name, content_type)
    if content_name:
        content_key += '_{}'.format(content_name)
    return content_key


def upload_string_to_s3(bucket, content_key, content):
    if content:
        k = Key(bucket)
        k.key = content_key
        k.set_contents_from_string(content)


def upload_file_to_s3(bucket, content_key, filename):
    if filename:
        k = Key(bucket)
        k.key = content_key
        k.set_contents_from_filename(filename)


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
    if logger:
        msg = '''MICROSERVICE_SEND_EMAIL: Upload email with UUID {}, to {}, from {},
        with attachments {} and files {}'''
        logger.info(msg.format(email_uuid, to, from_email, attachments, files))

    html_body_key = None
    if html_body:
        html_body_key = generate_s3_content_key(s3_folder_name, 'html')
        upload_string_to_s3(bucket, html_body_key, html_body)

    plaintext_body_key = None
    if plaintext_body:
        plaintext_body_key = generate_s3_content_key(s3_folder_name, 'plaintext')
        upload_string_to_s3(bucket, plaintext_body_key, plaintext_body)

    attachments_keys = []
    if attachments:
        for filename, mimetype, attachment in attachments:
            attachment_key = generate_s3_content_key(s3_folder_name, 'attachment',
                                                     content_name=filename)
            upload_file_to_s3(bucket, attachment_key, attachment)
            attachments_keys.append(attachment_key)
    if files:
        for filepath in files:
            filename = filepath.split('/')[-1]
            attachment_key = generate_s3_content_key(s3_folder_name, 'attachment',
                                                     content_name=filename)
            upload_file_to_s3(bucket, attachment_key, filepath)
            attachments_keys.append(attachment_key)

    event_data = {
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
        'user_id': user_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
    }

    if logger:
        logger.info('MICROSERVICE_SEND_EMAIL: Sent email with UUID {} and data {}'.format(
            email_uuid, event_data
        ))

    emit_microservice_event(EMAIL_EVENT_TYPE, **event_data)
