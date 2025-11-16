"""
时间工具测试
"""
from datetime import datetime, timedelta, timezone
import pytz
from crypto_history_exporter.utils.time import parse_time, to_timestamp_ms, from_timestamp_ms, iter_time_windows, format_iso8601


def test_parse_time():
    """测试时间解析"""
    # 测试日期格式
    dt1 = parse_time("2022-01-01")
    assert dt1.year == 2022
    assert dt1.month == 1
    assert dt1.day == 1
    assert dt1.hour == 0
    assert dt1.minute == 0
    assert dt1.second == 0
    assert dt1.tzinfo == pytz.utc
    
    # 测试日期时间格式
    dt2 = parse_time("2022-01-01 12:30:45")
    assert dt2.year == 2022
    assert dt2.month == 1
    assert dt2.day == 1
    assert dt2.hour == 12
    assert dt2.minute == 30
    assert dt2.second == 45
    assert dt2.tzinfo == pytz.utc
    
    # 测试ISO8601格式
    dt3 = parse_time("2022-01-01T12:30:45Z")
    assert dt3.year == 2022
    assert dt3.month == 1
    assert dt3.day == 1
    assert dt3.hour == 12
    assert dt3.minute == 30
    assert dt3.second == 45
    assert dt3.tzinfo == pytz.utc


def test_to_timestamp_ms():
    """测试转换为毫秒时间戳"""
    dt = datetime(2022, 1, 1, 12, 30, 45, tzinfo=pytz.utc)
    timestamp = to_timestamp_ms(dt)
    assert timestamp == 1641040245000


def test_from_timestamp_ms():
    """测试从毫秒时间戳转换"""
    timestamp = 1641040245000
    dt = from_timestamp_ms(timestamp)
    assert dt.year == 2022
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12
    assert dt.minute == 30
    assert dt.second == 45
    assert dt.tzinfo == pytz.utc


def test_iter_time_windows():
    """测试时间窗口迭代"""
    start_time = datetime(2022, 1, 1, tzinfo=pytz.utc)
    end_time = datetime(2022, 1, 3, tzinfo=pytz.utc)
    max_window = timedelta(days=1)
    
    windows = list(iter_time_windows(start_time, end_time, max_window))
    assert len(windows) == 2
    
    # 检查第一个窗口
    assert windows[0][0] == start_time
    assert windows[0][1] == datetime(2022, 1, 2, tzinfo=pytz.utc)
    
    # 检查第二个窗口
    assert windows[1][0] == datetime(2022, 1, 2, tzinfo=pytz.utc)
    assert windows[1][1] == end_time


def test_format_iso8601():
    """测试ISO8601格式化"""
    dt = datetime(2022, 1, 1, 12, 30, 45, 123456, tzinfo=pytz.utc)
    iso_string = format_iso8601(dt)
    assert iso_string == "2022-01-01T12:30:45.123Z"