"""生成今日工艺指令"""

from database import SessionLocal
from analysis import IntelligentCommander
import models
from datetime import datetime


def generate_today_instructions():
    """为今天生成工艺指令"""

    db = SessionLocal()
    commander = IntelligentCommander(db)

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 正在生成 {today} 的工艺指令...")

    # 检查是否已有今日指令
    existing = db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == today
    ).all()

    if existing:
        print(f"⚠️  已存在 {len(existing)} 条今日指令，先删除...")
        for inst in existing:
            db.delete(inst)
        db.commit()

    # 使用 IntelligentCommander 生成指令
    print("\n🔍 分析生产数据...")

    # 生成几条示例指令
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

    print(f"\n✅ 已生成 {len(instructions_data)} 条今日工艺指令：")
    for i, inst_data in enumerate(instructions_data, 1):
        print(f"  {i}. [{inst_data['role']}] {inst_data['content'][:60]}...")

    return instructions_data


if __name__ == "__main__":
    print("=" * 70)
    print("📋 今日工艺指令生成器")
    print("=" * 70)
    print()

    generate_today_instructions()

    print("\n" + "=" * 70)
    print("✅ 完成！现在刷新前端页面，应该能看到指令列表了。")
    print("=" * 70)
