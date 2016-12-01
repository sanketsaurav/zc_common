from __future__ import division

import mock
import uuid
import math

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


class IndexRebuildTestMixin(object):
    index_rebuild_event_task = None
    resource_index_rebuild_task = None
    model = None
    attributes = []
    resource_type = None
    event_name = None
    serializer = None

    # Optional
    queryset = None
    objects_count = 10
    default_batch_size = 50
    custom_batch_size = 5

    def setUp(self):
        super(IndexRebuildTestMixin, self).setUp()
        self.create_test_data()
        self._queryset = self.queryset if self.queryset else self.model.objects.all()

    def create_test_data(self):
        with mute_signals(pre_save, post_save):
            mommy.make(self.model, _quantity=self.objects_count)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_emitting_event_with_default_batch_size__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        self.resource_index_rebuild_task()

        events_count = int(math.ceil(self.objects_count / self.default_batch_size))
        self.assertEqual(mock_save_to_s3file.call_count, events_count)
        self.assertEqual(mock_emit_microservice_event.call_count, events_count)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_emitting_event_with_custom_batch_size__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        self.resource_index_rebuild_task(batch_size=self.custom_batch_size)

        events_count = int(math.ceil(self.objects_count / self.custom_batch_size))
        self.assertEqual(mock_save_to_s3file.call_count, events_count)
        self.assertEqual(mock_emit_microservice_event.call_count, events_count)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_emitting_event_with_correct_attributes__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        total_events = int(math.ceil(self.objects_count / self.default_batch_size))
        s3_keys = [str(uuid.uuid4()) for i in xrange(total_events)]
        mock_save_to_s3file.side_effect = s3_keys

        self.resource_index_rebuild_task()

        events_count = 0
        while events_count < total_events:
            start_index = events_count * self.default_batch_size
            end_index = start_index + self.default_batch_size

            data = []

            for instance in self._queryset.order_by('id')[start_index:end_index]:
                instance_data = self.serializer.__func__(instance)

                for attr in self.attributes:
                    msg = 'Attribute {} not found in serialized model instance. data: {}'
                    self.assertTrue(attr in instance_data, msg.format(attr, instance_data))

                data.append(instance_data)

            mock_save_to_s3file.assert_any_call(data, settings.AWS_CUD_EVENTS_BUCKET_NAME)

            s3_key = s3_keys[events_count]
            payload = event_payload(self.resource_type, None, None, {'s3_key': s3_key})
            mock_emit_microservice_event.assert_any_call(self.event_name, **payload)
            events_count += 1

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_filtering_data_works__pass(self, mock_save_to_s3file, mock_emit_microservice_event):
        # If both model and queryset are defined, this test ensures filters applied on the queryset returns less
        # objects than using model.objects.all()
        if self.queryset and self.model:
            msg = 'Both queryset and model.objects.all() returns same objects count. ' \
                  'Make sure processed objects differ when using both querysets. ' \
                  'Otherwise, set queryset to None.'
            self.assertTrue(self.queryset.count() < self.model.objects.count(), msg)

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_emitted_from_received_index_rebuild_event_without_resource_type__pass(
            self, mock_save_to_s3file, mock_emit_microservice_event):
        s3_key = str(uuid.uuid4())
        mock_save_to_s3file.return_value = s3_key

        self.index_rebuild_event_task(meta={'batch_size': self.custom_batch_size})

        total_events = int(math.ceil(self.objects_count / self.custom_batch_size))
        events_count = 0

        while events_count < total_events:
            start_index = events_count * self.custom_batch_size
            end_index = start_index + self.custom_batch_size

            data = []

            for instance in self._queryset.order_by('id')[start_index:end_index]:
                instance_data = self.serializer.__func__(instance)

                for attr in self.attributes:
                    msg = 'Attribute {} not found in serialized model instance. data: {}'
                    self.assertTrue(attr in instance_data, msg.format(attr, instance_data))

                data.append(instance_data)

            mock_save_to_s3file.assert_any_call(data, settings.AWS_CUD_EVENTS_BUCKET_NAME)

            payload = event_payload(self.resource_type, None, None, {'s3_key': s3_key})
            mock_emit_microservice_event.assert_any_call(self.event_name, **payload)

            events_count += 1

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_emitted_from_received_index_rebuild_event_with_same_resource_type__pass(
            self, mock_save_to_s3file, mock_emit_microservice_event):
        s3_key = str(uuid.uuid4())
        mock_save_to_s3file.return_value = s3_key

        self.index_rebuild_event_task(resource_type=self.resource_type, meta={'batch_size': self.custom_batch_size})

        total_events = int(math.ceil(self.objects_count / self.custom_batch_size))
        events_count = 0

        while events_count < total_events:
            start_index = events_count * self.custom_batch_size
            end_index = start_index + self.custom_batch_size

            data = []

            for instance in self._queryset.order_by('id')[start_index:end_index]:
                instance_data = self.serializer.__func__(instance)

                for attr in self.attributes:
                    msg = 'Attribute {} not found in serialized model instance. data: {}'
                    self.assertTrue(attr in instance_data, msg.format(attr, instance_data))

                data.append(instance_data)

            mock_save_to_s3file.assert_any_call(data, settings.AWS_CUD_EVENTS_BUCKET_NAME)

            payload = event_payload(self.resource_type, None, None, {'s3_key': s3_key})
            mock_emit_microservice_event.assert_any_call(self.event_name, **payload)

            events_count += 1

    @mock.patch('zc_common.events.emit.emit_microservice_event')
    @mock.patch('zc_common.events.emit.save_to_s3file')
    def test_event_not_emitted_from_received_index_rebuild_event_with_different_resource_type__pass(
            self, mock_save_to_s3file, mock_emit_microservice_event):

        self.index_rebuild_event_task(resource_type='Some Other Undefined Resource Type',
                                      meta={'batch_size': self.custom_batch_size})

        mock_save_to_s3file.assert_not_called()
        mock_emit_microservice_event.assert_not_called()
