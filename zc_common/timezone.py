"""
A helper to alleviate some of the weirdness with django.utils.timezone.
This file also provides other additional methods to be used when
dealing with datetime.

To use exactly as django.utils.timezone do the following:
from zc_common import timezone
timezone.now()
timezone.get_current_timezone()
"""
import datetime as python_datetime


def now(tz=None):
    """
    Just like django.utils.timezone.now(), except:
    Takes a timezone as a param and defaults to non-utc
    """
    import pytz
    from django.conf import settings

    if settings.USE_TZ:
        tz = _get_tz(tz)
        now_dt = python_datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return localtime(now_dt, tz=tz)
    else:
        return python_datetime.datetime.now()


def get_next_weekday(weekday, tz=None):
    tnow = now(tz)
    weekdays = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    weekday_num = weekdays[weekday.lower()]
    days_ahead = weekday_num - tnow.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return tnow + python_datetime.timedelta(days_ahead)


def localtime(value, tz=None):
    """
    Converts an aware datetime.datetime to a given time zone, defaults to currently activated time zone

    This method is taken almost directly from a later version of django.

    WARNING: In some cases (like with time math) normalize can cause times to shift by an hour
    when correcting the offset.
    """

    tz = _get_tz(tz)
    # If `value` is naive, astimezone() will raise a ValueError,
    # so we don't need to perform a redundant check.
    value = value.astimezone(tz)
    if hasattr(tz, 'normalize'):
        # This method is available for pytz time zones.
        value = tz.normalize(value)
    return value


def activate(value):
    """
    Override of django.utils.timezone.activate, but will first check
    if the value has a get_timezone method. If it does, the this method
    will use the value returned by get_timezone
    """
    import pytz

    if hasattr(value, 'get_timezone'):
        value = value.get_timezone()
    if isinstance(value, str):
        value = pytz.timezone(value)
    assert isinstance(value, python_datetime.tzinfo), 'Value passed was not tzinfo, it was: %s' % type(value)
    from django.utils.timezone import activate as timezone_activate
    return timezone_activate(value)


def is_daylight_savings_time(value):
    """
    Determines if the value is in daylight savings time.
    Can either take an aware datetime or a timezone object
    """
    new_datetime = _get_datetime_from_ambiguous_value(value)
    return new_datetime.dst() != python_datetime.timedelta(0)


def get_timezone_name(value):
    """
    Returns the current timezone name (PDT/PST).
    """
    return _get_datetime_from_ambiguous_value(value).strftime('%Z')


def get_timezone_offset(value):
    """
    Returns the current timezone offset (-0800).
    """
    return _get_datetime_from_ambiguous_value(value).strftime('%z')


def timezone_abbrv_mappings():
    """
    By default, dateutil doesn't parse at least `EDT` correctly.
    Pass output of this function as `tzinfos` param to parse() if it isn't pickin up timezone correctly.
    """
    from dateutil.tz import gettz
    return {'EDT': gettz('America/New_York'),
            'EST': gettz('America/New_York'),
            'CDT': gettz('America/Chicago'),
            'CST': gettz('America/Chicago'),
            'MDT': gettz('America/Denver'),
            'MST': gettz('America/Denver'),
            'PDT': gettz('America/Los_Angeles'),
            'PST': gettz('America/Los_Angeles')}


def _get_datetime_from_ambiguous_value(value):
    if type(value) is python_datetime.datetime:
        new_datetime = localtime(value, tz=value.tzinfo)
    elif type(value) is python_datetime.tzinfo:
        new_datetime = now(tz=value)
    else:
        raise Exception('value was not a timezone or a date, it was: %s' % type(value))
    return new_datetime


def combine(date, time, tz=None):
    """
    Like datetime.datetime.combine, but make it aware.
    Prefers timzeone that is passed in, followed by time.tzinfo, and then get_current_timezone
    """
    from django.utils.timezone import is_aware, make_aware

    if tz is None:
        tz = time.tzinfo
    tz = _get_tz(tz)
    combined = python_datetime.datetime.combine(date, time)
    return combined if is_aware(combined) else make_aware(combined, tz)


def parse(date_string, **kwargs):
    """ A wrapper around python-dateutil's parse function which ensures it always returns an aware datetime """
    from dateutil.parser import parse as datetime_parser
    from django.utils.timezone import is_aware, make_aware

    parsed = datetime_parser(date_string, **kwargs)
    # Make aware
    parsed = parsed if is_aware(parsed) else make_aware(parsed, _get_tz())
    # Ensure that we have the correct offset, while also keeping what was passed in.
    original = parsed
    parsed = localtime(parsed, tz=parsed.tzinfo).replace(
        year=original.year,
        month=original.month,
        day=original.day,
        hour=original.hour
    )
    return parsed


def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
    """
    A wrapper around datetime.datetime(), but ensures that the returned datetime is always
    timezone aware.
    """
    from django.utils.timezone import is_naive, make_aware

    tzinfo = _get_tz(tzinfo)
    dt = python_datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo)
    if is_naive(dt):
        dt = make_aware(dt, tzinfo)
    dt = localtime(dt, tz=tzinfo)  # Have to set the correct offset
    # Setting the offset may have changed something else, like the hour, so replace
    return dt.replace(
        year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=microsecond)


def datetime_min():
    """ Returns datetime.datetime.min, but timezone aware """
    from django.utils.timezone import get_default_timezone
    return python_datetime.datetime.min.replace(tzinfo=get_default_timezone())


