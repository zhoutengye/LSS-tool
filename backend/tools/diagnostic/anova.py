"""方差分析工具 (ANOVA)

所属层次: L2 诊断性分析
依赖: scipy
"""

from core.base import BaseTool

class ANOVATool(BaseTool):
    """方差分析工具

    功能: 判断显著性差异
    """

    def __init__(self):
        super().__init__()
        self.name = "anova"
        self.description = "方差分析"

    def run(self, data, config):
        # TODO: 待实现
        return self.format_result({
            "success": False,
            "message": "待实现"
        })
