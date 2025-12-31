"""LSS 工具箱基础架构

定义所有工具的基类和统一接口标准。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseTool(ABC):
    """LSS 工具箱基类

    所有分析工具都必须继承此类，实现统一的接口标准。

    Example:
        >>> class MyTool(BaseTool):
        ...     @property
        ...     def name(self):
        ...         return "My Analysis Tool"
        ...
        ...     @property
        ...     def required_data_type(self):
        ...         return "TimeSeries"
        ...
        ...     def run(self, data, config):
        ...         # 实现分析逻辑
        ...         return {"result": ..., "plot_data": ...}
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称

        Returns:
            工具的显示名称，如 "SPC Analysis", "Bayesian Network"
        """
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """工具分类

        Returns:
            工具所属分类:
            - "Descriptive": 描述性统计
            - "Diagnostic": 诊断性分析
            - "Predictive": 预测性分析
            - "Prescriptive": 指导性优化
        """
        pass

    @property
    @abstractmethod
    def required_data_type(self) -> str:
        """需要的数据类型

        Returns:
            数据类型:
            - "TimeSeries": 时序数据列表
            - "BatchSummary": 批次汇总数据
            - "GraphStructure": 图谱结构
            - "MultiSeries": 多组对比数据
        """
        pass

    @property
    def description(self) -> str:
        """工具描述"""
        return ""

    @property
    def version(self) -> str:
        """工具版本"""
        return "1.0.0"

    @abstractmethod
    def run(self, data: List[float], config: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析

        Args:
            data: 输入数据（格式根据 required_data_type 不同而不同）
            config: 工具配置参数，如:
                - usl: 规格上限
                - lsl: 规格下限
                - target: 目标值
                - alpha: 显著性水平
                - 等等...

        Returns:
            标准格式的结果字典:
            {
                "success": bool,           # 是否成功
                "result": dict,            # 分析结果
                "plot_data": dict,         # 可视化数据（可选）
                "metrics": dict,           # 关键指标
                "warnings": list[str],     # 警告信息
                "errors": list[str]        # 错误信息
            }

        Example:
            >>> tool.run([85, 86, 87], {"usl": 90, "lsl": 75})
            {
                "success": True,
                "result": {"cpk": 1.5, "mean": 86.0},
                "plot_data": {"type": "line", "data": [...]},
                "metrics": {"cpk": 1.5, "mean": 86.0, "std": 0.8},
                "warnings": [],
                "errors": []
            }
        """
        pass

    def validate_input(
        self,
        data: List[float],
        config: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """验证输入数据

        Args:
            data: 输入数据
            config: 配置参数

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        if not data:
            errors.append("数据不能为空")

        if len(data) < 2:
            errors.append("数据点不足，至少需要2个数据点")

        return len(errors) == 0, errors

    def format_result(
        self,
        result: Optional[Dict[str, Any]] = None,
        plot_data: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """格式化返回结果

        Args:
            result: 分析结果
            plot_data: 可视化数据
            metrics: 关键指标
            warnings: 警告信息
            errors: 错误信息

        Returns:
            标准格式的结果字典
        """
        return {
            "success": len(errors or []) == 0,
            "result": result or {},
            "plot_data": plot_data or {},
            "metrics": metrics or {},
            "warnings": warnings or [],
            "errors": errors or []
        }
