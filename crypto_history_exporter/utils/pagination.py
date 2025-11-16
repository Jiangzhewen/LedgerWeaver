"""
通用分页工具
"""
from typing import Iterator, List, Callable, Optional, Generic, TypeVar
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PaginationResult(Generic[T]):
    """分页结果"""
    items: List[T]
    has_more: bool
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None


class PaginationHelper(Generic[T]):
    """分页助手"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def paginate_with_cursor(
        self,
        fetch_func: Callable[[Optional[str]], PaginationResult[T]],
        initial_cursor: Optional[str] = None
    ) -> Iterator[T]:
        """使用游标进行分页"""
        cursor = initial_cursor
        page = 0
        
        while True:
            if self.debug_mode:
                logger.info(f"获取第 {page + 1} 页数据，游标: {cursor}")
            
            result: PaginationResult[T] = fetch_func(cursor)
            
            if self.debug_mode:
                logger.info(f"第 {page + 1} 页返回 {len(result.items)} 条记录")
            
            # 返回当前页的所有项目
            for item in result.items:
                yield item
            
            # 如果没有更多数据或没有下一个游标，则停止
            if not result.has_more or not result.next_cursor:
                break
            
            cursor = result.next_cursor
            page += 1
    
    def paginate_with_id(
        self,
        fetch_func: Callable[[Optional[str]], PaginationResult[T]],
        initial_id: Optional[str] = None
    ) -> Iterator[T]:
        """使用ID进行分页"""
        last_id = initial_id
        page = 0
        
        while True:
            if self.debug_mode:
                logger.info(f"获取第 {page + 1} 页数据，起始ID: {last_id}")
            
            result: PaginationResult[T] = fetch_func(last_id)
            
            if self.debug_mode:
                logger.info(f"第 {page + 1} 页返回 {len(result.items)} 条记录")
            
            # 返回当前页的所有项目
            for item in result.items:
                yield item
            
            # 如果返回的记录数小于限制，说明已经是最后一页
            if not result.has_more:
                break
            
            # 更新last_id为当前页的最大ID
            if result.items:
                last_id = getattr(result.items[-1], 'id', None)
                if last_id is None:
                    # 如果项目没有id属性，尝试获取trade_id、order_id等
                    for id_attr in ['trade_id', 'order_id', 'funding_id']:
                        last_id = getattr(result.items[-1], id_attr, None)
                        if last_id is not None:
                            break
            
            # 如果无法获取last_id，则停止分页
            if last_id is None:
                break
            
            page += 1
    
    def paginate_with_time_window(
        self,
        fetch_func: Callable[[int, int], List[T]],
        start_time: int,
        end_time: int,
        window_size: int,  # 毫秒
        overlap: int = 0  # 重叠毫秒数，避免遗漏
    ) -> Iterator[T]:
        """使用时间窗口进行分页"""
        current_start = start_time
        processed_ids = set()
        
        while current_start < end_time:
            current_end = min(current_start + window_size, end_time)
            
            if self.debug_mode:
                logger.info(f"获取时间窗口数据: {current_start} - {current_end}")
            
            items = fetch_func(current_start, current_end)
            
            if self.debug_mode:
                logger.info(f"时间窗口返回 {len(items)} 条记录")
            
            # 去重并返回项目
            for item in items:
                # 尝试获取项目的唯一标识
                item_id = getattr(item, 'id', None)
                if item_id is None:
                    # 如果没有id属性，尝试其他唯一标识
                    for id_attr in ['trade_id', 'order_id', 'funding_id', 'tx_hash']:
                        item_id = getattr(item, id_attr, None)
                        if item_id is not None:
                            break
                
                # 如果仍无法获取唯一标识，直接返回
                if item_id is None:
                    yield item
                    continue
                
                # 如果是新记录，返回并记录
                if item_id not in processed_ids:
                    processed_ids.add(item_id)
                    yield item
            
            current_start = current_end - overlap  # 重叠处理