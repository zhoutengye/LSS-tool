"""双样本T检验工具

所属层次: L2 诊断性分析
依赖: scipy
"""

from core.base import BaseTool

class TTestTool(BaseTool):
    """双样本T检验工具

    功能: 比较两组数据差异
    """

    def __init__(self):
        super().__init__()
        self.name = "t_test"
        self.description = "双样本T检验"

    def run(self, data, config):
        # TODO: 待实现
        return self.format_result({
            "success": False,
            "message": "待实现"
        })
