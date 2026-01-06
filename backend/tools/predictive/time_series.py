"""时序预测工具 (ARIMA)

所属层次: L3 预测性分析
依赖: statsmodels
"""

from core.base import BaseTool

class TimeSeriesTool(BaseTool):
    """时序预测工具

    功能: ARIMA/Prophet 时序预测
    """

    def __init__(self):
        super().__init__()
        self.name = "time_series"
        self.description = "时序预测"

    def run(self, data, config):
        # TODO: 待实现
        return self.format_result({
            "success": False,
            "message": "待实现"
        })
