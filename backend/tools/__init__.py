"""分析工具层

按功能分类：
- descriptive: 描述性分析 (SPC, 统计量等)
- diagnostic: 诊断性分析 (故障树, 相关性等)
- predictive: 预测性分析 (趋势预测, 异常检测等)
- prescriptive: 规范性分析 (优化建议等)
"""

from .descriptive.spc import SPCTool

__all__ = [
    "SPCTool",
]
