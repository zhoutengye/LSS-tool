"""指令管理API路由

提供工艺指令的查询、更新和生成接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models

router = APIRouter(prefix="/api/instructions", tags=["指令管理"])


@router.get("/")
def get_instructions(
    role: str,
    status: Optional[str] = None,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取指令列表

    GET /api/instructions?role=Operator&status=Pending,Read
    """
    try:
        from analysis import IntelligentCommander
        from datetime import datetime

        commander = IntelligentCommander(db)

        # 默认查询今天
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        instructions = commander.get_instructions_by_role(
            role=role,
            target_date=target_date,
            status=status
        )

        return {
            "instructions": [
                {
                    "id": inst.id,
                    "role": inst.role,
                    "content": inst.content,
                    "priority": inst.priority,
                    "status": inst.status,
                    "evidence": inst.evidence,
                    "node_code": inst.node_code,
                    "batch_id": inst.batch_id,
                    "created_at": inst.instruction_date.isoformat() if inst.instruction_date else None
                }
                for inst in instructions
            ],
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@router.post("/{instruction_id}/read")
def mark_instruction_read(instruction_id: int, db: Session = Depends(get_db)):
    """
    标记指令为已读（进行中）

    POST /api/instructions/123/read
    """
    try:
        from analysis import IntelligentCommander

        commander = IntelligentCommander(db)
        commander.mark_instruction_read(instruction_id)

        return {"success": True, "message": "指令已标记为进行中"}
    except Exception as e:
        return {"error": str(e), "success": False}


@router.post("/{instruction_id}/done")
def mark_instruction_done(
    instruction_id: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    标记指令为完成

    POST /api/instructions/123/done
    Body: { "feedback": "已完成调整" }
    """
    try:
        from analysis import IntelligentCommander

        commander = IntelligentCommander(db)
        commander.mark_instruction_done(instruction_id, feedback or "")

        return {"success": True, "message": "指令已完成"}
    except Exception as e:
        return {"error": str(e), "success": False}


@router.post("/generate-today")
def generate_today_instructions(db: Session = Depends(get_db)):
    """
    生成今日工艺指令（演示用）

    POST /api/instructions/generate-today
    """
    try:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        # 检查是否已有今日指令
        existing = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today
        ).all()

        if existing:
            # 删除旧指令
            for inst in existing:
                db.delete(inst)
            db.commit()

        # 生成示例指令
        instructions_data = [
            {
                "target_date": today,
                "role": "Operator",
                "content": "检测到E04 醇提罐温度异常（当前85.5℃），建议将蒸汽阀开度从50%调至45%",
                "priority": "HIGH",
                "evidence": {"current_value": 85.5, "target_value": 82.0, "cpk": 0.85},
                "action_code": "ADJUST_TEMP",
                "batch_id": "BATCH-001",
                "node_code": "E04",
                "param_code": "temp",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "QA",
                "content": "E04 醇提罐温度Cpk=0.85低于临界值1.33，请对批次BATCH-001启动偏差调查流程",
                "priority": "HIGH",
                "evidence": {"cpk": 0.85, "threshold": 1.33},
                "action_code": "DEV_INVESTIGATION",
                "batch_id": "BATCH-001",
                "node_code": "E04",
                "param_code": "temp",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "Operator",
                "content": "C01 混合机液位偏低（当前35%），请检查进料阀是否正常",
                "priority": "MEDIUM",
                "evidence": {"current_value": 35, "threshold": 40},
                "action_code": "CHECK_LEVEL",
                "batch_id": "BATCH-002",
                "node_code": "C01",
                "param_code": "level",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "TeamLeader",
                "content": "E03 投料站即将到清洁周期（已运行23小时），请安排清洁计划",
                "priority": "LOW",
                "evidence": {"run_hours": 23, "max_hours": 24},
                "action_code": "SCHEDULE_CLEAN",
                "batch_id": None,
                "node_code": "E03",
                "param_code": None,
                "status": "Pending"
            }
        ]

        # 保存到数据库
        for inst_data in instructions_data:
            record = models.DailyInstruction(**inst_data)
            db.add(record)

        db.commit()

        return {
            "success": True,
            "message": f"已生成 {len(instructions_data)} 条今日工艺指令",
            "count": len(instructions_data),
            "date": today
        }
    except Exception as e:
        return {"error": str(e), "success": False}
