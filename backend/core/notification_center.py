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
            models.DailyInstruction.target_role == "Operator",
            models.DailyInstruction.status == "pending"
        ).order_by(
            models.DailyInstruction.priority.desc(),
            models.DailyInstruction.created_at.desc()
        ).limit(10).all()

        # 转换为前端友好的格式
        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.title,
                "content": inst.content,
                "node_code": inst.node_code,
                "created_at": inst.created_at.isoformat(),
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
        # TODO: 实现具体逻辑
        # 1. 查询时间窗口内的测量数据
        # 2. 计算Cpk趋势
        # 3. 统计问题分布
        # 4. 生成建议

        return {
            "success": False,
            "message": "待实现"
        }

    def get_qa_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取QA的通知列表

        Args:
            user_id: 用户ID (可选)

        Returns:
            通知列表
        """
        # 查询待处理的指令
        instructions = self.db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_role == "QA",
            models.DailyInstruction.status == "pending"
        ).order_by(
            models.DailyInstruction.priority.desc()
        ).limit(10).all()

        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.title,
                "content": inst.content,
                "node_code": inst.node_code,
                "created_at": inst.created_at.isoformat(),
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
            models.DailyInstruction.target_role == "TeamLeader",
            models.DailyInstruction.status == "pending"
        ).order_by(
            models.DailyInstruction.priority.desc()
        ).limit(10).all()

        notifications = []
        for inst in instructions:
            notifications.append({
                "id": inst.id,
                "level": self._map_priority_to_level(inst.priority),
                "title": inst.title,
                "content": inst.content,
                "node_code": inst.node_code,
                "created_at": inst.created_at.isoformat(),
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
