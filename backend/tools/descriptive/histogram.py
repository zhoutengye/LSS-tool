"""直方图工具

所属层次: L1 描述性统计
依赖: numpy, scipy
"""

from core.base import BaseTool
import numpy as np
from scipy import stats
from typing import Dict, List


class HistogramTool(BaseTool):
    """直方图分析工具

    功能:
    - 频数分布统计
    - 正态性检验 (Shapiro-Wilk)
    - 偏度和峰度计算
    - 分布形态解释
    """

    @property
    def name(self) -> str:
        return "直方图分析"

    @property
    def category(self) -> str:
        return "Descriptive"

    @property
    def required_data_type(self) -> str:
        return "TimeSeries"

    @property
    def description(self) -> str:
        return "展示数据分布形态，检验正态性，计算偏度和峰度"

    def run(self, data: List[float], config: Dict) -> Dict:
        """运行直方图分析

        Args:
            data: 测量数据列表
            config: 配置参数 {bins, usl, lsl}

        Returns:
            分析结果
        """
        # 1. 验证输入
        is_valid, errors = self.validate_input(data, config)
        if not is_valid:
            return self.format_result(errors=errors)

        # 2. 提取配置
        bins = config.get("bins", "auto")
        usl = config.get("usl")
        lsl = config.get("lsl")

        # 3. 计算频数分布
        arr = np.array(data)
        counts, bin_edges = np.histogram(arr, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # 4. 基本统计量
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        median = float(np.median(arr))
        n = len(arr)

        # 5. 正态性检验
        is_normal = False
        p_value = None
        if n >= 3 and n <= 5000:
            statistic, p_value = stats.shapiro(arr)
            is_normal = bool(p_value > 0.05)  # 转换为Python bool类型

        # 6. 偏度和峰度
        skewness = float(stats.skew(arr))
        kurtosis = float(stats.kurtosis(arr))

        # 7. 分布解释
        distribution_interpretation = self._interpret_distribution(
            skewness, kurtosis, is_normal
        )

        # 8. 可视化数据
        plot_data = self._generate_plot_data(
            bin_edges, counts, mean, std, usl, lsl
        )

        # 9. 警告
        warnings = []
        if not is_normal and p_value is not None:
            warnings.append(f"数据不符合正态分布 (p={p_value:.4f})")

        if usl and max_val > usl:
            warnings.append(f"最大值{max_val:.2f}超过规格上限{usl}")
        if lsl and min_val < lsl:
            warnings.append(f"最小值{min_val:.2f}低于规格下限{lsl}")

        # 10. 洞察
        insights = self._generate_insights(
            mean, std, is_normal, skewness, kurtosis, usl, lsl
        )

        result = {
            "mean": mean,
            "std": std,
            "median": median,
            "min": min_val,
            "max": max_val,
            "n": n,
            "bins": int(len(counts)),
            "is_normal": is_normal,
            "p_value": p_value,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "distribution_type": distribution_interpretation["type"],
            "distribution_description": distribution_interpretation["description"]
        }

        result["insights"] = insights

        return self.format_result(
            result=result,
            plot_data=plot_data,
            metrics={"mean": mean, "std": std, "n": n, "is_normal": is_normal},
            warnings=warnings
        )

    def _interpret_distribution(
        self, skewness: float, kurtosis: float, is_normal: bool
    ) -> Dict[str, str]:
        """解释分布形态"""
        if is_normal:
            return {"type": "正态分布", "description": "数据呈正态分布，符合SPC假设"}
        elif abs(skewness) > 1:
            direction = "右偏" if skewness > 0 else "左偏"
            return {"type": f"{direction}分布", "description": f"数据{direction}，存在极端值"}
        elif kurtosis > 1:
            return {"type": "尖峰分布", "description": "数据分布陡峭，集中在均值附近"}
        elif kurtosis < -1:
            return {"type": "平峰分布", "description": "数据分布平坦，离散程度大"}
        else:
            return {"type": "近似正态", "description": "数据近似正态分布"}

    def _generate_plot_data(
        self, bin_edges, counts, mean, std, usl, lsl
    ) -> Dict:
        """生成可视化数据"""
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        plot_data = {
            "type": "histogram",
            "bins": bin_edges.tolist(),
            "counts": counts.tolist(),
            "lines": {
                "mean": {"x": mean, "label": f"均值 ({mean:.2f})"},
                "median": {"x": np.median(bin_centers), "label": "中位数"}
            }
        }

        if usl:
            plot_data["lines"]["usl"] = {"x": usl, "label": f"规格上限 ({usl})"}
        if lsl:
            plot_data["lines"]["lsl"] = {"x": lsl, "label": f"规格下限 ({lsl})"}

        return plot_data

    def _generate_insights(
        self, mean, std, is_normal, skewness, kurtosis, usl, lsl
    ) -> List[str]:
        """生成洞察建议"""
        insights = []

        insights.append(f"📊 均值={mean:.2f}, 标准差={std:.2f}")

        if is_normal:
            insights.append("✅ 数据符合正态分布，可使用SPC控制图")
        else:
            insights.append("⚠️ 数据偏离正态分布，建议先变换")

        if abs(skewness) > 0.5:
            direction = "右偏" if skewness > 0 else "左偏"
            insights.append(f"ℹ️ 数据{direction}，可能存在特殊原因")

        if usl and lsl:
            cp = (usl - lsl) / (6 * std)
            if cp >= 1.33:
                insights.append(f"✅ 过程能力充足 (Cp≈{cp:.2f})")
            elif cp >= 1.0:
                insights.append(f"⚠️ 过程能力尚可 (Cp≈{cp:.2f})")
            else:
                insights.append(f"❌ 过程能力不足 (Cp≈{cp:.2f})")

        return insights

    def validate_input(self, data: List, config: Dict) -> tuple:
        """验证输入数据"""
        errors = []

        if not data or len(data) == 0:
            errors.append("数据不能为空")
            return False, errors

        if len(data) < 3:
            errors.append("数据量至少需要3个点")
            return False, errors

        return True, errors