def datetime_max():
    """ Returns datetime.datetime.max, but timezone aware """
    from django.utils.timezone import get_default_timezone
    return python_datetime.datetime.max.replace(tzinfo=get_default_timezone())


def math(date, op, delta, keep_hour=False):
    """
    Performs operator math on datetime and timezone objects.
    This is needed when crossing daylight savings time thresholds to maintain
    the correct offset.

    WARNING FOR NON-UTC DATETIMES:
    If the daylight savings time threshold is crossed, the hour could change from under you.
    If this is not desired behaviour, pass in keep_hour=True.

    For example, if you have 7/1/2014 at midnight and you add 180 days to it, and keep_hour=False,
    it will return 12/27/2014 at 11 p.m. -- NOT 12/28/2014 at midnight like you might would expect.

    This is caused by pytz.normalize method.
    """
    converted = op(date, delta)
    original = converted
    converted = localtime(converted, tz=converted.tzinfo)  # Need to localize to get the timezone offset correct
    if keep_hour:
        if is_daylight_savings_time(date) != is_daylight_savings_time(converted):
            # Crossed the DST threshold
            # The hour doesn't change if datetime +/- timedelta
            # But does change when crossing DST and localizing
            converted = converted.replace(
                year=original.year,
                month=original.month,
                day=original.day,
                hour=original.hour
            )
    return converted


def javascript_iso_format(date):
    import pytz
    date = localtime(date, tz=pytz.utc)
    return date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


def monthly_iter(start, end):
    """
    Iterates on a monthly basis, and wraps around dateutil.rrule

    Example:
    In [1]: from zc_common import timezone

    In [2]: for m in timezone.monthly_iter(timezone.datetime(2014, 10, 1), timezone.now()):
    ...:     print m
    ...:
    2014-10-01 00:00:00-07:00
    2014-11-01 00:00:00-07:00

    In [3]: for m in timezone.monthly_iter(timezone.datetime(2014, 10, 19), timezone.now()):
    ...:     print m
    ...:
    2014-10-19 00:00:00-07:00

    In [4]: timezone.now()
    Out[4]: datetime.datetime(
        2014, 11, 18, 16, 36, 54, 994666, tzinfo=<DstTzInfo 'America/Los_Angeles' PST-1 day, 16:00:00 STD>)
    """
    from dateutil import rrule

    for date in rrule.rrule(rrule.MONTHLY, dtstart=start, until=end):
        yield date


def weekly_iter(start, end, day=False):
    """
    Iterates weekly, wrapper around rrule.

    In [2]: for w in timezone.weekly_iter(timezone.datetime(2014, 7, 1), timezone.datetime(2014, 7, 31)):
    ...:     print w
    2014-07-01 00:00:00-07:00
    2014-07-08 00:00:00-07:00
    2014-07-15 00:00:00-07:00
    2014-07-22 00:00:00-07:00
    2014-07-29 00:00:00-07:00
    """
    from dateutil import rrule

    if day:
        while start.isoweekday() != day:
            start = start + python_datetime.timedelta(days=1)
    for date in rrule.rrule(rrule.WEEKLY, dtstart=start, until=end):
        yield date


def to_start_of_month(time):
    original_month = time.month
    original_year = time.year
    time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    time = localtime(time, time.tzinfo)
    # If the time crossed DST, the month and/or year may have changed.
    return time.replace(year=original_year, month=original_month,
                        day=1, hour=0, minute=0, second=0, microsecond=0)


def to_end_of_month(time):
    original_month = time.month
    original_year = time.year
    last_day = get_last_day_of_month(time)
    time.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    time = localtime(time, time.tzinfo)
    # If the time crossed DST, the month and/or year may have changed.
    return time.replace(year=original_year, month=original_month,
                        day=last_day, hour=23, minute=59, second=59, microsecond=999999)


def to_start_of_day(time):
    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def to_end_of_day(time):
    return time.replace(hour=23, minute=59, second=59, microsecond=999999)


def to_start_of_week(time):
    day = time.isoweekday()
    if day > 0:
        start = time - python_datetime.timedelta(days=day - 1)
    else:
        start = time
    return start


def to_end_of_week(time):
    day = time.isoweekday()
    if day > 0:
        start = time + python_datetime.timedelta(days=7 - day)
    else:
        start = time
    return start


def get_last_day_of_month(time):
    import calendar

    return calendar.monthrange(time.year, time.month)[1]


def is_business_day(time, include_weekends=True):
    """
    Determines if the current date is not a holiday.
    By default this includes weekends.
    """
    from django.conf import settings

    return not ((include_weekends and time.date().weekday() in [5, 6]) or  # saturday, sunday
                time.date() in settings.ZEROCATER_HOLIDAYS)


def _get_tz(tz=None):
    # Always get the current timezone, unless something is passed in
    from django.utils.timezone import get_current_timezone
    return tz if tz else get_current_timezone()


# http://aboutsimon.com/2013/06/05/datetime-hell-time-zone-aware-to-unix-timestamp/
def convert_to_timestamp(dt):
    import calendar
    import pytz
    from django.utils.timezone import is_aware
    if is_aware(dt):
        if dt.tzinfo != pytz.utc:
            dt = dt.astimezone(pytz.utc)
        return calendar.timegm(dt.timetuple())
    else:
        raise Exception('Can only convert aware datetimes to timestamps')


def convert_from_timestamp(timestamp):
    import pytz

    return python_datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
