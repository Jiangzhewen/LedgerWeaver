"""
分页工具测试
"""
from typing import List, Optional
from dataclasses import dataclass
from crypto_history_exporter.utils.pagination import PaginationHelper, PaginationResult


@dataclass
class MockItem:
    """模拟数据项"""
    id: str
    value: str


def test_paginate_with_cursor():
    """测试使用游标分页"""
    # 模拟分页函数
    def mock_fetch_func(cursor: Optional[str]) -> PaginationResult[MockItem]:
        if cursor is None:
            # 第一页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(3)]
            return PaginationResult(items=items, has_more=True, next_cursor="cursor_1")
        elif cursor == "cursor_1":
            # 第二页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(3, 6)]
            return PaginationResult(items=items, has_more=True, next_cursor="cursor_2")
        elif cursor == "cursor_2":
            # 最后一页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(6, 8)]
            return PaginationResult(items=items, has_more=False, next_cursor=None)
        else:
            # 不应该到达这里
            return PaginationResult(items=[], has_more=False, next_cursor=None)
    
    # 测试分页助手
    helper = PaginationHelper[MockItem](debug_mode=False)
    items = list(helper.paginate_with_cursor(mock_fetch_func))
    
    # 验证结果
    assert len(items) == 8
    assert items[0].id == "0"
    assert items[0].value == "value_0"
    assert items[7].id == "7"
    assert items[7].value == "value_7"


def test_paginate_with_id():
    """测试使用ID分页"""
    # 模拟分页函数
    def mock_fetch_func(last_id: Optional[str]) -> PaginationResult[MockItem]:
        if last_id is None:
            # 第一页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(3)]
            return PaginationResult(items=items, has_more=True)
        elif last_id == "2":
            # 第二页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(3, 6)]
            return PaginationResult(items=items, has_more=True)
        elif last_id == "5":
            # 最后一页
            items = [MockItem(id=str(i), value=f"value_{i}") for i in range(6, 8)]
            return PaginationResult(items=items, has_more=False)
        else:
            # 不应该到达这里
            return PaginationResult(items=[], has_more=False)
    
    # 测试分页助手
    helper = PaginationHelper[MockItem](debug_mode=False)
    items = list(helper.paginate_with_id(mock_fetch_func))
    
    # 验证结果
    assert len(items) == 8
    assert items[0].id == "0"
    assert items[0].value == "value_0"
    assert items[7].id == "7"
    assert items[7].value == "value_7"


def test_paginate_with_time_window():
    """测试使用时间窗口分页"""
    # 模拟分页函数
    def mock_fetch_func(start_time: int, end_time: int) -> List[MockItem]:
        # 根据时间窗口返回不同的数据
        if start_time == 0 and end_time == 1000:
            return [MockItem(id="1", value="item_1"), MockItem(id="2", value="item_2")]
        elif start_time == 1000 and end_time == 2000:
            return [MockItem(id="3", value="item_3"), MockItem(id="4", value="item_4")]
        elif start_time == 2000 and end_time == 3000:
            return [MockItem(id="5", value="item_5")]
        else:
            return []
    
    # 测试分页助手
    helper = PaginationHelper[MockItem](debug_mode=False)
    items = list(helper.paginate_with_time_window(mock_fetch_func, 0, 3000, 1000))
    
    # 验证结果
    assert len(items) == 5
    assert items[0].id == "1"
    assert items[0].value == "item_1"
    assert items[4].id == "5"
    assert items[4].value == "item_5"


def test_paginate_with_time_window_overlap():
    """测试使用时间窗口分页（带重叠）"""
    # 模拟分页函数，会返回重复数据
    def mock_fetch_func(start_time: int, end_time: int) -> List[MockItem]:
        # 根据时间窗口返回不同的数据
        if start_time == 0 and end_time == 1000:
            return [MockItem(id="1", value="item_1"), MockItem(id="2", value="item_2")]
        elif start_time == 900 and end_time == 1900:  # 重叠100ms
            # 包含重复数据
            return [MockItem(id="2", value="item_2"), MockItem(id="3", value="item_3")]
        elif start_time == 1800 and end_time == 2800:  # 重叠100ms
            # 包含重复数据
            return [MockItem(id="3", value="item_3"), MockItem(id="4", value="item_4")]
        else:
            return []
    
    # 测试分页助手
    helper = PaginationHelper[MockItem](debug_mode=False)
    items = list(helper.paginate_with_time_window(mock_fetch_func, 0, 2800, 1000, overlap=100))
    
    # 验证结果，应该去重
    assert len(items) == 4
    assert items[0].id == "1"
    assert items[0].value == "item_1"
    assert items[3].id == "4"
    assert items[3].value == "item_4"