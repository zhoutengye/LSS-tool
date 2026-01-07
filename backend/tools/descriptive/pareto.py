"""LSS 精益六西格玛工具集 - 帕累托图分析模块

本模块提供帕累托图分析工具，用于识别"关键少数"问题。
"""

import numpy as np
from typing import Dict, List, Optional
from core.base import BaseTool


class ParetoTool(BaseTool):
    """帕累托图分析工具

    提供80/20法则分析，属于第一层"描述性统计"工具。

    功能包括：
    - 问题类别排序
    - 累计贡献率计算
    - 关键少数识别
    - ABC分类

    Example:
        >>> from core.registry import get_tool
        >>> pareto = get_tool("pareto")
        >>> data = [
        ...     {"category": "温度异常", "count": 15},
        ...     {"category": "压力异常", "count": 8},
        ...     {"category": "液位异常", "count": 5}
        ... ]
        >>> result = pareto.run(data, {})
        >>> print(result["key_few"])
        ['温度异常']
    """

    @property
    def name(self) -> str:
        return "帕累托图分析"

    @property
    def category(self) -> str:
        return "Descriptive"

    @property
    def required_data_type(self) -> str:
        return "CategoricalData"

    @property
    def description(self) -> str:
        return "识别'关键少数'问题，应用80/20法则进行根因分析"

    def run(self, data: List[Dict], config: Dict) -> Dict:
        """执行帕累托分析

        Args:
            data: 类别数据列表，格式:
                [{"category": "问题类型", "count": 15}, ...]
                或者
                [{"category": "温度异常", "value": 85.5}, ...]
            config: 配置参数，包括:
                - threshold: 累计占比阈值 (默认0.8，即80%)
                - category_field: 类别字段名 (默认"category")
                - value_field: 数值字段名 (默认"count"，如果不存在则用"value")

        Returns:
            标准格式的分析结果
        """
        # 1. 验证输入
        is_valid, errors = self.validate_input(data, config)
        if not is_valid:
            return self.format_result(errors=errors)

        # 2. 提取配置
        threshold = config.get("threshold", 0.8)
        category_field = config.get("category_field", "category")
        value_field = config.get("value_field", "count")

        # 3. 聚合数据（如果有重复类别）
        aggregated = self._aggregate_data(data, category_field, value_field)

        # 4. 排序（降序）
        sorted_data = sorted(aggregated, key=lambda x: x["count"], reverse=True)

        # 5. 计算累计贡献率
        total = sum(item["count"] for item in sorted_data)
        cumulative = 0
        for item in sorted_data:
            cumulative += item["count"]
            item["cumulative_count"] = cumulative
            item["cumulative_pct"] = cumulative / total * 100 if total > 0 else 0

        # 6. 识别关键少数 (80/20)
        key_few = self._identify_key_few(sorted_data, threshold)

        # 7. ABC分类
        abc_classification = self._classify_abc(sorted_data)

        # 8. 生成可视化数据
        plot_data = self._generate_plot_data(sorted_data, threshold)

        # 9. 格式化结果
        result = {
            "total_count": total,
            "total_categories": len(sorted_data),
            "key_few_count": len(key_few),
            "key_few_percentage": len(key_few) / len(sorted_data) * 100 if sorted_data else 0,
            "key_few_contribution": sum(
                item["count"] for item in sorted_data
                if item["category"] in key_few
            ) / total * 100 if total > 0 else 0,
            "sorted_data": sorted_data,
            "key_few": key_few,
            "abc_classification": abc_classification
        }

        # 10. 生成洞察
        insights = self._generate_insights(result, threshold)

        # 11. 添加洞察到结果
        result["insights"] = insights

        metrics = {
            "total_count": total,
            "key_few_count": len(key_few),
            "concentration_ratio": result["key_few_contribution"]
        }

        return self.format_result(
            result=result,
            plot_data=plot_data,
            metrics=metrics,
            warnings=[]
        )

    def _aggregate_data(
        self,
        data: List[Dict],
        category_field: str,
        value_field: str
    ) -> List[Dict]:
        """聚合重复类别数据

        Args:
            data: 原始数据
            category_field: 类别字段名
            value_field: 数值字段名

        Returns:
            聚合后的数据
        """
        aggregated = {}

        for item in data:
            category = item.get(category_field, "Unknown")

            # 尝试获取数值
            count = item.get(value_field)
            if count is None:
                # 尝试其他可能的字段
                count = item.get("value", 1)

            # 聚合
            if category not in aggregated:
                aggregated[category] = {
                    "category": category,
                    "count": 0
                }

            aggregated[category]["count"] += count

        return list(aggregated.values())

    def _identify_key_few(
        self,
        sorted_data: List[Dict],
        threshold: float
    ) -> List[str]:
        """识别关键少数类别

        Args:
            sorted_data: 已排序的数据
            threshold: 累计占比阈值

        Returns:
            关键少数类别列表
        """
        key_few = []

        for item in sorted_data:
            if item["cumulative_pct"] <= threshold * 100:
                key_few.append(item["category"])
            else:
                break

        # 如果第一个类别就超过阈值，仍然返回它
        if not key_few and sorted_data:
            key_few.append(sorted_data[0]["category"])

        return key_few

    def _classify_abc(self, sorted_data: List[Dict]) -> Dict[str, List[str]]:
        """ABC分类

        - A类: 累计贡献率0-80%
        - B类: 累计贡献率80-95%
        - C类: 累计贡献率95-100%

        Args:
            sorted_data: 已排序的数据

        Returns:
            {"A": [...], "B": [...], "C": [...]}
        """
        classification = {"A": [], "B": [], "C": []}

        for item in sorted_data:
            if item["cumulative_pct"] <= 80:
                classification["A"].append(item["category"])
            elif item["cumulative_pct"] <= 95:
                classification["B"].append(item["category"])
            else:
                classification["C"].append(item["category"])

        return classification

    def _generate_plot_data(
        self,
        sorted_data: List[Dict],
        threshold: float
    ) -> Dict:
        """生成可视化数据

        Args:
            sorted_data: 已排序的数据
            threshold: 阈值

        Returns:
            可视化数据字典
        """
        return {
            "type": "pareto",
            "categories": [item["category"] for item in sorted_data],
            "counts": [item["count"] for item in sorted_data],
            "cumulative": [item["cumulative_pct"] for item in sorted_data],
            "threshold_line": threshold * 100,
            "colors": self._generate_colors(len(sorted_data))
        }

    def _generate_colors(self, n: int) -> List[str]:
        """生成颜色列表

        前几个关键少数用红色，其余用灰色

        Args:
            n: 类别数量

        Returns:
            颜色列表
        """
        colors = []
        for i in range(n):
            if i < 3:  # 前3个用不同深度的红色
                colors.append(f"rgba(255, {100 - i * 30}, 0, 0.7)")
            else:
                colors.append("rgba(200, 200, 200, 0.5)")
        return colors

    def _generate_insights(self, result: Dict, threshold: float) -> List[str]:
        """生成洞察建议

        Args:
            result: 分析结果
            threshold: 阈值

        Returns:
            洞察建议列表
        """
        insights = []

        # 关键少数洞察
        key_few_count = result["key_few_count"]
        total_categories = result["total_categories"]
        contribution = result["key_few_contribution"]

        if total_categories > 0:
            insights.append(
                f"🎯 前{key_few_count}类问题（占总数{key_few_count/total_categories*100:.1f}%）"
                f"贡献了{contribution:.1f}%的问题总量"
            )

        # ABC分类洞察
        abc = result["abc_classification"]
        if abc["A"]:
            insights.append(f"📌 A类关键问题（优先解决）: {', '.join(abc['A'][:3])}")

        if abc["B"]:
            insights.append(f"⚠️ B类次要问题: {', '.join(abc['B'][:3])}")

        # 改进建议
        if contribution >= 80:
            insights.append(f"💡 建议：优先解决'{result['key_few'][0]}'类问题，可消除{contribution:.1f}%的故障")
        else:
            insights.append("💡 问题分布较为分散，建议进一步分类细化")

        return insights

    def validate_input(self, data: List, config: Dict) -> tuple:
        """验证输入数据"""
        errors = []

        if not data or len(data) == 0:
            errors.append("数据不能为空")
            return False, errors

        if not isinstance(data, list):
            errors.append("数据必须是列表格式")
            return False, errors

        # 检查每个元素是否为字典
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"第{i}个元素必须是字典")
                return False, errors

        return True, errors
