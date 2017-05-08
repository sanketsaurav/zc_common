from __future__ import absolute_import, unicode_literals

from django.conf import settings
from statsd.defaults.django import statsd as remote_statsd

from .statsd_client import LocalStatsClient


statsd = remote_statsd

STATSD_ENABLED = getattr(settings, 'STATSD_ENABLED', False)

if not STATSD_ENABLED:
    statsd = LocalStatsClient()
