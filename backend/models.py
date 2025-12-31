"""LSS 数据库模型定义

本模块定义了药品制造工艺仿真系统的核心数据模型，包括：
- 工序节点 (ProcessNode)
- 工艺流向 (ProcessEdge)
- 参数定义 (ParameterDef)
- 风险节点 (RiskNode)
- 测量数据 (Measurement)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

# ==========================================
# 核心知识图谱 (Meta Data) - 覆盖 PDF Ch2, Ch4
# ==========================================

class ProcessNode(Base):
    """工序节点模型

    表示药品制造过程中的工序单元，支持 IDEF0 层级结构。

    层级关系:
        - Block (区块): 四大车间级别
        - Unit (单元): 具体设备级别

    Attributes:
        id: 主键
        code: 节点代码 (如: E04, P01)，唯一标识
        name: 节点名称 (如: 醇提1)
        parent_id: 父节点 ID，支持层级结构
        node_type: 节点类型 ("Block" 或 "Unit")
        params: 关联的参数列表
        children: 子节点列表

    Example:
        >>> block = ProcessNode(code="BLOCK_E", name="提取纯化车间", node_type="Block")
        >>> unit = ProcessNode(code="E04", name="醇提罐", node_type="Unit", parent_id=block.id)
    """
    __tablename__ = "meta_process_nodes"

    id = Column(Integer, primary_key=True, doc="主键")
    code = Column(String, unique=True, index=True, doc="节点代码 (如: E04)")
    name = Column(String, doc="节点名称 (如: 醇提1)")

    # 关键修正：支持父子层级 (Block -> Unit)
    parent_id = Column(Integer, ForeignKey("meta_process_nodes.id"), nullable=True, doc="父节点 ID")
    node_type = Column(String, doc="节点类型: 'Block' (区块) 或 'Unit' (单元)")

    params = relationship("ParameterDef", back_populates="node", doc="关联的参数定义")
    children = relationship("ProcessNode",
                           remote_side=[id],
                           doc="子节点列表")


class ProcessEdge(Base):
    """工艺流向连线模型

    表示工序之间的物料/产品流动关系，对应 IDEF0 中的箭头。

    Attributes:
        id: 主键
        source_code: 源节点代码 (如: E04)
        target_code: 目标节点代码 (如: E17)
        name: 流动物料名称 (如: "醇提液")
        loss_rate: 传输损耗率，用于物料衡算计算

    Example:
        >>> edge = ProcessEdge(
        ...     source_code="E04",
        ...     target_code="E17",
        ...     name="醇提液",
        ...     loss_rate=0.02
        ... )
    """
    __tablename__ = "meta_process_flows"

    id = Column(Integer, primary_key=True, doc="主键")
    source_code = Column(String, doc="源节点代码 (如: E04)")
    target_code = Column(String, doc="目标节点代码 (如: E17)")
    name = Column(String, doc="流动物料名 (如: '醇提液')")
    loss_rate = Column(Float, default=0.0, doc="传输损耗率，用于物料衡算")


class ParameterDef(Base):
    """参数定义模型

    定义工序节点的工艺参数，支持 SPC 控制和多种数据类型。

    参数角色 (role):
        - Control: 控制参数 (X)
        - Output: 输出参数 (Y)
        - Input: 输入参数

    数据类型 (data_type):
        - Scalar: 标量值 (温度、压力等)
        - Spectrum: 光谱数据
        - Image: 图像数据

    Attributes:
        id: 主键
        node_id: 关联的工序节点 ID
        code: 参数代码
        name: 参数名称
        unit: 单位
        role: 参数角色
        usl: 规格上限
        lsl: 规格下限
        target: 目标值
        is_material: 是否物料参数
        data_type: 数据类型
        node: 关联的工序节点

    Example:
        >>> param = ParameterDef(
        ...     code="temp",
        ...     name="提取温度",
        ...     unit="℃",
        ...     role="Control",
        ...     usl=90.0,
        ...     lsl=80.0,
        ...     target=85.0
        ... )
    """
    __tablename__ = "meta_parameters"

    id = Column(Integer, primary_key=True, doc="主键")
    node_id = Column(Integer, ForeignKey("meta_process_nodes.id"), doc="关联节点 ID")

    code = Column(String, doc="参数代码")
    name = Column(String, doc="参数名称")
    unit = Column(String, doc="单位")

    # 属性 A: 角色 (Ch2)
    role = Column(String, doc="参数角色: 'Control', 'Output', 'Input'")

    # 属性 B: 规格标准 (Ch6.1 SPC)
    usl = Column(Float, nullable=True, doc="规格上限")
    lsl = Column(Float, nullable=True, doc="规格下限")
    target = Column(Float, nullable=True, doc="目标值")

    # 属性 C: 物料衡算 (Ch3)
    is_material = Column(Boolean, default=False, doc="是否物料参数")

    # 属性 D: 数据类型 (Ch5)
    data_type = Column(String, default="Scalar", doc="数据类型: 'Scalar', 'Spectrum', 'Image'")

    node = relationship("ProcessNode", back_populates="params", doc="关联节点")


class RiskNode(Base):
    """风险节点模型

    表示工艺过程中的潜在风险，支持故障树分析和贝叶斯推理。

    风险分类 (category):
        - Equipment: 设备故障
        - Material: 物料异常
        - Method: 方法偏差
        - Man: 人员失误
        - Environment: 环境因素

    Attributes:
        id: 主键
        code: 风险代码
        name: 风险名称
        category: 鱼骨图分类
        base_probability: 基础发生概率
        related_param_id: 关联的参数 ID

    Example:
        >>> risk = RiskNode(
        ...     code="R001",
        ...     name="搅拌速度异常",
        ...     category="Equipment",
        ...     base_probability=0.01
        ... )
    """
    __tablename__ = "meta_risk_nodes"

    id = Column(Integer, primary_key=True, doc="主键")
    code = Column(String, unique=True, doc="风险代码")
    name = Column(String, doc="风险名称")

    # 属性 A: 鱼骨图分类 (Ch4)
    category = Column(String, doc="风险分类: Equipment, Material, Method, Man, Environment")

    # 属性 B: 贝叶斯概率 (Ch6.2)
    base_probability = Column(Float, default=0.01, doc="基础发生概率")

    # 关联：风险可能由某个参数异常触发
    related_param_id = Column(Integer, ForeignKey("meta_parameters.id"), nullable=True, doc="关联参数 ID")


class RiskEdge(Base):
    """风险关系连线模型

    表示风险节点之间的因果关系，用于构建贝叶斯网络。

    Attributes:
        id: 主键
        source_code: 源风险代码
        target_code: 目标风险代码
        weight: 因果强度 (0.0-1.0)

    Example:
        >>> edge = RiskEdge(
        ...     source_code="R001",
        ...     target_code="R002",
        ...     weight=0.8
        ... )
    """
    __tablename__ = "meta_risk_edges"

    id = Column(Integer, primary_key=True, doc="主键")
    source_code = Column(String, doc="源风险代码")
    target_code = Column(String, doc="目标风险代码")
    weight = Column(Float, default=1.0, doc="因果强度")


# ==========================================
# 动态数据存储 (Instance Data) - 覆盖三种数据源
# ==========================================

class Batch(Base):
    """批次管理模型

    管理生产任务，作为测量数据的索引表。

    Attributes:
        id: 批号，主键 (如: "WX20231001")
        product_name: 产品名称
        start_time: 批次开始时间
        status: 批次状态 ("Running", "Completed", "Archived")
        measurements: 关联的测量数据列表

    Example:
        >>> batch = Batch(
        ...     id="WX20231001",
        ...     product_name="稳心颗粒",
        ...     status="Running"
        ... )
    """
    __tablename__ = "data_batches"

    id = Column(String, primary_key=True, index=True, doc="批号")
    product_name = Column(String, default="稳心颗粒", doc="产品名称")
    start_time = Column(DateTime, default=datetime.datetime.utcnow, doc="批次开始时间")
    status = Column(String, default="Running", doc="批次状态: 'Running', 'Completed', 'Archived'")

    # 关联测量数据
    measurements = relationship("Measurement", back_populates="batch", doc="关联的测量数据")


class Measurement(Base):
    """测量数据模型

    存储工艺过程的实际测量数据，支持多种数据源。

    数据源类型 (source_type):
        - HISTORY: 历史数据
        - SIMULATION: 仿真数据
        - SENSOR: 实时传感器数据

    Attributes:
        id: 主键
        batch_id: 批号 (外键关联到 Batch 表)
        node_code: 关联工序代码
        param_code: 参数代码 (如: temp, pressure)
        timestamp: 测量时间戳
        value: 具体数值
        source_type: 数据源类型
        batch: 关联的批次对象

    Example:
        >>> measurement = Measurement(
        ...     batch_id="BATCH-2025-001",
        ...     node_code="E04",
        ...     param_code="temp",
        ...     value=85.5,
        ...     source_type="SENSOR"
        ... )
    """
    __tablename__ = "data_measurements"

    id = Column(Integer, primary_key=True, doc="主键")

    # 关联到 Batch 表
    batch_id = Column(String, ForeignKey("data_batches.id"), doc="批号")

    node_code = Column(String, doc="关联工序代码")
    param_code = Column(String, doc="参数代码 (如: temp, pressure)")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, doc="测量时间")

    value = Column(Float, doc="具体数值")

    source_type = Column(String, doc="数据源: 'HISTORY', 'SIMULATION', 'SENSOR'")

    batch = relationship("Batch", back_populates="measurements", doc="关联批次")
