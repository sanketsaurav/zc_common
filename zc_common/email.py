from datetime import date
import time
import uuid

import boto
from boto.s3.key import Key
from django.conf import settings
from raven.contrib.django.raven_compat.models import client
from zc_common.events.emit import emit_microservice_event


S3_BUCKET_NAME = 'zc-email-template-test'
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
        raise MissingCredentialsError

    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(S3_BUCKET_NAME)
    k = Key(bucket)
    return k


def generate_s3_folder_name():
    email_date = date.today().isoformat()
    email_timestamp = int(time.time())
    email_uuid = uuid.uuid4()
    return "{}/{}_{}".format(email_date, email_timestamp, email_uuid)


def send_email(from_email=None, to=None, cc=None, bcc=None, reply_to=None,
               subject=None, plaintext_body=None, html_body=None, headers=None,
               files=None, attachments=None):
    """
    files:       A list of file paths
    attachments: A list of tuples of the format (filename, content_type, content)
    """
    try:
        bucket = get_s3_email_bucket()
        s3_folder_name = generate_s3_folder_name()
    except MissingCredentialsError:
        raise
    except:
        send_error_to_sentry()
        raise

    html_body_key = None
    if html_body:
        html_body_key = "{}/html".format(s3_folder_name)
        bucket.key = html_body_key
        bucket.set_contents_from_string(html_body)

    plaintext_body_key = None
    if plaintext_body:
        plaintext_body_key = "{}/plaintext".format(s3_folder_name)
        bucket.key = plaintext_body_key
        bucket.set_contents_from_string(plaintext_body)

    attachments_keys = []
    if attachments:
        for filename, mimetype, attachment in attachments:
            attachment_key = "{}/attachment_{}".format(s3_folder_name, filename)
            bucket.key = attachment_key
            bucket.set_contents_from_filename(attachment)
            attachments_keys.append(attachment_key)
    if files:
        for filepath in files:
            filename = filepath.split('/')[-1]
            attachment_key = "{}/attachment_{}".format(s3_folder_name, filename)
            bucket.key = attachment_key
            bucket.set_contents_from_filename(filepath)
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
    }
    emit_microservice_event(EMAIL_EVENT_TYPE, **event_data)
