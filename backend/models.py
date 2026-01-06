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


# ==========================================
# 指挥决策系统 (Command & Action System)
# ==========================================

class ActionDef(Base):
    """对策方案定义（OCAP - Out of Control Action Plan）

    当检测到异常时，系统自动推送的标准化应对措施。
    这是连接"分析"与"行动"的桥梁。

    业务场景：
        - 操作工收到："E04温度偏高，请将蒸汽阀开度从50%调至45%"
        - QA收到："BATCH-001水分异常，请启动OOS调查流程"
        - 班长收到："党参原料波动较大，建议启用备用配方参数"

    Attributes:
        id: 主键
        code: 对策代码（唯一标识）
        name: 对策名称
        risk_code: 关联的风险节点代码
        target_role: 目标角色（"Operator"/"QA"/"TeamLeader"/"Manager"）
        instruction_template: 指令模板（支持变量替换）
        priority: 优先级（"CRITICAL"/"HIGH"/"MEDIUM"/"LOW"）
        category: 对策类别（"Equipment"/"Material"/"Method"/"Man"/"Environment"）
        estimated_impact: 预期效果描述
        active: 是否启用

    Example:
        >>> action = ActionDef(
        ...     code="ACTION_E04_TEMP_HIGH",
        ...     name="E04温度偏高对策",
        ...     risk_code="R_E04_TEMP_HIGH",
        ...     target_role="Operator",
        ...     instruction_template="检测到{node_name}温度异常（当前{current_value}℃），建议将蒸汽阀开度调至{suggested_value}%",
        ...     priority="HIGH",
        ...     category="Equipment"
        ... )
    """
    __tablename__ = "meta_actions"

    id = Column(Integer, primary_key=True, doc="主键")
    code = Column(String, unique=True, index=True, doc="对策代码")

    # 基本信息
    name = Column(String, doc="对策名称")
    risk_code = Column(String, ForeignKey("meta_risk_nodes.code"), doc="关联的风险代码")
    target_role = Column(String, doc="目标角色: Operator/QA/TeamLeader/Manager")

    # 核心字段：指令模板（支持自然语言生成）
    instruction_template = Column(String, doc="指令模板，支持 {node}, {value} 等变量")

    # 对策属性
    priority = Column(String, default="MEDIUM", doc="优先级: CRITICAL/HIGH/MEDIUM/LOW")
    category = Column(String, doc="对策类别: Equipment/Material/Method/Man/Environment")
    estimated_impact = Column(String, doc="预期效果描述")

    # 状态控制
    active = Column(Boolean, default=True, doc="是否启用")

    # 元数据
    created_at = Column(DateTime, default=datetime.datetime.utcnow, doc="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, doc="更新时间")


class DailyInstruction(Base):
    """每日指令记录表

    记录系统每日自动生成的行动指令，用于：
    1. 次日清晨推送到对应角色的终端
    2. 追踪指令的执行状态（Pending/Read/Done）
    3. 积累历史数据，优化对策效果

    业务价值：
        - 不是"生成报告"，而是"推送任务"
        - 支持事后追溯：为什么当时发了这个指令？
        - 闭环管理：指令是否被执行？效果如何？

    Attributes:
        id: 主键
        instruction_date: 指令生成日期
        target_date: 针对哪一天的生产数据
        role: 目标角色
        content: 指令内容（自然语言）
        status: 状态（Pending/Read/Done/Cancelled）
        priority: 优先级
        evidence: 证据数据（JSON，存储Cpk、风险概率等）
        action_code: 关联的对策方案代码
        batch_id: 关联的批次ID（如果针对特定批次）
        node_code: 关联的工序节点代码
        sent_at: 推送时间
        read_at: 阅读时间
        done_at: 完成时间
        feedback: 执行反馈（操作工的实际执行结果）

    Example:
        >>> instruction = DailyInstruction(
        ...     target_date="2023-10-25",
        ...     role="Operator",
        ...     content="E04温度异常，建议将蒸汽阀开度调至45%",
        ...     evidence={"cpk": 0.85, "current_temp": 85.5},
        ...     action_code="ACTION_E04_TEMP_HIGH"
        ... )
    """
    __tablename__ = "data_instructions"

    id = Column(Integer, primary_key=True, doc="主键")

    # 时间维度
    instruction_date = Column(DateTime, default=datetime.datetime.utcnow, doc="指令生成时间")
    target_date = Column(String, index=True, doc="针对的生产日期 (YYYY-MM-DD)")

    # 核心内容
    role = Column(String, index=True, doc="目标角色: Operator/QA/TeamLeader/Manager")
    content = Column(String, doc="指令内容（自然语言）")
    status = Column(String, default="Pending", doc="状态: Pending/Read/Done/Cancelled")

    priority = Column(String, doc="优先级: CRITICAL/HIGH/MEDIUM/LOW")

    # 证据链（为什么发这个指令？）
    evidence = Column(JSON, doc="证据数据: {cpk, risk_prob, current_value, ...}")
    action_code = Column(String, ForeignKey("meta_actions.code"), doc="关联的对策代码")

    # 关联维度
    batch_id = Column(String, ForeignKey("data_batches.id"), nullable=True, doc="关联批次ID")
    node_code = Column(String, nullable=True, doc="关联工序节点代码")
    param_code = Column(String, nullable=True, doc="关联参数代码")

    # 生命周期追踪
    sent_at = Column(DateTime, nullable=True, doc="实际推送时间")
    read_at = Column(DateTime, nullable=True, doc="阅读时间")
    done_at = Column(DateTime, nullable=True, doc="完成时间")
    feedback = Column(String, nullable=True, doc="执行反馈（操作工填写）")

    # 关联
    batch = relationship("Batch", doc="关联批次")
    action_def = relationship("ActionDef", doc="关联对策定义")
