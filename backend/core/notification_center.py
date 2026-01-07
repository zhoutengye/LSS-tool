"""消息分发中心 (Notification Center)

功能: 基于角色的消息分发、多渠道推送、优先级管理
真实能力: 支持App推送、邮件、短信、企业微信
Demo能力: API返回筛选后的JSON数据
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from datetime import datetime, timedelta


class NotificationCenter:
    """消息分发中心

    根据用户角色分发不同的消息和报告
    """

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def get_worker_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取操作工的通知列表

        Args:
            user_id: 用户ID (可选)

        Returns:
            通知列表
        """
        # 查询待处理的指令
        instructions = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.role == "Operator",
            models.DailyInstruction.status == "Pending"
        ).order_by(
            models.DailyInstruction.priority.desc(),
            models.DailyInstruction.instruction_date.desc()
        ).limit(10).all()

        # 转换为前端友好的格式
        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.content[:50] + "..." if inst.content else "",
                "content": inst.content,
                "node_code": getattr(inst, 'node_code', ''),
                "created_at": inst.instruction_date.isoformat() if inst.instruction_date else "",
                "action_required": True
            })

        return notifications

    def get_manager_report(self, time_window: int = 7) -> Dict[str, Any]:
        """获取经理的洞察报告

        Args:
            time_window: 时间窗口 (天数)

        Returns:
            报告数据
        """
        try:
            from datetime import datetime, timedelta
            import numpy as np
            from sqlalchemy import func

            # 1. 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_window)

            # 2. 查询测量数据统计
            measurements_count = self.db.query(func.count(models.Measurement.id)).filter(
                models.Measurement.timestamp >= start_date
            ).scalar()

            # 3. 查询关键参数的Cpk趋势 (Demo: 模拟数据)
            cpk_trend = self._calculate_demo_cpk_trend(time_window)

            # 4. 统计待处理指令数量
            pending_instructions = self.db.query(func.count(models.DailyInstruction.id)).filter(
                models.DailyInstruction.status == "Pending",
                models.DailyInstruction.instruction_date >= start_date
            ).scalar()

            # 5. 风险事件统计
            risk_events = self.db.query(func.count(models.RiskNode.id)).scalar()

            # 6. 生成洞察建议
            insights = self._generate_manager_insights(
                measurements_count, cpk_trend, pending_instructions
            )

            return {
                "success": True,
                "time_window": time_window,
                "summary": {
                    "measurements_count": measurements_count,
                    "pending_instructions": pending_instructions,
                    "risk_nodes_count": risk_events,
                    "avg_cpk": np.mean([d["cpk"] for d in cpk_trend]) if cpk_trend else 0
                },
                "cpk_trend": cpk_trend,
                "insights": insights,
                "chart_data": {
                    "type": "line",
                    "title": f"近{time_window}天Cpk趋势",
                    "x_axis": [d["date"] for d in cpk_trend],
                    "y_axis": [d["cpk"] for d in cpk_trend],
                    "threshold": 1.33
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"生成报告失败: {str(e)}"
            }

    def _calculate_demo_cpk_trend(self, days: int) -> List[Dict[str, Any]]:
        """计算演示用的Cpk趋势数据

        Args:
            days: 天数

        Returns:
            Cpk趋势数据
        """
        from datetime import datetime, timedelta
        import random

        trend = []
        base_date = datetime.now() - timedelta(days=days)

        # Demo: 生成模拟的Cpk数据，显示改善趋势
        base_cpk = 1.0
        for i in range(days):
            date = base_date + timedelta(days=i)
            # 模拟Cpk逐渐改善
            cpk_value = base_cpk + (i * 0.05) + random.uniform(-0.1, 0.15)
            cpk_value = min(max(cpk_value, 0.8), 2.0)  # 限制在合理范围内

            trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "cpk": round(cpk_value, 3)
            })

        return trend

    def _generate_manager_insights(self, measurements_count: int, cpk_trend: List[Dict], pending_instructions: int) -> List[str]:
        """生成经理洞察建议

        Args:
            measurements_count: 测量数据量
            cpk_trend: Cpk趋势
            pending_instructions: 待处理指令数

        Returns:
            洞察建议列表
        """
        insights = []

        # 分析Cpk趋势
        if cpk_trend:
            recent_cpk = cpk_trend[-1]["cpk"]
            if recent_cpk >= 1.33:
                insights.append(f"✅ 过程能力良好，最新Cpk为{recent_cpk:.2f}，达到A级标准")
            elif recent_cpk >= 1.0:
                insights.append(f"⚠️ 过程能力尚可，最新Cpk为{recent_cpk:.2f}，建议持续监控")
            else:
                insights.append(f"❌ 过程能力不足，最新Cpk为{recent_cpk:.2f}，需要立即改进")

            # 分析趋势
            if len(cpk_trend) >= 2:
                improvement = cpk_trend[-1]["cpk"] - cpk_trend[0]["cpk"]
                if improvement > 0.1:
                    insights.append(f"📈 Cpk呈上升趋势，较{len(cpk_trend)}天前提升{improvement:.2f}")
                elif improvement < -0.1:
                    insights.append(f"📉 Cpk呈下降趋势，较{len(cpk_trend)}天前下降{abs(improvement):.2f}")

        # 分析待处理指令
        if pending_instructions > 10:
            insights.append(f"⚠️ 待处理指令较多({pending_instructions}条)，建议协调资源加快处理")
        elif pending_instructions > 0:
            insights.append(f"ℹ️ 当前有{pending_instructions}条待处理指令")

        # 数据量统计
        if measurements_count > 0:
            insights.append(f"📊 近期已收集{measurements_count}条测量数据")

        return insights

    def get_qa_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取QA的通知列表

        Args:
            user_id: 用户ID (可选)

        Returns:
            通知列表
        """
        # 查询待处理的指令
        instructions = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.role == "QA",
            models.DailyInstruction.status == "Pending"
        ).order_by(
            models.DailyInstruction.priority.desc()
        ).limit(10).all()

        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.content[:50] + "..." if inst.content else "",
                "content": inst.content,
                "node_code": getattr(inst, 'node_code', ''),
                "created_at": inst.instruction_date.isoformat() if inst.instruction_date else "",
                "action_required": True
            })

        return notifications

    def get_teamleader_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取班长的通知列表

        Args:
            user_id: 用户ID (可选)

        Returns:
            通知列表
        """
        instructions = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.role == "TeamLeader",
            models.DailyInstruction.status == "Pending"
        ).order_by(
            models.DailyInstruction.priority.desc()
        ).limit(10).all()

        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.content[:50] + "..." if inst.content else "",
                "content": inst.content,
                "node_code": getattr(inst, 'node_code', ''),
                "created_at": inst.instruction_date.isoformat() if inst.instruction_date else "",
                "action_required": True
            })

        return notifications

    def mark_as_read(self, instruction_id: int, user_id: str) -> bool:
        """标记指令为已读

        Args:
            instruction_id: 指令ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        try:
            instruction = self.db.query(models.DailyInstruction).filter(
                models.DailyInstruction.id == instruction_id
            ).first()

            if instruction:
                instruction.status = "in_progress"
                instruction.updated_at = datetime.now()
                self.db.commit()
                return True

            return False
        except Exception as e:
            self.db.rollback()
            return False

    def mark_as_done(self, instruction_id: int, user_id: str, feedback: str = "") -> bool:
        """标记指令为完成

        Args:
            instruction_id: 指令ID
            user_id: 用户ID
            feedback: 执行反馈

        Returns:
            是否成功
        """
        try:
            instruction = self.db.query(models.DailyInstruction).filter(
                models.DailyInstruction.id == instruction_id
            ).first()

            if instruction:
                instruction.status = "completed"
                instruction.feedback = feedback
                instruction.updated_at = datetime.now()
                self.db.commit()
                return True

            return False
        except Exception as e:
            self.db.rollback()
            return False

    def _map_priority_to_level(self, priority: str) -> str:
        """映射优先级到显示级别

        Args:
            priority: 优先级 (CRITICAL/HIGH/MEDIUM/LOW)

        Returns:
            显示级别 (high/normal/low)
        """
        mapping = {
            "CRITICAL": "high",
            "HIGH": "high",
            "MEDIUM": "normal",
            "LOW": "low"
        }
        return mapping.get(priority, "normal")
