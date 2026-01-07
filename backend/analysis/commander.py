"""智能工艺指挥官 - 核心决策引擎

这是连接"分析"与"行动"的桥梁。
不同于分析报告，指挥官输出的是**可执行的指令**。

核心职责：
1. 每日自动分析生产数据
2. 检测异常（SPC、风险、趋势）
3. 匹配对策库（ActionDef）
4. 生成角色化指令（DailyInstruction）
5. 推送到对应角色的终端

业务场景：
- 前一天 22:00：自动拉取全天数据，运行分析
- 次日 06:00：推送到操作工/QA/班长终端
- 操作工收到："E04温度偏高，请将蒸汽阀开度调至45%"
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from data import query_data_by_dimension, DataContext
from .orchestrator import BlackBeltCommander, DiagnosisReport
from .decision_engine import DecisionEngineFactory, AnalysisMode
from core.registry import registry
import models


@dataclass
class Instruction:
    """指令数据结构"""
    role: str                    # 目标角色
    content: str                 # 指令内容（自然语言）
    priority: str                # 优先级
    evidence: Dict[str, Any]     # 证据数据
    action_code: str             # 对策代码
    batch_id: Optional[str]      # 关联批次
    node_code: Optional[str]     # 关联工序
    param_code: Optional[str]    # 关联参数


class IntelligentCommander:
    """智能工艺指挥官

    从"黑带专家"升级为"指挥官"：
    - 不仅分析问题，还要下达指令
    - 不仅输出报告，还要推动行动
    - 不仅告知风险，还要指导对策

    工作流程：
        1. 数据分析（调用 BlackBeltCommander）
        2. 问题识别（提取 critical_issues 和 warnings）
        3. 对策匹配（查询 ActionDef）
        4. 指令生成（填充模板，生成自然语言）
        5. 角色分发（按 role 分组）
        6. 持久化存储（写入 DailyInstruction 表）
    """

    def __init__(
        self,
        db: Session,
        mode: AnalysisMode = AnalysisMode.RULE_BASED,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化指挥官

        Args:
            db: 数据库会话
            mode: 分析模式
            config: 配置参数
        """
        self.db = db
        self.mode = mode
        self.config = config or self._default_config()

        # 初始化黑带分析器（底层能力）
        self.analyzer = BlackBeltCommander(db, mode, config)

    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 触发阈值
            "cpk_critical": 0.8,
            "cpk_warning": 1.33,
            "risk_critical": 0.3,
            "risk_warning": 0.1,

            # 指令生成策略
            "max_instructions_per_role": 10,  # 每个角色最多收几条指令
            "aggregate_similar_issues": True,  # 是否合并相似问题
        }

    # ========================================
    # 核心功能：每日指令生成
    # ========================================

    def generate_daily_orders(
        self,
        target_date: str,
        dimensions: Optional[List[str]] = None
    ) -> Dict[str, List[Instruction]]:
        """
        生成每日指令（核心入口）

        这是 PPT 流程图的核心：
            前一天 22:00 → 数据引擎 → 智能编排器 → 角色指令生成器 → 次日 06:00 推送

        Args:
            target_date: 目标日期 (YYYY-MM-DD)，如 "2023-10-25"
            dimensions: 分析维度列表，默认 ["batch", "process", "workshop"]

        Returns:
            按角色分组的指令字典:
            {
                "Operator": [Instruction1, Instruction2, ...],
                "QA": [Instruction1, ...],
                "TeamLeader": [Instruction1, ...],
                "Manager": [Instruction1, ...]
            }

        Example:
            >>> commander = IntelligentCommander(db)
            >>> orders = commander.generate_daily_orders("2023-10-25")
            >>> print(f"操作工今日收到 {len(orders['Operator'])} 条指令")
        """
        if dimensions is None:
            dimensions = ["batch", "process", "workshop"]

        all_instructions = []

        # Step 1: 多维度分析（黑带思维）
        for dimension in dimensions:
            if dimension == "batch":
                # 分析所有批次
                batches = self.db.query(models.Batch).all()
                for batch in batches:
                    report = self.analyzer.analyze_by_batch(batch.id)
                    instructions = self._convert_report_to_instructions(
                        report,
                        target_date
                    )
                    all_instructions.extend(instructions)

            elif dimension == "process":
                # 分析所有关键工序
                nodes = self.db.query(models.ProcessNode).filter(
                    models.ProcessNode.node_type == "Unit"
                ).all()
                for node in nodes:
                    report = self.analyzer.analyze_by_process(node.code)
                    instructions = self._convert_report_to_instructions(
                        report,
                        target_date
                    )
                    all_instructions.extend(instructions)

            elif dimension == "workshop":
                # 分析所有车间
                blocks = self.db.query(models.ProcessNode).filter(
                    models.ProcessNode.node_type == "Block"
                ).all()
                for block in blocks:
                    report = self.analyzer.analyze_by_workshop(block.code)
                    instructions = self._convert_report_to_instructions(
                        report,
                        target_date
                    )
                    all_instructions.extend(instructions)

        # Step 2: 去重和优先级排序
        all_instructions = self._deduplicate_instructions(all_instructions)
        all_instructions.sort(
            key=lambda x: self._priority_score(x.priority),
            reverse=True
        )

        # Step 3: 按角色分组
        role_groups = self._group_by_role(all_instructions)

        # Step 4: 限制每个角色的指令数量
        for role in role_groups:
            role_groups[role] = role_groups[role][:self.config["max_instructions_per_role"]]

        # Step 5: 持久化到数据库
        self._save_instructions(role_groups, target_date)

        return role_groups

    def _convert_report_to_instructions(
        self,
        report: DiagnosisReport,
        target_date: str
    ) -> List[Instruction]:
        """
        将诊断报告转换为指令列表

        核心逻辑：
            1. 提取报告中的 critical_issues 和 warnings
            2. 为每个问题匹配 ActionDef（对策库）
            3. 填充指令模板，生成自然语言

        Args:
            report: 诊断报告
            target_date: 目标日期

        Returns:
            指令列表
        """
        instructions = []

        # 合并所有需要处理的问题
        all_issues = report.critical_issues + report.warnings

        for issue in all_issues:
            # 提取问题关键信息
            param_code = issue.get("param_code")
            node_code = issue.get("node_code")
            batch_id = issue.get("batch_id")
            severity = issue.get("severity")

            # 查询相关的风险代码
            risk_code = self._map_issue_to_risk_code(issue)

            if not risk_code:
                continue

            # 查询对策库
            actions = self.db.query(models.ActionDef).filter(
                models.ActionDef.risk_code == risk_code,
                models.ActionDef.active == True
            ).all()

            # 为每个对策生成指令
            for action in actions:
                # 填充模板变量
                template_vars = self._extract_template_vars(
                    issue,
                    report,
                    action
                )

                # 生成自然语言指令
                content = action.instruction_template.format(**template_vars)

                # 构造指令对象
                instruction = Instruction(
                    role=action.target_role,
                    content=content,
                    priority=action.priority,
                    evidence={
                        "severity": severity,
                        "cpk": issue.get("cpk"),
                        "current_value": issue.get("current_value"),
                        "target_value": issue.get("target_value"),
                    },
                    action_code=action.code,
                    batch_id=batch_id,
                    node_code=node_code,
                    param_code=param_code
                )

                instructions.append(instruction)

        return instructions

    def _map_issue_to_risk_code(self, issue: Dict[str, Any]) -> Optional[str]:
        """
        将问题映射到风险代码

        Example:
            温度偏高 → R_E04_TEMP_HIGH
            水分超标 → R_P01_MOISTURE_HIGH
        """
        param_code = issue.get("param_code")
        node_code = issue.get("node_code")
        severity = issue.get("severity")

        # 简化版映射逻辑（实际应从知识图谱查询）
        if param_code and "temp" in param_code.lower() and severity in ["CRITICAL", "HIGH"]:
            return f"R_{node_code}_TEMP_HIGH"
        elif param_code and "temp" in param_code.lower():
            return f"R_{node_code}_TEMP_LOW"
        elif param_code and "pressure" in param_code.lower():
            return f"R_{node_code}_PRESSURE_HIGH"
        elif param_code and "moisture" in param_code.lower():
            return "R_P01_MOISTURE_HIGH"
        elif param_code and "time" in param_code.lower():
            return f"R_{node_code}_TIME_SHORT"

        return None

    def _extract_template_vars(
        self,
        issue: Dict[str, Any],
        report: DiagnosisReport,
        action: models.ActionDef
    ) -> Dict[str, Any]:
        """
        提取模板变量

        支持的变量：
            {node_name}: 工序名称
            {current_value}: 当前值
            {target_value}: 目标值
            {batch_id}: 批次号
            {cpk}: Cpk值
            {suggested_valve}: 建议阀门开度
            {root_cause}: 根本原因
            {prob}: 概率
        """
        vars = {
            "node_name": issue.get("node_name", "未知工序"),
            "current_value": issue.get("current_value", 0),
            "target_value": issue.get("target_value", 0),
            "batch_id": issue.get("batch_id", ""),
            "cpk": issue.get("cpk", 0),
        }

        # 计算建议值（简化版）
        if "valve" in action.instruction_template:
            current_valve = 50  # 默认50%
            suggested_valve = current_valve - 5 if issue.get("current_value", 0) > issue.get("target_value", 0) else current_valve + 5
            vars["current_valve"] = current_valve
            vars["suggested_valve"] = suggested_valve

        # 提取根本原因（从 risk_assessments）
        if report.risk_assessments:
            top_risk = report.risk_assessments[0]
            vars["root_cause"] = top_risk.get("risk_name", "设备异常")
            vars["prob"] = int(top_risk.get("probability", 0) * 100)

        return vars

    # ========================================
    # 辅助方法
    # ========================================

    def _deduplicate_instructions(self, instructions: List[Instruction]) -> List[Instruction]:
        """去重相似的指令"""
        # 简化版：根据 action_code + batch_id 去重
        seen = set()
        unique = []
        for inst in instructions:
            key = (inst.action_code, inst.batch_id)
            if key not in seen:
                seen.add(key)
                unique.append(inst)
        return unique

    def _priority_score(self, priority: str) -> int:
        """优先级转换为分数"""
        scores = {
            "CRITICAL": 100,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 25
        }
        return scores.get(priority, 0)

    def _group_by_role(self, instructions: List[Instruction]) -> Dict[str, List[Instruction]]:
        """按角色分组"""
        groups = {
            "Operator": [],
            "QA": [],
            "TeamLeader": [],
            "Manager": []
        }

        for inst in instructions:
            if inst.role in groups:
                groups[inst.role].append(inst)

        return groups

    def _save_instructions(
        self,
        role_groups: Dict[str, List[Instruction]],
        target_date: str
    ):
        """
        持久化指令到数据库

        写入 DailyInstruction 表，用于：
            1. 次日推送
            2. 追溯历史
            3. 闭环管理
        """
        for role, instructions in role_groups.items():
            for inst in instructions:
                record = models.DailyInstruction(
                    target_date=target_date,
                    role=role,
                    content=inst.content,
                    priority=inst.priority,
                    evidence=inst.evidence,
                    action_code=inst.action_code,
                    batch_id=inst.batch_id,
                    node_code=inst.node_code,
                    param_code=inst.param_code,
                    status="Pending"
                )
                self.db.add(record)

        self.db.commit()
        print(f"✅ 已保存 {sum(len(v) for v in role_groups.values())} 条指令到数据库")

    # ========================================
    # 查询接口
    # ========================================

    def get_instructions_by_role(
        self,
        role: str,
        target_date: str,
        status: Optional[str] = None
    ) -> List[models.DailyInstruction]:
        """
        查询指定角色的指令

        这是前端调用"我的指令"的接口。

        Args:
            role: 角色（Operator/QA/TeamLeader/Manager）
            target_date: 目标日期
            status: 状态过滤（Pending/Read/Done）

        Returns:
            指令列表
        """
        query = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.role == role,
            models.DailyInstruction.target_date == target_date
        )

        if status:
            # 支持逗号分隔的多个状态: "Pending,Read" -> ["Pending", "Read"]
            status_list = [s.strip() for s in status.split(',')]
            query = query.filter(models.DailyInstruction.status.in_(status_list))

        return query.order_by(
            models.DailyInstruction.priority.desc(),
            models.DailyInstruction.instruction_date.desc()
        ).all()

    def mark_instruction_read(self, instruction_id: int):
        """标记指令为已读"""
        inst = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.id == instruction_id
        ).first()

        if inst:
            inst.status = "Read"
            inst.read_at = datetime.now()
            self.db.commit()

    def mark_instruction_done(self, instruction_id: int, feedback: str = ""):
        """标记指令为已完成"""
        inst = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.id == instruction_id
        ).first()

        if inst:
            inst.status = "Done"
            inst.done_at = datetime.now()
            inst.feedback = feedback
            self.db.commit()
