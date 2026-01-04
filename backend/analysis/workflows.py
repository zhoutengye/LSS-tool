"""分析工作流 - 标准化的分析流程

定义可复用的分析流程，编排多个工具的调用。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session

from data import DataContext
from .decision_engine import DecisionEngine
from core.registry import registry


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_name: str
    dimension: str  # person/batch/process/workshop/time
    success: bool
    findings: List[Dict[str, Any]]  # 关键发现
    metrics: Dict[str, Any]         # 关键指标
    raw_results: Dict[str, Any]     # 原始数据
    errors: List[str] = None


class AnalysisWorkflow(ABC):
    """分析工作流抽象基类"""

    def __init__(
        self,
        tool_registry,
        decision_engine: DecisionEngine,
        db: Session
    ):
        self.registry = tool_registry
        self.decision_engine = decision_engine
        self.db = db

    @abstractmethod
    def execute(self, context: DataContext) -> WorkflowResult:
        """
        执行工作流

        Args:
            context: 数据上下文

        Returns:
            WorkflowResult: 工作流执行结果
        """
        pass


class ComprehensiveDiagnosisWorkflow(AnalysisWorkflow):
    """综合诊断工作流

    标准的"黑带专家"诊断流程:
    1. 数据概览
    2. 逐参数 SPC 分析
    3. 根本原因分析
    4. 风险评估
    5. 生成建议

    适用场景:
    - 每日生产报告
    - 批次放行决策
    - 异常批次调查
    """

    def execute(self, context: DataContext) -> WorkflowResult:
        """
        执行综合诊断

        Args:
            context: 数据上下文

        Returns:
            WorkflowResult
        """
        findings = []
        all_metrics = {}
        raw_results = {}
        errors = []

        try:
            # Step 1: 数据概览
            all_metrics["data_overview"] = self._analyze_data_overview(context)

            # Step 2: 获取所有需要分析的参数
            parameters = self._get_parameters_from_context(context)

            if not parameters:
                findings.append({
                    "type": "warning",
                    "severity": "INFO",
                    "description": "未找到需要分析的参数"
                })
                return WorkflowResult(
                    workflow_name="comprehensive_diagnosis",
                    dimension=context.dimension,
                    success=True,
                    findings=findings,
                    metrics=all_metrics,
                    raw_results=raw_results
                )

            # Step 3: 逐参数分析
            param_issues = []

            for param in parameters:
                node_code = param["node_code"]
                param_code = param["param_code"]

                # 3.1 获取时序数据
                measurements = self._get_measurements(
                    context,
                    node_code,
                    param_code
                )
                data_values = [m.value for m in measurements]

                if len(data_values) < self.decision_engine.config["min_data_points"]:
                    # 数据太少，跳过
                    continue

                # 3.2 获取参数规格
                param_def = self._get_param_def(node_code, param_code)
                if not param_def:
                    continue

                # 3.3 调用 SPC 工具
                spc_tool = self.registry.get_tool("spc")
                if not spc_tool:
                    errors.append("SPC工具未注册")
                    continue

                spc_result = spc_tool.run(data_values, {
                    "usl": param_def.get("usl"),
                    "lsl": param_def.get("lsl"),
                    "target": param_def.get("target")
                })

                # 3.4 决策引擎评估
                health = self.decision_engine.assess_parameter_health(
                    param, spc_result
                )

                # 3.5 记录问题参数
                if health["status"] in ["WARNING", "CRITICAL"]:
                    param_issues.append({
                        "param_info": param,
                        "health": health,
                        "spc_result": spc_result
                    })

                    findings.append({
                        "type": "parameter_issue",
                        "severity": health["status"],
                        "node_code": node_code,
                        "param_code": param_code,
                        "param_name": param.get("name", param_code),
                        "description": f"{param.get('name', param_code)} {health['issues'][0] if health['issues'] else '异常'}",
                        "data": {
                            "cpk": spc_result["metrics"]["cpk"],
                            "mean": spc_result["result"]["mean"],
                            "health_score": health["score"]
                        }
                    })

                # 保存原始结果
                raw_results[f"{node_code}.{param_code}"] = spc_result

            # Step 4: 根本原因分析 (如果有问题)
            root_causes = []
            if param_issues:
                knowledge_graph = {"nodes": [], "edges": []}  # TODO: 从数据库获取
                root_causes = self.decision_engine.diagnose_root_causes(
                    param_issues, knowledge_graph
                )

                for cause in root_causes:
                    findings.append({
                        "type": "root_cause",
                        "severity": "HIGH" if cause["probability"] > 0.3 else "MEDIUM",
                        "description": cause["root_cause"],
                        "probability": cause["probability"],
                        "category": cause["category"],
                        "evidence": cause["evidence"]
                    })

            # Step 5: 生成建议
            recommendations = []
            if root_causes or param_issues:
                knowledge_graph = {"nodes": [], "edges": []}  # TODO: 从数据库获取
                recommendations = self.decision_engine.generate_recommendations(
                    {"root_causes": root_causes, "param_issues": param_issues},
                    knowledge_graph
                )

                for rec in recommendations:
                    findings.append({
                        "type": "recommendation",
                        "severity": rec.get("priority", "MEDIUM"),
                        "action": rec["action"],
                        "estimated_impact": rec.get("estimated_impact", ""),
                        "effort": rec.get("effort", ""),
                        "based_on": rec.get("based_on", "")
                    })

            # Step 6: 优先级排序
            priority_actions = self.decision_engine.prioritize_actions(
                recommendations
            )

            all_metrics.update({
                "total_parameters": len(parameters),
                "analyzed_parameters": len(raw_results),
                "problem_parameters": len(param_issues),
                "root_causes_found": len(root_causes),
                "recommendations": len(recommendations),
                "priority_actions": priority_actions[:5]  # Top 5
            })

            return WorkflowResult(
                workflow_name="comprehensive_diagnosis",
                dimension=context.dimension,
                success=True,
                findings=findings,
                metrics=all_metrics,
                raw_results=raw_results,
                errors=errors if errors else None
            )

        except Exception as e:
            return WorkflowResult(
                workflow_name="comprehensive_diagnosis",
                dimension=context.dimension,
                success=False,
                findings=[],
                metrics={},
                raw_results={},
                errors=[str(e)]
            )

    def _analyze_data_overview(self, context: DataContext) -> Dict[str, Any]:
        """分析数据概览"""
        return {
            "total_batches": len(context.batches),
            "total_measurements": len(context.measurements),
            "dimension": context.dimension,
            "metadata": context.metadata
        }

    def _get_parameters_from_context(self, context: DataContext) -> List[Dict[str, Any]]:
        """从上下文中提取参数列表"""
        # 从 measurements 中提取唯一的 node_code + param_code 组合
        param_set = set()

        for m in context.measurements:
            param_set.add((m.node_code, m.param_code))

        # 查询参数定义
        parameters = []
        for node_code, param_code in param_set:
            param_def = self._get_param_def(node_code, param_code)
            if param_def:
                parameters.append({
                    "node_code": node_code,
                    "param_code": param_code,
                    "name": param_def.get("name", param_code),
                    "unit": param_def.get("unit", ""),
                    "role": param_def.get("role", ""),
                    "usl": param_def.get("usl"),
                    "lsl": param_def.get("lsl"),
                    "target": param_def.get("target")
                })

        return parameters

    def _get_param_def(self, node_code: str, param_code: str) -> Optional[Dict[str, Any]]:
        """获取参数定义"""
        import models
        param_def = self.db.query(models.ParameterDef).join(
            models.ProcessNode
        ).filter(
            models.ProcessNode.code == node_code,
            models.ParameterDef.code == param_code
        ).first()

        if not param_def:
            return None

        return {
            "name": param_def.name,
            "unit": param_def.unit,
            "role": param_def.role,
            "usl": param_def.usl,
            "lsl": param_def.lsl,
            "target": param_def.target
        }

    def _get_measurements(
        self,
        context: DataContext,
        node_code: str,
        param_code: str
    ) -> List[Any]:
        """获取测量数据"""
        return [
            m for m in context.measurements
            if m.node_code == node_code and m.param_code == param_code
        ]


class WorkflowRegistry:
    """工作流注册表"""

    def __init__(
        self,
        data_providers: Dict[str, Any],
        decision_engine: DecisionEngine,
        db: Session
    ):
        self.data_providers = data_providers
        self.decision_engine = decision_engine
        self.db = db
        self._workflows = {}

        # 注册默认工作流
        self.register("comprehensive_diagnosis", ComprehensiveDiagnosisWorkflow(
            registry,
            decision_engine,
            db
        ))

    def register(self, name: str, workflow: AnalysisWorkflow):
        """注册工作流"""
        self._workflows[name] = workflow

    def get(self, name: str) -> Optional[AnalysisWorkflow]:
        """获取工作流"""
        return self._workflows.get(name)

    def list_workflows(self) -> List[str]:
        """列出所有工作流"""
        return list(self._workflows.keys())
