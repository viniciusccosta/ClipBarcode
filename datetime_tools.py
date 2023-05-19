from datetime import datetime, timedelta

def calculate_date(data_base, fator):
    return datetime.strptime(data_base, "%d/%m/%Y") + timedelta(days=int(fator))

def timens_to_datetime(nanoseconds):
    timestamp_microseconds = nanoseconds / 1000
    timestamp_seconds = timestamp_microseconds / 1000000
    return datetime.fromtimestamp(timestamp_seconds)
