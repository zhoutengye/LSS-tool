"""决策引擎 - 可插拔的决策逻辑

定义统一的决策接口，支持多种实现方式:
- RuleBasedDecisionEngine: 基于阈值的规则
- LLMDecisionEngine: 基于 LLM 的推理（预留接口）
- HybridDecisionEngine: 混合模式（预留接口）
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum


class AnalysisMode(Enum):
    """分析模式"""
    RULE_BASED = "rule_based"       # 纯规则引擎
    LLM_BASED = "llm_based"         # 纯 LLM (未来)
    HYBRID = "hybrid"               # 混合模式 (未来)


class DecisionEngine(ABC):
    """决策引擎抽象基类

    定义统一的决策接口，支持多种实现方式。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化决策引擎

        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # SPC 阈值
            "cpk_critical": 0.8,      # Cpk < 0.8 = CRITICAL
            "cpk_warning": 1.33,       # Cpk < 1.33 = WARNING

            # 风险概率阈值
            "risk_critical": 0.3,      # 概率 > 30% = CRITICAL
            "risk_warning": 0.1,       # 概率 > 10% = WARNING

            # 数据质量要求
            "min_data_points": 5,      # 最少数据点数

            # 分析优先级权重
            "priority_weights": {
                "cpk": 0.4,           # 过程能力权重
                "risk": 0.3,          # 风险概率权重
                "trend": 0.2,         # 趋势异常权重
                "violations": 0.1     # 违规点数量权重
            }
        }

    @abstractmethod
    def assess_parameter_health(
        self,
        param_info: Dict[str, Any],
        spc_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估参数健康度

        Args:
            param_info: 参数信息 {node_code, param_code, name, ...}
            spc_result: SPC 分析结果

        Returns:
            {
                "status": "CRITICAL" | "WARNING" | "NORMAL",
                "score": float,  # 0-100 健康度评分
                "issues": ["issue1", "issue2"],
                "confidence": float  # 置信度
            }
        """
        pass

    @abstractmethod
    def diagnose_root_causes(
        self,
        param_issues: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        诊断根本原因

        Args:
            param_issues: 参数问题列表
            knowledge_graph: 知识图谱数据

        Returns:
            [
                {
                    "root_cause": "温度传感器故障",
                    "probability": 0.8,
                    "category": "Equipment",
                    "evidence": ["Cpk低", "温度波动大"]
                }
            ]
        """
        pass

    @abstractmethod
    def generate_recommendations(
        self,
        diagnosis: Dict[str, Any],
        knowledge_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成改进建议

        Args:
            diagnosis: 诊断结果
            knowledge_graph: 知识图谱

        Returns:
            [
                {
                    "action": "校准温度传感器",
                    "priority": "HIGH",
                    "estimated_impact": "Cpk提升至1.5",
                    "effort": "1小时"
                }
            ]
        """
        pass

    @abstractmethod
    def prioritize_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        行动优先级排序

        Args:
            actions: 行动列表

        Returns:
            按优先级排序的行动列表
        """
        pass


class RuleBasedDecisionEngine(DecisionEngine):
    """基于规则的决策引擎

    使用阈值和专家规则进行决策。

    优点:
    - 快速、可解释、稳定
    - 适合实时监控
    - 可直接部署
    """

    def assess_parameter_health(
        self,
        param_info: Dict[str, Any],
        spc_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于阈值的健康度评估

        评估规则:
        1. Cpk 评估: < 0.8 = CRITICAL, < 1.33 = WARNING
        2. 违规点扣分: 每个违规点扣10分
        """
        # 提取 SPC 结果
        metrics = spc_result.get("metrics", {})
        result = spc_result.get("result", {})

        cpk = metrics.get("cpk")
        violations = result.get("violations", [])

        # 规则 1: Cpk 评估
        if cpk is None:
            status = "UNKNOWN"
            score = 50
        elif cpk < self.config["cpk_critical"]:
            status = "CRITICAL"
            score = 20  # Cpk < 0.8，基础20分
        elif cpk < self.config["cpk_warning"]:
            status = "WARNING"
            score = 50  # Cpk < 1.33，基础50分
        else:
            status = "NORMAL"
            # Cpk >= 1.33，基础60分 + Cpk * 13.3
            score = min(100, int(60 + cpk * 13.3))

        # 规则 2: 违规点扣分
        if len(violations) > 0:
            score -= min(30, len(violations) * 10)
            if status == "NORMAL":
                status = "WARNING"

        # 确保分数在 0-100 范围内
        score = max(0, min(100, score))

        # 生成问题描述
        issues = []
        if cpk and cpk < self.config["cpk_warning"]:
            issues.append(f"过程能力不足 (Cpk={cpk:.2f})")
        if len(violations) > 0:
            issues.append(f"发现{len(violations)}个超规格点")

        return {
            "status": status,
            "score": score,
            "issues": issues,
            "confidence": 1.0,  # 规则引擎置信度100%
            "method": "rule_based"
        }

    def diagnose_root_causes(
        self,
        param_issues: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        基于风险图谱的根本原因诊断

        诊断规则:
        1. 匹配参数到风险节点
        2. 计算风险概率 = 基础概率 * 权重
        3. 过滤低概率风险
        """
        root_causes = []

        for issue in param_issues:
            node_code = issue.get("param_info", {}).get("node_code")
            param_code = issue.get("param_info", {}).get("param_code")

            # 简化实现：根据节点编码推断风险
            # 实际应该查询 knowledge_graph 中的 RiskNode
            related_risks = self._infer_risks(node_code, param_code)

            for risk in related_risks:
                probability = risk["base_probability"] * risk.get("weight", 1.0)

                if probability > self.config["risk_warning"]:
                    root_causes.append({
                        "root_cause": risk["name"],
                        "probability": min(1.0, probability),  # 最大不超过1.0
                        "category": risk["category"],
                        "evidence": [issue.get("issue", "异常")],
                        "risk_code": risk.get("code", "")
                    })

        # 按概率排序
        root_causes.sort(key=lambda x: x["probability"], reverse=True)

        return root_causes[:5]  # 返回 Top 5

    def generate_recommendations(
        self,
        diagnosis: Dict[str, Any],
        knowledge_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        基于规则库生成建议

        规则库: 问题 -> 建议映射
        """
        recommendations = []

        # 规则库: 问题 -> 建议映射
        rule_book = {
            "Equipment": {
                "温度传感器": {
                    "action": "校准温度传感器",
                    "priority": "HIGH",
                    "effort": "1小时",
                    "estimated_impact": "Cpk提升至1.5以上"
                },
                "液位计": {
                    "action": "检查液位计连接",
                    "priority": "MEDIUM",
                    "effort": "30分钟",
                    "estimated_impact": "消除虚假报警"
                },
                "设备": {
                    "action": "检查设备状态",
                    "priority": "HIGH",
                    "effort": "2小时",
                    "estimated_impact": "恢复过程稳定性"
                }
            },
            "Material": {
                "药材": {
                    "action": "检验原料质量",
                    "priority": "HIGH",
                    "effort": "2小时",
                    "estimated_impact": "提升得率5%"
                }
            },
            "Method": {
                "工艺参数": {
                    "action": "优化工艺参数",
                    "priority": "MEDIUM",
                    "effort": "实验验证",
                    "estimated_impact": "提升过程稳定性"
                }
            },
            "Man": {
                "人员": {
                    "action": "加强人员培训",
                    "priority": "MEDIUM",
                    "effort": "1天",
                    "estimated_impact": "减少人为偏差"
                }
            }
        }

        root_causes = diagnosis.get("root_causes", [])

        for cause in root_causes:
            category = cause["category"]
            name = cause["root_cause"]

            # 模糊匹配规则
            if category in rule_book:
                for key, rule in rule_book[category].items():
                    if key in name:
                        recommendations.append({
                            **rule,
                            "based_on": f"诊断: {name} (概率{cause['probability']:.0%})"
                        })

        return recommendations

    def prioritize_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        优先级排序 (加权评分)

        评分规则:
        - HIGH 优先级: +100分
        - MEDIUM 优先级: +50分
        - LOW 优先级: +20分
        - 预期影响大: +40分
        """
        weights = self.config.get("priority_weights", {})

        scored_actions = []
        for action in actions:
            score = 0

            # 规则: 基于优先级打分
            priority = action.get("priority", "LOW")
            if priority == "HIGH":
                score += 100
            elif priority == "MEDIUM":
                score += 50
            else:
                score += 20

            # 规则: 基于影响打分
            impact = action.get("estimated_impact", "")
            if "Cpk" in impact:
                score += weights.get("cpk", 0.4) * 100

            scored_actions.append({**action, "_priority_score": score})

        # 按分数排序
        scored_actions.sort(key=lambda x: x["_priority_score"], reverse=True)

        return scored_actions

    def _infer_risks(self, node_code: str, param_code: str) -> List[Dict[str, Any]]:
        """
        根据节点和参数推断可能的风险

        简化实现，实际应该查询 RiskNode 表
        """
        # 这里返回模拟数据，实际应该从数据库查询
        risks = []

        # 根据参数类型推断风险
        if "temp" in param_code.lower() or "温度" in param_code:
            risks.append({
                "code": f"TEMP_{node_code}",
                "name": f"{node_code}温度异常",
                "category": "Equipment",
                "base_probability": 0.05,
                "weight": 15.0  # 异常时概率放大15倍
            })

        if "pressure" in param_code.lower() or "压力" in param_code:
            risks.append({
                "code": f"PRES_{node_code}",
                "name": f"{node_code}压力异常",
                "category": "Equipment",
                "base_probability": 0.03,
                "weight": 20.0
            })

        # 通用风险
        risks.append({
            "code": f"GENERIC_{node_code}",
            "name": f"{node_code}设备异常",
            "category": "Equipment",
            "base_probability": 0.02,
            "weight": 10.0
        })

        return risks


class LLMDecisionEngine(DecisionEngine):
    """基于 LLM 的决策引擎（预留接口）

    使用大语言模型进行推理。

    优点:
    - 更灵活的自然语言理解
    - 能处理复杂的多因素因果关系
    - 可生成更人性化的建议

    实现方式:
    - 调用 OpenAI API / 本地模型
    - 使用 agent_tools.py 包装的工具
    - 通过 function calling 调用分析工具
    """

    def assess_parameter_health(self, param_info: Dict[str, Any], spc_result: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: 调用 LLM 分析
        raise NotImplementedError("LLM决策引擎尚未实现")

    def diagnose_root_causes(self, param_issues: List[Dict[str, Any]], knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        # TODO: 调用 LLM 推理
        raise NotImplementedError("LLM决策引擎尚未实现")

    def generate_recommendations(self, diagnosis: Dict[str, Any], knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        # TODO: 调用 LLM 生成建议
        raise NotImplementedError("LLM决策引擎尚未实现")

    def prioritize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # TODO: 调用 LLM 排序
        raise NotImplementedError("LLM决策引擎尚未实现")


class HybridDecisionEngine(DecisionEngine):
    """混合决策引擎（预留接口）

    结合规则和 LLM 的优势:
    - 规则处理快速、明确的判断
    - LLM 处理复杂、模糊的推理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rule_engine = RuleBasedDecisionEngine(config)
        self.llm_engine = LLMDecisionEngine(config)

    def assess_parameter_health(self, param_info: Dict[str, Any], spc_result: Dict[str, Any]) -> Dict[str, Any]:
        # 优先用规则，复杂情况用 LLM
        cpk = spc_result.get("metrics", {}).get("cpk")

        if cpk and (cpk < 0.5 or cpk > 2.0):
            # 明确情况：用规则
            return self.rule_engine.assess_parameter_health(param_info, spc_result)
        else:
            # 模糊区域：用 LLM
            return self.llm_engine.assess_parameter_health(param_info, spc_result)

    def diagnose_root_causes(self, param_issues: List[Dict[str, Any]], knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 规则筛选 + LLM 深度分析
        # TODO: 实现混合逻辑
        raise NotImplementedError("混合决策引擎尚未实现")

    def generate_recommendations(self, diagnosis: Dict[str, Any], knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 规则生成标准建议 + LLM 生成个性化建议
        # TODO: 实现混合逻辑
        raise NotImplementedError("混合决策引擎尚未实现")

    def prioritize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # 规则初筛 + LLM 微调
        # TODO: 实现混合逻辑
        raise NotImplementedError("混合决策引擎尚未实现")


class DecisionEngineFactory:
    """决策引擎工厂"""

    @staticmethod
    def create(mode: AnalysisMode, config: Optional[Dict[str, Any]] = None) -> DecisionEngine:
        """
        创建决策引擎实例

        Args:
            mode: 分析模式
            config: 配置参数

        Returns:
            DecisionEngine: 决策引擎实例
        """
        if mode == AnalysisMode.RULE_BASED:
            return RuleBasedDecisionEngine(config)
        elif mode == AnalysisMode.LLM_BASED:
            return LLMDecisionEngine(config)
        elif mode == AnalysisMode.HYBRID:
            return HybridDecisionEngine(config)
        else:
            raise ValueError(f"Unknown analysis mode: {mode}")
