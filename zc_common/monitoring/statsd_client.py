import logging
from statsd.client import Timer


logger = logging.getLogger('django')


class LocalStatsClient(object):

    def timer(self, stat, rate=1):
        return Timer(self, stat, rate)

    def timing(self, stat, delta, rate=1):
        logger.info("STATSD_STAT::TIMING {} delta={} rate={}".format(stat, delta, rate))

    def incr(self, stat, count=1, rate=1):
        logger.info("STATSD_STAT::INCR {} count={} rate={}".format(stat, count, rate))

    def decr(self, stat, count=1, rate=1):
        logger.info("STATSD_STAT::DECR {} count={} rate={}".format(stat, count, rate))

    def gauge(self, stat, value, rate=1, delta=False):
        logger.info("STATSD_STAT::GAUGE {} value={} rate={} delta={}".format(stat, value, rate, delta))

    def set(self, stat, value, rate=1):
        logger.info("STATSD_STAT::SET {} value={} rate={}".format(stat, value, rate))
