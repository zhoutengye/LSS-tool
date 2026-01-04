"""黑带指挥官 - 智能编排层核心

模仿 Lean Six Sigma 黑带专家的决策流程，自动化生成生产诊断报告。
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session

from data import DataProviderFactory, DataContext, query_data_by_dimension
from .decision_engine import DecisionEngineFactory, AnalysisMode, DecisionEngine
from .workflows import WorkflowRegistry, WorkflowResult


@dataclass
class DiagnosisReport:
    """诊断报告数据结构

    统一的报告格式，适用于所有维度的分析。
    """
    # 基本信息
    dimension: str  # person/batch/process/workshop/time
    analysis_id: str  # 唯一标识
    analysis_date: str  # 分析日期
    overall_status: str  # "NORMAL", "WARNING", "CRITICAL"

    # 核心发现
    critical_issues: List[Dict[str, Any]]  # 紧急问题
    warnings: List[Dict[str, Any]]         # 警告
    opportunities: List[Dict[str, Any]]    # 改进机会

    # 详细分析
    parameter_analyses: Dict[str, Any]     # 每个参数的详细分析
    risk_assessments: List[Dict[str, Any]] # 风险评估

    # 行动建议
    priority_actions: List[Dict[str, Any]] # 优先级行动
    recommendations: List[str]             # 建议

    # 元数据
    analysis_metadata: Dict[str, Any]      # 分析时间、工具版本等


class BlackBeltCommander:
    """黑带指挥官 - 智能编排器

    核心职责:
    1. 协调多个分析工具 (SPC、风险分析、相关性等)
    2. 执行分析工作流 (批次诊断、多参数分析、趋势分析)
    3. 决策逻辑 (规则引擎 → LLM 推理)
    4. 生成可执行的生产诊断报告

    设计模式:
    - Strategy Pattern: 可插拔的决策引擎 (rules vs LLM)
    - Builder Pattern: 报告生成流程
    - Chain of Responsibility: 分析工作流链条
    """

    def __init__(
        self,
        db: Session,
        mode: AnalysisMode = AnalysisMode.RULE_BASED,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化黑带指挥官

        Args:
            db: 数据库会话
            mode: 分析模式 (规则/LLM/混合)
            config: 配置参数 (如 Cpk 阈值、风险概率阈值等)
        """
        self.db = db
        self.mode = mode
        self.config = config or self._default_config()

        # 初始化组件
        self.data_providers = DataProviderFactory.create(db)
        self.decision_engine = DecisionEngineFactory.create(mode, config)
        self.workflows = WorkflowRegistry(
            self.data_providers,
            self.decision_engine,
            db
        )

    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # SPC 阈值
            "cpk_critical": 0.8,      # Cpk < 0.8 为紧急
            "cpk_warning": 1.33,       # Cpk < 1.33 为警告

            # 风险概率阈值
            "risk_critical": 0.3,      # 概率 > 30% 为紧急
            "risk_warning": 0.1,       # 概率 > 10% 为警告

            # 数据质量要求
            "min_data_points": 5,      # 最少数据点数

            # 分析优先级权重
            "priority_weights": {
                "cpk": 0.4,           # 过程能力权重
                "risk": 0.3,          # 风险概率权重
                "trend": 0.2,         # 趋势异常权重
                "violations": 0.1     # 违规点数量权重
            }
        }

    # ========================================
    # 多维度分析入口（统一接口）
    # ========================================

    def analyze_by_person(
        self,
        operator_id: str,
        date_range: Optional[tuple] = None
    ) -> DiagnosisReport:
        """
        按人员分析

        分析特定操作工/班组的绩效。

        Args:
            operator_id: 操作工ID
            date_range: (start_date, end_date) 可选

        Returns:
            DiagnosisReport: 人员绩效诊断报告
        """
        context = query_data_by_dimension(
            self.db,
            "person",
            operator_id=operator_id,
            date_range=date_range
        )

        return self._analyze_context(context)

    def analyze_by_batch(self, batch_id: str) -> DiagnosisReport:
        """
        按批次分析

        分析单个批次的完整生命周期。

        Args:
            batch_id: 批次号

        Returns:
            DiagnosisReport: 批次诊断报告
        """
        context = query_data_by_dimension(
            self.db,
            "batch",
            batch_id=batch_id
        )

        return self._analyze_context(context)

    def analyze_by_process(
        self,
        node_code: str,
        time_window: int = 7
    ) -> DiagnosisReport:
        """
        按工序分析

        分析特定工序的稳定性。

        Args:
            node_code: 工序代码 (如 E04)
            time_window: 时间窗口（天数），默认7天

        Returns:
            DiagnosisReport: 工序诊断报告
        """
        context = query_data_by_dimension(
            self.db,
            "process",
            node_code=node_code,
            time_window=time_window
        )

        return self._analyze_context(context)

    def analyze_by_workshop(
        self,
        block_id: str,
        date: Optional[str] = None
    ) -> DiagnosisReport:
        """
        按车间分析

        分析整个车间的整体表现。

        Args:
            block_id: 车间ID (如 BLOCK_E - 提取车间)
            date: 日期 (YYYY-MM-DD)，默认为今天

        Returns:
            DiagnosisReport: 车间诊断报告
        """
        context = query_data_by_dimension(
            self.db,
            "workshop",
            block_id=block_id,
            date=date
        )

        return self._analyze_context(context)

    def analyze_by_time(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "day"
    ) -> DiagnosisReport:
        """
        按时间分析

        分析时间维度的趋势。

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            granularity: 粒度 (day/week/month)，默认 day

        Returns:
            DiagnosisReport: 时间趋势报告
        """
        context = query_data_by_dimension(
            self.db,
            "time",
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )

        return self._analyze_context(context)

    # ========================================
    # 通用分析流程
    # ========================================

    def _analyze_context(self, context: DataContext) -> DiagnosisReport:
        """
        对任意维度的DataContext执行标准化分析流程

        这是核心的通用分析方法，所有维度都走这个流程。

        Args:
            context: 数据上下文

        Returns:
            DiagnosisReport: 诊断报告
        """
        # 执行工作流
        workflow = self.workflows.get("comprehensive_diagnosis")
        if not workflow:
            raise RuntimeError("工作流 'comprehensive_diagnosis' 未注册")

        result = workflow.execute(context)

        # 生成报告
        from .report_formatter import ReportFormatter
        formatter = ReportFormatter()

        return formatter.build_report(result, context)

    # ========================================
    # 快速API（便捷方法）
    # ========================================

    def get_recommended_actions(
        self,
        batch_id: str,
        max_actions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取优先级行动建议（快速API）

        只返回最关键的行动建议，用于前端快速显示。

        Args:
            batch_id: 批次号
            max_actions: 最多返回几条建议

        Returns:
            按优先级排序的行动建议列表
        """
        report = self.analyze_by_batch(batch_id)
        return report.priority_actions[:max_actions]

    def set_analysis_mode(self, mode: AnalysisMode):
        """
        切换分析模式（运行时）

        支持从规则引擎无缝切换到 LLM 模式。

        Args:
            mode: 新的分析模式
        """
        self.mode = mode
        self.decision_engine = DecisionEngineFactory.create(mode, self.config)

        # 更新所有工作流的决策引擎
        self.workflows.decision_engine = self.decision_engine
