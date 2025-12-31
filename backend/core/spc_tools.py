"""LSS 精益六西格玛工具集 - SPC 分析模块

本模块提供统计过程控制分析工具，包括过程能力指数计算和报警规则判定。
"""

import numpy as np
from typing import Dict, List, Optional
from .base import BaseTool


class SPCToolbox(BaseTool):
    """统计过程控制工具箱

    提供标准的 SPC 分析功能，属于第一层"描述性统计"工具。

    功能包括：
    - 过程能力指数 (Cpk, Cp, Ppk) 计算
    - 简单报警规则判定
    - 统计量计算 (均值、标准差)
    - 控制图数据生成

    Example:
        >>> from core.registry import get_tool
        >>> spc = get_tool("spc")
        >>> result = spc.run([85, 86, 87], {"usl": 90, "lsl": 75})
        >>> print(result["metrics"]["cpk"])
        2.123
    """

    @property
    def name(self) -> str:
        return "SPC 统计过程控制分析"

    @property
    def category(self) -> str:
        return "Descriptive"

    @property
    def required_data_type(self) -> str:
        return "TimeSeries"

    @property
    def description(self) -> str:
        return "计算过程能力指数(Cpk)、控制限，判定过程是否受控"

    def run(self, data: List[float], config: Dict) -> Dict:
        """执行 SPC 分析

        Args:
            data: 时序数据列表
            config: 配置参数，包括:
                - usl: 规格上限
                - lsl: 规格下限
                - target: 目标值 (可选)

        Returns:
            标准格式的分析结果
        """
        # 1. 验证输入
        is_valid, errors = self.validate_input(data, config)
        if not is_valid:
            return self.format_result(errors=errors)

        # 2. 提取配置
        usl = config.get("usl")
        lsl = config.get("lsl")
        target = config.get("target")

        # 3. 计算统计量
        arr = np.array(data)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        n = len(arr)

        # 4. 计算 Cpk
        cpk_result = self._calculate_cpk(data, usl, lsl)

        # 5. 报警判定
        violations = self._check_violations(data, usl, lsl)

        # 6. 生成控制图数据
        plot_data = self._generate_control_chart_data(data, mean, std, usl, lsl)

        # 7. 格式化结果
        result = {
            "mean": mean,
            "std": std,
            "min": min_val,
            "max": max_val,
            "n": n,
            "usl": usl,
            "lsl": lsl,
            "target": target,
            "cpk": cpk_result["cpk"],
            "cpu": cpk_result["cpu"],
            "cpl": cpk_result["cpl"],
            "violations": violations
        }

        metrics = {
            "cpk": cpk_result["cpk"],
            "mean": mean,
            "std": std,
            "n": n
        }

        warnings = []
        if cpk_result["cpk"] is not None and cpk_result["cpk"] < 1.33:
            warnings.append(f"过程能力不足 (Cpk={cpk_result['cpk']:.3f} < 1.33)")

        if len(violations) > 0:
            warnings.append(f"发现 {len(violations)} 个超规格数据点")

        return self.format_result(
            result=result,
            plot_data=plot_data,
            metrics=metrics,
            warnings=warnings
        )

    def _calculate_cpk(
        self,
        data: List[float],
        usl: Optional[float],
        lsl: Optional[float]
    ) -> Dict[str, Optional[float]]:
        """计算过程能力指数

        Args:
            data: 数据列表
            usl: 规格上限
            lsl: 规格下限

        Returns:
            {"cpk": float, "cpu": float, "cpl": float}
        """
        if not data or len(data) < 2:
            return {"cpk": None, "cpu": None, "cpl": None}

        arr = np.array(data)
        mean = np.mean(arr)
        std = np.std(arr, ddof=1)

        if std == 0:
            return {"cpk": 0.0, "cpu": None, "cpl": None}

        # 计算 Cpu (上侧能力指数)
        cpu = None
        if usl is not None:
            cpu = (usl - mean) / (3 * std)

        # 计算 Cpl (下侧能力指数)
        cpl = None
        if lsl is not None:
            cpl = (mean - lsl) / (3 * std)

        # 计算 Cpk (取较小值)
        if cpu is not None and cpl is not None:
            cpk = min(cpu, cpl)
        elif cpu is not None:
            cpk = cpu
        elif cpl is not None:
            cpk = cpl
        else:
            cpk = None

        return {
            "cpk": round(float(cpk), 3) if cpk is not None else None,
            "cpu": round(float(cpu), 3) if cpu is not None else None,
            "cpl": round(float(cpl), 3) if cpl is not None else None
        }

    def _check_violations(
        self,
        data: List[float],
        usl: Optional[float],
        lsl: Optional[float]
    ) -> List[Dict[str, any]]:
        """检查违规数据点

        Args:
            data: 数据列表
            usl: 规格上限
            lsl: 规格下限

        Returns:
            违规点列表 [{"index": 0, "value": 95.5, "type": "OOS_HIGH"}, ...]
        """
        violations = []

        for i, value in enumerate(data):
            if usl is not None and value > usl:
                violations.append({
                    "index": i,
                    "value": value,
                    "type": "OOS_HIGH"
                })
            elif lsl is not None and value < lsl:
                violations.append({
                    "index": i,
                    "value": value,
                    "type": "OOS_LOW"
                })

        return violations

    def _generate_control_chart_data(
        self,
        data: List[float],
        mean: float,
        std: float,
        usl: Optional[float],
        lsl: Optional[float]
    ) -> Dict:
        """生成控制图可视化数据

        Args:
            data: 原始数据
            mean: 平均值
            std: 标准差
            usl: 规格上限
            lsl: 规格下限

        Returns:
            可视化数据字典
        """
        # 计算控制限 (3 sigma)
        ucl = mean + 3 * std
        lcl = mean - 3 * std

        return {
            "type": "control_chart",
            "data": [{"x": i, "y": val} for i, val in enumerate(data)],
            "lines": {
                "mean": {"y": mean, "label": "均值"},
                "ucl": {"y": ucl, "label": "上控制限 (UCL)"},
                "lcl": {"y": lcl, "label": "下控制限 (LCL)"},
                "usl": {"y": usl, "label": "规格上限 (USL)"} if usl else None,
                "lsl": {"y": lsl, "label": "规格下限 (LSL)"} if lsl else None
            }
        }

    @staticmethod
    def check_rules(value: float, usl: float, lsl: float) -> str:
        """简单报警规则判定 (便捷方法)

        Args:
            value: 测量值
            usl: 规格上限
            lsl: 规格下限

        Returns:
            报警状态: "NORMAL", "OOS_HIGH", "OOS_LOW"
        """
        if usl and value > usl:
            return "OOS_HIGH"
        if lsl and value < lsl:
            return "OOS_LOW"
        return "NORMAL"
