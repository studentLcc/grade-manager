from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def app_now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().app_timezone))
