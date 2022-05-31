import datetime


def timens_to_datetime(nanoseconds):
    timestamp_microseconds = nanoseconds / 1000
    timestamp_seconds = timestamp_microseconds / 1000000
    return datetime.datetime.fromtimestamp(timestamp_seconds)