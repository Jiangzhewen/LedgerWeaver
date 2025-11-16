"""
时间处理工具
"""
from datetime import datetime, timedelta
from typing import Iterator, Tuple
import pytz


def parse_time(time_str: str) -> datetime:
    """解析时间字符串为UTC datetime对象"""
    if isinstance(time_str, datetime):
        return time_str
    
    # 支持多种时间格式
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            # 如果没有时区信息，默认为UTC
            if dt.tzinfo is None:
                dt = pytz.utc.localize(dt)
            return dt
        except ValueError:
            continue
    
    raise ValueError(f"无法解析时间字符串: {time_str}")


def to_timestamp_ms(dt: datetime) -> int:
    """将datetime转换为UTC毫秒时间戳"""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    else:
        dt = dt.astimezone(pytz.utc)
    return int(dt.timestamp() * 1000)


def from_timestamp_ms(timestamp_ms: int) -> datetime:
    """将UTC毫秒时间戳转换为datetime对象"""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.utc)


def iter_time_windows(start_time: datetime, end_time: datetime, max_window: timedelta) -> Iterator[Tuple[datetime, datetime]]:
    """按max_window切片，返回[start, end)半开区间序列"""
    current_start = start_time
    while current_start < end_time:
        current_end = min(current_start + max_window, end_time)
        yield (current_start, current_end)
        current_start = current_end


def format_iso8601(dt: datetime) -> str:
    """格式化为ISO8601字符串"""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    else:
        dt = dt.astimezone(pytz.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"