import mock
import uuid

from model_mommy import mommy
from factory.django import mute_signals

from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.conf import settings

from zc_common.events.utils import event_payload


class CUDEventTestMixin(object):
    """
    Base test for all CUD events. This is written to support most caveats that are found in legacy but not
    available in microservices.
    """

    event_name_prefix = None
    model = None
    resource_type = None
    serializer = None
    post_save_handler = None
    pre_delete_handler = None
    attributes = []

    def create_model_instance(self):
        return mommy.make(self.model)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_emitted_on_create__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        """
        I am using .assert_any_call(...) instead of .assert_called_with(...) because some models (i.e.
        ScheduledMeal in legacy) will have their .save() method called twice (instead of once). This behavior will
        then make it so that two CUD events are triggered (both create and update) in semi-random order. This also
        represents an edge case where listeners of CUD events could end up consuming an event whose payload
        has been already overwritten by a previously consumed event.
        """
        s3_key = str(uuid.uuid4())
        mock_save_to_s3file.return_value = s3_key

        with mute_signals(pre_save, post_save):
            post_save.connect(self.post_save_handler.__func__, self.model)
            instance = self.create_model_instance()

        instance_data = self.serializer.__func__(instance)

        for attr in self.attributes:
            msg = 'Attribute {} not found in serialized model instance. instance data: {}'.format(attr, instance_data)
            self.assertTrue(attr in instance_data, msg)

        mock_save_to_s3file.assert_any_call(instance_data, settings.AWS_CUD_EVENTS_BUCKET_NAME)

        payload = event_payload(self.resource_type, instance.pk, None, {'s3_key': s3_key})
        event_name = '{}_create'.format(self.event_name_prefix)

        mock_emit_microservice_event.assert_any_call(event_name, **payload)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_emitted_on_update__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        """See comment in self.test_event_emitted_on_create__pass."""
        s3_key = str(uuid.uuid4())
        mock_save_to_s3file.return_value = s3_key

        with mute_signals(pre_save, post_save):
            instance = self.create_model_instance()

        # Simulate update
        with mute_signals(pre_save, post_save):
            post_save.connect(self.post_save_handler.__func__, self.model)
            instance.save()

        instance_data = self.serializer.__func__(instance)

        for attr in self.attributes:
            msg = 'Attribute {} not found in serialized model instance. instance data: {}'.format(attr, instance_data)
            self.assertTrue(attr in instance_data, msg)

        mock_save_to_s3file.assert_any_call(instance_data, settings.AWS_CUD_EVENTS_BUCKET_NAME)

        payload = event_payload(self.resource_type, instance.pk, None, {'s3_key': s3_key})
        event_name = '{}_update'.format(self.event_name_prefix)

        mock_emit_microservice_event.assert_any_call(event_name, **payload)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_emitted_on_delete__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        if not self.pre_delete_handler:
            return

        s3_key = str(uuid.uuid4())
        mock_save_to_s3file.return_value = s3_key

        with mute_signals(pre_save, post_save):
            instance = self.create_model_instance()

        payload = event_payload(self.resource_type, instance.pk, None, None)
        event_name = '{}_delete'.format(self.event_name_prefix)

        # Simulate delete
        with mute_signals(pre_delete, post_delete):
            # Connecting to post_delete because unlike in prod where the task will execute asynchronously, tests
            # are running on the same thread. It would result in this test failing if connected to pre_delete.
            post_delete.connect(self.pre_delete_handler.__func__, self.model)  # I connected post_delete becaus
            instance.delete()

        mock_save_to_s3file.assert_not_called()
        mock_emit_microservice_event.assert_any_call(event_name, **payload)
