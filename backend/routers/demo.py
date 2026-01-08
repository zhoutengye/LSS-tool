"""演示数据管理API路由

提供演示环境的数据管理、重置和工人填报接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/api/demo", tags=["演示管理"])


@router.delete("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    重置演示环境（回到初始状态）

    DELETE /api/demo/reset

    清空内容：
    - 工人填报的测量记录（保留初始演示数据）
    - 工人填报的批次记录（保留 BATCH-DEMO-001）
    - 生成的指令（保留初始示例指令）

    保留内容：
    - ProcessNode (流程节点)
    - ProcessEdge (流向)
    - ParameterDef (参数定义)
    - RiskNode/RiskEdge (风险图谱)
    - ActionDef (对策库)
    - 初始演示数据（700条历史测量 + 4条示例指令）
    """
    try:
        from initial_data.demo_init import init_demo_data
        import os

        # 清空工人新增的动态数据（但保留初始演示数据）
        # 删除非 BATCH-DEMO-001 的批次
        db.query(models.Batch).filter(
            models.Batch.id != "BATCH-DEMO-001"
        ).delete()

        # 删除 BATCH-DEMO-001 以外的测量记录（保留初始700条）
        db.query(models.Measurement).filter(
            models.Measurement.batch_id != "BATCH-DEMO-001"
        ).delete()

        # 删除今日以外的指令（保留初始示例指令）
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date != today
        ).delete()

        # 清空今日的指令（会由 init_demo_data 重新生成）
        db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today
        ).delete()

        db.commit()

        # 重新初始化演示数据（恢复到初始状态）
        db_path = os.path.join(os.path.dirname(__file__), "..", "lss.db")
        init_demo_data(db_path)

        return {
            "success": True,
            "message": "✅ 演示环境已重置：已恢复到初始演示状态，工人填报数据已清空。"
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@router.post("/init-actions")
def init_action_definitions(db: Session = Depends(get_db)):
    """
    初始化对策库数据（演示用）

    POST /api/demo/init-actions

    从 initial_data/actions.csv 加载对策定义到数据库。
    """
    try:
        import csv
        import os

        # 检查是否已有数据
        existing_count = db.query(models.ActionDef).count()
        if existing_count > 0:
            return {
                "success": True,
                "message": f"对策库已存在 {existing_count} 条记录，无需初始化。",
                "count": existing_count
            }

        # 读取 actions.csv
        actions_csv = os.path.join(
            os.path.dirname(__file__),
            "..",
            "initial_data",
            "actions.csv"
        )

        if not os.path.exists(actions_csv):
            return {
                "success": False,
                "error": f"文件不存在: {actions_csv}"
            }

        with open(actions_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actions_data = list(reader)

        # 插入数据
        for row in actions_data:
            active_str = row.get('active', 'true')
            action = models.ActionDef(
                code=row['code'],
                name=row['name'],
                risk_code=row['risk_code'],
                target_role=row['target_role'],
                instruction_template=row['instruction_template'],
                priority=row['priority'],
                category=row['category'],
                estimated_impact=row.get('estimated_impact', ''),
                active=active_str.lower() == 'true' if active_str else True
            )
            db.add(action)

        db.commit()

        return {
            "success": True,
            "message": f"✅ 已初始化 {len(actions_data)} 条对策定义",
            "count": len(actions_data)
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@router.post("/shift-report")
def submit_shift_report(data: dict, db: Session = Depends(get_db)):
    """
    下工填报单（工人填写生产数据）

    POST /api/demo/shift-report
    {
        "batch_id": "WX-20231026",
        "worker_id": "WORKER_007",
        "shift_end_time": "2023-10-26T17:00:00",
        "data": [
            {
                "node_code": "E04",
                "param_code": "temp",
                "value": 98.5,
                "unit": "℃"
            },
            {
                "node_code": "E04",
                "param_code": "pressure",
                "value": 2.5,
                "unit": "MPa"
            },
            {
                "node_code": "E04",
                "param_code": "motor_status",
                "value": "abnormal",
                "unit": "status"
            }
        ]
    }
    """
    try:
        from datetime import datetime

        batch_id_input = data.get("batch_id")

        # 创建或获取批次记录（注意：Batch模型的主键是id，不是batch_id）
        batch = db.query(models.Batch).filter(
            models.Batch.id == batch_id_input
        ).first()

        if not batch:
            batch = models.Batch(
                id=batch_id_input,  # 使用id字段
                product_name="稳心颗粒",
                start_time=datetime.now(),
                status="In Progress"
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

        # 插入测量数据
        measurements = []
        for item in data.get("data", []):
            param_code = item.get("param_code")
            node_code = item.get("node_code")
            raw_value = item["value"]

            # 转换参数代码为全大写P前缀格式: temp -> P_E04_TEMP
            if param_code != "motor_status":  # motor_status保持原样
                param_code = f"P_{node_code}_{param_code.upper()}"

            # 根据参数类型处理值
            # 注意：Measurement.value 字段是 Float 类型，不能存储字符串
            if param_code == "motor_status":
                # 将设备状态转换为数值代码：normal=1.0, abnormal=0.0
                if isinstance(raw_value, str):
                    processed_value = 1.0 if raw_value.lower() == "normal" else 0.0
                else:
                    processed_value = float(raw_value)
            else:
                # 数值型参数转换为float
                processed_value = float(raw_value) if isinstance(raw_value, (int, float, str)) else 0

            record = models.Measurement(
                batch_id=batch.id,  # 外键关联
                node_code=node_code,
                param_code=param_code,
                value=processed_value,
                source_type="SENSOR",  # 标记为传感器数据
                timestamp=datetime.now()
            )
            db.add(record)
            measurements.append(record)

        db.commit()

        # 触发智能分析（模拟夜间批处理）
        from analysis import IntelligentCommander
        commander = IntelligentCommander(db)

        # 生成指令
        print(f"🔍 开始分析 {len(measurements)} 条测量数据...")
        for meas in measurements:
            print(f"  - {meas.node_code}.{meas.param_code} = {meas.value}")

        instructions_generated = commander.generate_instructions_from_data(
            batch_id=batch.id,  # 使用batch.id
            measurements=measurements
        )

        print(f"✅ 分析完成，生成了 {len(instructions_generated)} 条指令")

        return {
            "success": True,
            "message": f"已提交 {len(measurements)} 条数据，生成 {len(instructions_generated)} 条指令",
            "batch_id": batch.id,
            "data_count": len(measurements),
            "instructions_count": len(instructions_generated)
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@router.post("/login")
def worker_login(data: dict, db: Session = Depends(get_db)):
    """
    工人上工登录（刷卡）

    POST /api/demo/login
    {
        "worker_id": "WORKER_007"
    }
    """
    try:
        from datetime import datetime

        worker_id = data.get("worker_id")
        today = datetime.now().strftime("%Y-%m-%d")

        # 查询今日指派给该工人的指令
        instructions = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today,
            models.DailyInstruction.role.in_(["Operator", worker_id])
        ).order_by(
            models.DailyInstruction.priority.desc(),  # HIGH > MEDIUM > LOW
            models.DailyInstruction.id
        ).all()

        # 查询系统状态概览
        total_pending = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today,
            models.DailyInstruction.status == "Pending"
        ).count()

        return {
            "success": True,
            "worker_id": worker_id,
            "worker_name": f"操作工 {worker_id}",
            "login_time": datetime.now().isoformat(),
            "briefing": {
                "total_instructions": len(instructions),
                "pending_count": total_pending,
                "instructions": [
                    {
                        "id": inst.id,
                        "priority": inst.priority,
                        "content": inst.content,
                        "node_code": inst.node_code,
                        "batch_id": inst.batch_id,
                        "evidence": inst.evidence
                    }
                    for inst in instructions
                ]
            }
        }
    except Exception as e:
        return {"error": str(e), "success": False}
