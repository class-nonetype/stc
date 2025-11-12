from pytz import timezone
from datetime import datetime


def get_timezone(): return timezone(zone='America/Santiago')
def get_datetime() -> datetime: return datetime.now(tz=get_timezone())

