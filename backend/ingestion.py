"""数据采集接口模块

本模块提供数据采集的"漏斗"功能，负责：
- 自动批次管理 (新建或增量更新)
- 数据清洗和验证
- 多源数据统一入库
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import models


class DataIngestor:
    """数据采集器

    处理单点数据的采集，支持自动批次创建。

    Attributes:
        db: SQLAlchemy 数据库会话

    Example:
        >>> from database import SessionLocal
        >>> db = SessionLocal()
        >>> ingestor = DataIngestor(db)
        >>>
        >>> # 首次数据会自动创建批次
        >>> ingestor.ingest_single_point(
        ...     batch_id="BATCH_001",
        ...     node_code="E04",
        ...     param_code="temp",
        ...     value=95.0,
        ...     source="SIMULATION"
        ... )
        >>>
        >>> db.close()
    """

    def __init__(self, db: Session):
        """初始化数据采集器

        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db

    def ingest_single_point(
        self,
        batch_id: str,
        node_code: str,
        param_code: str,
        value: float,
        source: str
    ) -> models.Measurement:
        """采集单点数据 (适用于传感器/模拟)

        逻辑：自动检查批次是否存在，不存在则新建 (Auto-Create Batch)

        Args:
            batch_id: 批号 (如: "BATCH_001")
            node_code: 工序节点代码 (如: "E04")
            param_code: 参数代码 (如: "temp")
            value: 测量值
            source: 数据源类型 ("HISTORY", "SIMULATION", "SENSOR")

        Returns:
            创建的 Measurement 对象

        Example:
            >>> ingestor = DataIngestor(db)
            >>> measure = ingestor.ingest_single_point(
            ...     batch_id="BATCH_001",
            ...     node_code="E04",
            ...     param_code="temp",
            ...     value=95.0,
            ...     source="SIMULATION"
            ... )
            >>> print(measure.id)
            1
        """
        # 1. 检查批次是否存在
        batch = self.db.query(models.Batch).filter(
            models.Batch.id == batch_id
        ).first()

        if not batch:
            # 新建批次
            print(f"检测到新批次 {batch_id}，正在创建...")
            new_batch = models.Batch(
                id=batch_id,
                start_time=datetime.utcnow()
            )
            self.db.add(new_batch)
            self.db.commit()
            self.db.refresh(new_batch)
            batch = new_batch

        # 2. 写入测量数据
        measure = models.Measurement(
            batch_id=batch_id,
            node_code=node_code,
            param_code=param_code,
            value=value,
            source_type=source
        )
        self.db.add(measure)
        self.db.commit()
        self.db.refresh(measure)

        return measure

    def get_batch_measurements(
        self,
        batch_id: str,
        node_code: Optional[str] = None,
        param_code: Optional[str] = None
    ) -> list[models.Measurement]:
        """查询批次的测量数据

        Args:
            batch_id: 批号
            node_code: 过滤工序代码 (可选)
            param_code: 过滤参数代码 (可选)

        Returns:
            Measurement 对象列表

        Example:
            >>> measurements = ingestor.get_batch_measurements(
            ...     batch_id="BATCH_001",
            ...     node_code="E04",
            ...     param_code="temp"
            ... )
            >>> print([m.value for m in measurements])
            [85.5, 86.0, 85.8, ...]
        """
        query = self.db.query(models.Measurement).filter(
            models.Measurement.batch_id == batch_id
        )

        if node_code:
            query = query.filter(models.Measurement.node_code == node_code)

        if param_code:
            query = query.filter(models.Measurement.param_code == param_code)

        return query.order_by(models.Measurement.timestamp).all()
