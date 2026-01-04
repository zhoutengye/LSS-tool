"""数据提供者 - 多维度查询接口

统一的数据访问层，支持5种核心分析维度：
- Person: 按人员查询
- Batch: 按批次查询
- Process: 按工序查询
- Workshop: 按车间查询
- Time: 按时间查询
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import models


@dataclass
class DataContext:
    """统一的查询结果上下文

    任何维度的查询结果都封装为这个结构，便于后续流程统一处理。
    """
    dimension: str  # person/batch/process/workshop/time
    filters: Dict[str, Any]  # 查询条件

    # 原始数据
    batches: List[str]  # 相关批次ID列表
    measurements: List[Any]  # 测量数据 (models.Measurement)

    # 元数据
    metadata: Dict[str, Any]  # 维度特定的元数据
    query_time: datetime  # 查询时间戳


class DataProvider(ABC):
    """数据提供者基类

    定义统一的数据查询接口，所有维度的Provider都继承此类。
    """

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def query(self, dimension: str, **filters) -> DataContext:
        """
        按维度查询数据

        Args:
            dimension: 维度类型 (person/batch/process/workshop/time)
            **filters: 过滤条件

        Returns:
            DataContext: 包含该维度下的所有相关数据
        """
        pass


class PersonDataProvider(DataProvider):
    """按人员维度查询

    查询特定操作工/班组负责的所有批次和相关数据。
    """

    def query(self, dimension: str, **filters) -> DataContext:
        """
        查询指定操作工的所有批次数据

        Args:
            dimension: 固定为 "person"
            **filters:
                - operator_id: 操作工ID
                - date_range: (start_date, end_date) 可选

        Returns:
            DataContext
        """
        operator_id = filters.get("operator_id")
        date_range = filters.get("date_range")

        if not operator_id:
            raise ValueError("operator_id is required for person dimension")

        # 查询该操作工的所有批次
        query = self.db.query(models.Batch).filter(
            models.Batch.operator_id == operator_id
        )

        # 时间范围过滤
        if date_range:
            start_date, end_date = date_range
            query = query.filter(
                models.Batch.start_time >= start_date,
                models.Batch.start_time < end_date
            )

        batches = query.all()
        batch_ids = [b.id for b in batches]

        # 查询这些批次的所有测量数据
        measurements = self.db.query(models.Measurement).filter(
            models.Measurement.batch_id.in_(batch_ids)
        ).all() if batch_ids else []

        return DataContext(
            dimension="person",
            filters=filters,
            batches=batch_ids,
            measurements=measurements,
            metadata={
                "operator_id": operator_id,
                "total_batches": len(batch_ids),
                "date_range": date_range
            },
            query_time=datetime.now()
        )


class BatchDataProvider(DataProvider):
    """按批次维度查询

    查询单个批次的完整数据。
    """

    def query(self, dimension: str, **filters) -> DataContext:
        """
        查询指定批次的完整数据

        Args:
            dimension: 固定为 "batch"
            **filters:
                - batch_id: 批次号

        Returns:
            DataContext
        """
        batch_id = filters.get("batch_id")

        if not batch_id:
            raise ValueError("batch_id is required for batch dimension")

        # 查询批次信息
        batch = self.db.query(models.Batch).filter(
            models.Batch.id == batch_id
        ).first()

        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        # 查询该批次的所有测量数据
        measurements = self.db.query(models.Measurement).filter(
            models.Measurement.batch_id == batch_id
        ).all()

        return DataContext(
            dimension="batch",
            filters=filters,
            batches=[batch_id],
            measurements=measurements,
            metadata={
                "batch_id": batch_id,
                "product_name": batch.product_name,
                "start_time": batch.start_time.isoformat() if batch.start_time else None,
                "status": batch.status,
                "operator_id": getattr(batch, 'operator_id', None)
            },
            query_time=datetime.now()
        )


class ProcessDataProvider(DataProvider):
    """按工序维度查询

    查询特定工序的历史数据。
    """

    def query(self, dimension: str, **filters) -> DataContext:
        """
        查询指定工序的历史数据

        Args:
            dimension: 固定为 "process"
            **filters:
                - node_code: 工序代码 (如 E04)
                - time_window: 时间窗口（天数），默认7天
                - date_from: 开始日期（可选，优先于time_window）

        Returns:
            DataContext
        """
        node_code = filters.get("node_code")
        time_window = filters.get("time_window", 7)
        date_from = filters.get("date_from")

        if not node_code:
            raise ValueError("node_code is required for process dimension")

        # 计算时间范围
        if date_from:
            cutoff_date = date_from
        else:
            cutoff_date = datetime.now() - timedelta(days=time_window)

        # 查询时间窗口内该工序的所有批次
        # 通过 Measurement 表反向查找 Batch
        batch_ids = self.db.query(models.Measurement.batch_id).filter(
            models.Measurement.node_code == node_code,
            models.Measurement.timestamp >= cutoff_date
        ).distinct().all()

        batch_ids = [b[0] for b in batch_ids]

        # 查询这些批次的测量数据（仅该工序的）
        measurements = self.db.query(models.Measurement).filter(
            models.Measurement.batch_id.in_(batch_ids),
            models.Measurement.node_code == node_code
        ).all() if batch_ids else []

        return DataContext(
            dimension="process",
            filters=filters,
            batches=batch_ids,
            measurements=measurements,
            metadata={
                "node_code": node_code,
                "time_window": time_window,
                "cutoff_date": cutoff_date.isoformat(),
                "total_batches": len(batch_ids)
            },
            query_time=datetime.now()
        )


class WorkshopDataProvider(DataProvider):
    """按车间维度查询

    查询指定车间的整体数据。
    """

    def query(self, dimension: str, **filters) -> DataContext:
        """
        查询指定车间的整体数据

        Args:
            dimension: 固定为 "workshop"
            **filters:
                - block_id: 车间ID (如 BLOCK_E - 提取车间)
                - date: 日期 (YYYY-MM-DD)，默认为今天

        Returns:
            DataContext
        """
        block_id = filters.get("block_id")
        date = filters.get("date")

        if not block_id:
            raise ValueError("block_id is required for workshop dimension")

        # 解析日期
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()

        # 查询该车间下的所有工序节点
        nodes = self.db.query(models.ProcessNode).filter(
            models.ProcessNode.parent_id == block_id
        ).all()

        node_codes = [n.code for n in nodes]

        # 查询该日期所有相关批次的测量数据
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)

        measurements = self.db.query(models.Measurement).filter(
            models.Measurement.node_code.in_(node_codes),
            models.Measurement.timestamp >= start_time,
            models.Measurement.timestamp < end_time
        ).all()

        # 获取涉及的批次
        batch_ids = list(set([m.batch_id for m in measurements]))

        return DataContext(
            dimension="workshop",
            filters=filters,
            batches=batch_ids,
            measurements=measurements,
            metadata={
                "block_id": block_id,
                "date": date,
                "node_codes": node_codes,
                "total_nodes": len(node_codes)
            },
            query_time=datetime.now()
        )


class TimeDataProvider(DataProvider):
    """按时间维度查询

    查询时间窗口内的聚合数据。
    """

    def query(self, dimension: str, **filters) -> DataContext:
        """
        查询时间窗口内的聚合数据

        Args:
            dimension: 固定为 "time"
            **filters:
                - start_date: 开始日期 (YYYY-MM-DD)
                - end_date: 结束日期 (YYYY-MM-DD)
                - granularity: 粒度 (day/week/month)，默认 day

        Returns:
            DataContext
        """
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        granularity = filters.get("granularity", "day")

        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required for time dimension")

        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含结束日期当天

        # 查询时间窗口内的所有测量数据
        measurements = self.db.query(models.Measurement).filter(
            models.Measurement.timestamp >= start_dt,
            models.Measurement.timestamp < end_dt
        ).all()

        # 获取涉及的批次
        batch_ids = list(set([m.batch_id for m in measurements]))

        return DataContext(
            dimension="time",
            filters=filters,
            batches=batch_ids,
            measurements=measurements,
            metadata={
                "start_date": start_date,
                "end_date": end_date,
                "granularity": granularity,
                "total_days": (end_dt - start_dt).days
            },
            query_time=datetime.now()
        )


class DataProviderFactory:
    """数据提供者工厂

    根据维度类型创建对应的 Provider 实例。
    """

    _providers = {
        "person": PersonDataProvider,
        "batch": BatchDataProvider,
        "process": ProcessDataProvider,
        "workshop": WorkshopDataProvider,
        "time": TimeDataProvider
    }

    @classmethod
    def create(cls, db: Session) -> Dict[str, DataProvider]:
        """
        创建所有 Provider 实例

        Args:
            db: 数据库会话

        Returns:
            Dict[str, DataProvider]: 维度名 -> Provider 实例的映射
        """
        return {
            dimension: provider_class(db)
            for dimension, provider_class in cls._providers.items()
        }

    @classmethod
    def get_provider(cls, db: Session, dimension: str) -> DataProvider:
        """
        获取指定维度的 Provider

        Args:
            db: 数据库会话
            dimension: 维度类型

        Returns:
            DataProvider: 对应的 Provider 实例
        """
        provider_class = cls._providers.get(dimension)
        if not provider_class:
            raise ValueError(f"Unknown dimension: {dimension}")

        return provider_class(db)


# 便捷函数
def query_data_by_dimension(
    db: Session,
    dimension: str,
    **filters
) -> DataContext:
    """
    按维度查询数据的便捷函数

    Args:
        db: 数据库会话
        dimension: 维度类型 (person/batch/process/workshop/time)
        **filters: 过滤条件

    Returns:
        DataContext
    """
    provider = DataProviderFactory.get_provider(db, dimension)
    return provider.query(dimension, **filters)
