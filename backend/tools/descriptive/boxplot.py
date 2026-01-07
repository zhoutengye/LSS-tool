"""箱线图工具

所属层次: L1 描述性统计
依赖: numpy
"""

from core.base import BaseTool
import numpy as np
from typing import Dict, List


class BoxplotTool(BaseTool):
    """箱线图工具

    功能:
    - 多组数据对比
    - 异常值识别
    - 四分位数分析
    - 过程稳定性对比
    """

    @property
    def name(self) -> str:
        return "箱线图分析"

    @property
    def category(self) -> str:
        return "Descriptive"

    @property
    def required_data_type(self) -> str:
        return "MultiSeries"

    @property
    def description(self) -> str:
        return "多组数据对比，识别异常值，分析过程稳定性"

    def run(self, data: Dict[str, List[float]], config: Dict) -> Dict:
        """运行箱线图分析

        Args:
            data: 多组数据 {"E01": [85, 86, ...], "E02": [84, 87, ...]}
            config: 配置参数

        Returns:
            分析结果
        """
        # 1. 验证输入
        is_valid, errors = self.validate_input(data, config)
        if not is_valid:
            return self.format_result(errors=errors)

        # 2. 提取配置
        outlier_method = config.get("outlier_method", "iqr")  # iqr或zscore

        # 3. 计算每组数据的统计量
        series_stats = {}
        all_outliers = []

        for series_name, values in data.items():
            arr = np.array(values)

            # 四分位数
            q1 = float(np.percentile(arr, 25))
            q2 = float(np.percentile(arr, 50))  # 中位数
            q3 = float(np.percentile(arr, 75))
            iqr = q3 - q1

            # 异常值检测
            outliers = []
            if outlier_method == "iqr":
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                for i, val in enumerate(arr):
                    if val < lower_bound or val > upper_bound:
                        outliers.append({
                            "index": i,
                            "value": float(val),
                            "type": "low" if val < lower_bound else "high"
                        })

            # 基本统计
            stats_data = {
                "q1": q1,
                "q2": q2,
                "q3": q3,
                "iqr": iqr,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr, ddof=1)),
                "n": len(arr),
                "outliers": outliers
            }

            series_stats[series_name] = stats_data
            all_outliers.extend([
                {**outlier, "series": series_name} for outlier in outliers
            ])

        # 4. 生成可视化数据
        plot_data = self._generate_plot_data(series_stats)

        # 5. 对比分析
        comparison = self._compare_series(series_stats)

        # 6. 洞察
        insights = self._generate_insights(series_stats, comparison)

        result = {
            "series_stats": series_stats,
            "total_outliers": len(all_outliers),
            "outlier_details": all_outliers,
            "comparison": comparison
        }

        metrics = {
            "total_series": len(data),
            "total_outliers": len(all_outliers),
            "most_variable_series": comparison.get("most_variable"),
            "most_outliers_series": comparison.get("most_outliers")
        }

        warnings = []
        if len(all_outliers) > 0:
            warnings.append(f"发现{len(all_outliers)}个异常值")

        result["insights"] = insights

        return self.format_result(
            result=result,
            plot_data=plot_data,
            metrics=metrics,
            warnings=warnings
        )

    def _generate_plot_data(self, series_stats: Dict) -> Dict:
        """生成可视化数据"""
        plot_data = {
            "type": "boxplot",
            "series": []
        }

        for series_name, stats in series_stats.items():
            plot_data["series"].append({
                "name": series_name,
                "min": stats["min"],
                "q1": stats["q1"],
                "median": stats["q2"],
                "q3": stats["q3"],
                "max": stats["max"],
                "outliers": [o["value"] for o in stats["outliers"]]
            })

        return plot_data

    def _compare_series(self, series_stats: Dict) -> Dict:
        """对比各组的波动性"""
        # 找出波动最大的（标准差最大）
        most_variable = max(
            series_stats.items(),
            key=lambda x: x[1]["std"]
        )[0]

        # 找出异常值最多的
        most_outliers = max(
            series_stats.items(),
            key=lambda x: len(x[1]["outliers"])
        )[0]

        # 对比中位数
        medians = {k: v["q2"] for k, v in series_stats.items()}
        max_median = max(medians, key=medians.get)
        min_median = min(medians, key=medians.get)

        return {
            "most_variable": most_variable,
            "most_outliers": most_outliers,
            "max_median_series": max_median,
            "min_median_series": min_median,
            "median_range": medians[max_median] - medians[min_median]
        }

    def _generate_insights(self, series_stats: Dict, comparison: Dict) -> List[str]:
        """生成洞察建议"""
        insights = []

        # 波动性洞察
        most_var = comparison["most_variable"]
        most_var_std = series_stats[most_var]["std"]
        insights.append(f"📊 {most_var}波动最大（标准差={most_var_std:.2f}）")

        # 异常值洞察
        most_out = comparison["most_outliers"]
        outlier_count = len(series_stats[most_out]["outliers"])
        if outlier_count > 0:
            insights.append(f"⚠️ {most_out}异常值最多（{outlier_count}个），需检查原因")

        # 中位数对比
        median_range = comparison["median_range"]
        if median_range > 0:
            insights.append(
                f"ℹ️ 各组中位数差异较大（范围={median_range:.2f}）"
            )

        # 稳定性建议
        stable_series = [
            k for k, v in series_stats.items()
            if len(v["outliers"]) == 0 and v["std"] < most_var_std * 0.5
        ]

        if stable_series:
            insights.append(f"✅ {', '.join(stable_series)}过程稳定，可作为标杆")

        return insights

    def validate_input(self, data: Dict, config: Dict) -> tuple:
        """验证输入数据"""
        errors = []

        if not data or len(data) == 0:
            errors.append("数据不能为空")
            return False, errors

        if not isinstance(data, dict):
            errors.append("数据必须是字典格式: {'series_name': [values]}")
            return False, errors

        # 检查每组数据
        for series_name, values in data.items():
            if not isinstance(values, list):
                errors.append(f"{series_name}的数据必须是列表")
                return False, errors

            if len(values) < 5:
                errors.append(f"{series_name}数据量至少需要5个点")
                return False, errors

        return True, errors
