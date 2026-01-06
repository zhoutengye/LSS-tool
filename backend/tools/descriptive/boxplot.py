"""箱线图工具

所属层次: L1 描述性统计
依赖: numpy, matplotlib
"""

from core.base import BaseTool

class BoxplotTool(BaseTool):
    """箱线图工具

    功能: 对比不同批次波动
    """

    def __init__(self):
        super().__init__()
        self.name = "boxplot"
        self.description = "箱线图"

    def run(self, data, config):
        # TODO: 待实现
        return self.format_result({
            "success": False,
            "message": "待实现"
        })
