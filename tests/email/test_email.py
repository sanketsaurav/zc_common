import mock
from unittest import TestCase

from zc_common import email


class EmailTests(TestCase):
    def setUp(self):
        pass

    @mock.patch('boto.connect_s3', side_effect=Exception)
    def test_send_email__connection_fail(self, mock_connect_s3):
        with self.assertRaises(Exception):
            email.send_email()

    @mock.patch('boto.connect_s3')
    @mock.patch('zc_common.email.emit_microservice_event')
    def test_send_email(self, mock_emit_event, mock_connect_s3):
        send_email_kwargs = {
            'from_address': 'from@test.com',
            'to_list': ['to@test.com'],
            'cc_list': ['cc_1@test.com', 'cc_2@test.com'],
            'bcc_list': ['bcc_1@test.com', 'bcc_2@test.com'],
            'reply_to_list': ['reply_to@test.com'],
            'subject': 'email subject',
        }

        email.send_email(**send_email_kwargs)

        mock_emit_event.assert_called_once()
        event_args = mock_emit_event.call_args_list[0][1]

        expected_event_args = ['from_address', 'to', 'cc', 'bcc', 'reply_to',
                               'subject', 'html_body_key', 'plaintext_body_key',
                               'headers', 'attachments_keys']

        for expected_arg in expected_event_args:
            self.assertTrue(expected_arg in event_args)
            self.assertEqual(emit_event_args[arg])

    @mock.patch('zc_common.email.get_s3_email_bucket')
    @mock.patch('zc_common.email.emit_microservice_event')
    def test_send_email_multiple_attachments(self, mock_emit_event, mock_get_bucket):
        attachments = [
            ('file1.pdf', 'application/pdf', None),
            ('file2.pdf', 'application/pdf', None),
            ('file3.pdf', 'application/pdf', None),
        ]

        email.send_email(attachments=attachments)
        mock_emit_event.assert_called_once()
        attachments_keys = mock_emit_event.call_args_list[0][1]['attachments_keys']
        self.assertEqual(len(attachments_keys), len(attachments))

    @mock.patch('zc_common.email.get_s3_email_bucket')
    @mock.patch('zc_common.email.emit_microservice_event')
    def test_send_email_headers(self, mock_emit_event, mock_get_bucket):
        email_headers = {'send_email_header': True}

        email.send_email(headers=email_headers)
        mock_emit_event.assert_called_once()
        headers = mock_emit_event.call_args_list[0][1]['headers']
        self.assertEqual(len(headers), len(email_headers))
