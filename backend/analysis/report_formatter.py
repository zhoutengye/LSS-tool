"""报告格式化器 - 生成结构化报告

将工作流结果转换为标准化的诊断报告。
"""

from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .orchestrator import DiagnosisReport
from .workflows import WorkflowResult
from data import DataContext


class ReportFormatter:
    """报告格式化器"""

    def build_report(
        self,
        result: WorkflowResult,
        context: DataContext
    ) -> DiagnosisReport:
        """
        构建诊断报告

        Args:
            result: 工作流执行结果
            context: 数据上下文

        Returns:
            DiagnosisReport: 结构化的诊断报告
        """
        # 分类发现
        critical = []
        warnings = []
        opportunities = []

        for finding in result.findings:
            severity = finding.get("severity", "INFO")

            if severity == "CRITICAL":
                critical.append(finding)
            elif severity in ["WARNING", "HIGH"]:
                warnings.append(finding)
            else:
                opportunities.append(finding)

        # 提取行动建议
        priority_actions = result.metrics.get("priority_actions", [])

        # 生成建议摘要
        recommendations = self._generate_recommendations_summary(priority_actions)

        # 确定整体状态
        if critical:
            overall_status = "CRITICAL"
        elif warnings:
            overall_status = "WARNING"
        else:
            overall_status = "NORMAL"

        # 生成唯一标识
        analysis_id = self._generate_analysis_id(context)

        # 提取风险评估
        risk_assessments = [
            f for f in result.findings
            if f.get("type") == "root_cause"
        ]

        return DiagnosisReport(
            dimension=context.dimension,
            analysis_id=analysis_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            overall_status=overall_status,
            critical_issues=critical,
            warnings=warnings,
            opportunities=opportunities,
            parameter_analyses=result.raw_results,
            risk_assessments=risk_assessments,
            priority_actions=priority_actions,
            recommendations=recommendations,
            analysis_metadata={
                "generated_at": datetime.now().isoformat(),
                "dimension": context.dimension,
                "mode": "rule_based",  # TODO: 从决策引擎获取
                "total_parameters": result.metrics.get("total_parameters", 0),
                "analyzed_parameters": result.metrics.get("analyzed_parameters", 0),
                "problem_parameters": result.metrics.get("problem_parameters", 0),
                "tool_version": "1.0.0"
            }
        )

    def _generate_recommendations_summary(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        生成建议摘要

        Args:
            actions: 行动建议列表

        Returns:
            建议摘要列表
        """
        summaries = []

        for action in actions[:5]:  # Top 5
            action_text = action["action"]
            impact = action.get("estimated_impact", "")

            if impact:
                summaries.append(f"{action_text} (预计: {impact})")
            else:
                summaries.append(action_text)

        return summaries

    def _generate_analysis_id(self, context: DataContext) -> str:
        """
        生成唯一分析标识

        Args:
            context: 数据上下文

        Returns:
            分析ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{context.dimension}_{timestamp}"

    def merge_reports(
        self,
        reports: List[DiagnosisReport]
    ) -> Dict[str, Any]:
        """
        汇总多个报告

        用于生成跨维度、跨车间的综合报告。

        Args:
            reports: 多个诊断报告

        Returns:
            汇总后的报告
        """
        all_critical = []
        all_warnings = []
        all_actions = []

        for report in reports:
            all_critical.extend(report.critical_issues)
            all_warnings.extend(report.warnings)
            all_actions.extend(report.priority_actions)

        # 按优先级排序行动
        all_actions.sort(key=lambda x: x.get("_priority_score", 0), reverse=True)

        # 确定整体状态
        if all_critical:
            overall_status = "CRITICAL"
        elif all_warnings:
            overall_status = "WARNING"
        else:
            overall_status = "NORMAL"

        return {
            "analysis_type": "merged_report",
            "overall_status": overall_status,
            "total_reports": len(reports),
            "critical_issues_count": len(all_critical),
            "warnings_count": len(all_warnings),
            "critical_issues": all_critical[:10],  # Top 10
            "warnings": all_warnings[:20],  # Top 20
            "priority_actions": all_actions[:10],  # Top 10
            "generated_at": datetime.now().isoformat()
        }

    def to_dict(self, report: DiagnosisReport) -> Dict[str, Any]:
        """
        转换为字典（用于 JSON 序列化）

        Args:
            report: 诊断报告

        Returns:
            字典格式的报告
        """
        return asdict(report)

    def to_json(self, report: DiagnosisReport) -> str:
        """
        转换为 JSON 字符串

        Args:
            report: 诊断报告

        Returns:
            JSON 字符串
        """
        import json
        return json.dumps(
            self.to_dict(report),
            ensure_ascii=False,
            indent=2
        )

    def to_markdown(self, report: DiagnosisReport) -> str:
        """
        转换为 Markdown 格式

        Args:
            report: 诊断报告

        Returns:
            Markdown 字符串
        """
        lines = []

        # 标题
        lines.append(f"# {report.dimension.upper()} 生产诊断报告")
        lines.append(f"**分析ID**: {report.analysis_id}")
        lines.append(f"**分析日期**: {report.analysis_date}")
        lines.append(f"**整体状态**: {report.overall_status}")
        lines.append("")

        # 紧急问题
        if report.critical_issues:
            lines.append("## 🔴 紧急问题")
            for issue in report.critical_issues:
                lines.append(f"- **{issue.get('param_name', issue.get('description', ''))}**")
                lines.append(f"  - 严重程度: {issue.get('severity', '')}")
                if 'cpk' in issue.get('data', {}):
                    lines.append(f"  - Cpk: {issue['data']['cpk']}")
                lines.append("")
            lines.append("")

        # 警告
        if report.warnings:
            lines.append("## ⚠️ 警告")
            for warning in report.warnings[:10]:
                lines.append(f"- {warning.get('description', '')}")
            lines.append("")

        # 行动建议
        if report.priority_actions:
            lines.append("## ✅ 优先级行动")
            for i, action in enumerate(report.priority_actions[:5], 1):
                lines.append(f"{i}. **{action['action']}**")
                lines.append(f"   - 优先级: {action.get('priority', '')}")
                if action.get('estimated_impact'):
                    lines.append(f"   - 预期效果: {action['estimated_impact']}")
                if action.get('effort'):
                    lines.append(f"   - 工作量: {action['effort']}")
                lines.append("")
            lines.append("")

        # 元数据
        lines.append("## 📊 分析元数据")
        lines.append(f"- 分析时间: {report.analysis_metadata.get('generated_at', '')}")
        lines.append(f"- 分析维度: {report.dimension}")
        lines.append(f"- 总参数数: {report.analysis_metadata.get('total_parameters', 0)}")
        lines.append(f"- 分析参数数: {report.analysis_metadata.get('analyzed_parameters', 0)}")
        lines.append(f"- 问题参数数: {report.analysis_metadata.get('problem_parameters', 0)}")

        return "\n".join(lines)
