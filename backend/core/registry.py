"""LSS 工具箱注册中心

管理所有可用的分析工具，提供统一的工具查询和调用接口。
"""

from typing import Dict, Optional
from .base import BaseTool
from tools.descriptive.spc import SPCTool
from tools.descriptive.pareto import ParetoTool
from tools.descriptive.histogram import HistogramTool
from tools.descriptive.boxplot import BoxplotTool


class ToolRegistry:
    """工具注册中心

    使用单例模式管理所有工具实例。
    """

    _instance = None
    _tools: Dict[str, BaseTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool_key: str, tool: BaseTool):
        """注册工具

        Args:
            tool_key: 工具的唯一标识符 (如 "spc", "bayesian")
            tool: 工具实例
        """
        self._tools[tool_key] = tool
        print(f"✅ 已注册工具: {tool.name} ({tool_key})")

    def get_tool(self, tool_key: str) -> Optional[BaseTool]:
        """获取工具实例

        Args:
            tool_key: 工具标识符

        Returns:
            工具实例，如果不存在返回 None
        """
        return self._tools.get(tool_key)

    def list_tools(self) -> Dict[str, Dict[str, str]]:
        """列出所有已注册工具

        Returns:
            工具列表字典:
            {
                "spc": {
                    "name": "SPC Analysis",
                    "category": "Descriptive",
                    "description": "统计过程控制分析"
                },
                ...
            }
        """
        result = {}
        for key, tool in self._tools.items():
            result[key] = {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "version": tool.version,
                "required_data_type": tool.required_data_type
            }
        return result

    def get_tools_by_category(self, category: str) -> Dict[str, BaseTool]:
        """按分类获取工具

        Args:
            category: 分类名称 ("Descriptive", "Diagnostic", etc.)

        Returns:
            该分类下的所有工具字典
        """
        return {
            key: tool
            for key, tool in self._tools.items()
            if tool.category == category
        }


# 全局注册中心实例
registry = ToolRegistry()


# ==========================================
# 自动注册所有工具
# ==========================================

def register_all_tools():
    """注册所有可用工具"""

    # 第一层：描述性统计 (Descriptive)
    registry.register("spc", SPCTool())
    registry.register("pareto", ParetoTool())
    registry.register("histogram", HistogramTool())
    registry.register("boxplot", BoxplotTool())

    # TODO: 未来添加更多工具
    # registry.register("pareto", ParetoTool())
    # registry.register("histogram", HistogramTool())
    # registry.register("capability", CapabilityTool())
    # registry.register("oee", OEETool())

    # 第二层：诊断性分析 (Diagnostic)
    # registry.register("correlation", CorrelationTool())
    # registry.register("anova", ANOVATool())
    # registry.register("fmea", FMEATool())

    # 第三层：预测性分析 (Predictive)
    # registry.register("bayesian", BayesianTool())
    # registry.register("gcn", GCNTool())
    # registry.register("timeseries", TimeSeriesTool())

    # 第四层：指导性优化 (Prescriptive)
    # registry.register("nsga2", NSGA2Tool())
    # registry.register("doe", DOETool())

    print(f"📦 工具箱初始化完成，共加载 {len(registry._tools)} 个工具")


# 自动执行注册
register_all_tools()


# 便捷函数
def get_tool(tool_key: str) -> Optional[BaseTool]:
    """获取工具的便捷函数"""
    return registry.get_tool(tool_key)


def list_tools() -> Dict[str, Dict[str, str]]:
    """列出工具的便捷函数"""
    return registry.list_tools()
