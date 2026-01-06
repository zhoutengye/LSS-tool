"""演示智能工艺指挥官的完整流程

模拟PPT场景：
- 前一天 22:00：数据分析
- 次日 06:00：推送指令
"""

import sys
sys.path.insert(0, '.')

from database import SessionLocal
from analysis import IntelligentCommander
import models


def demo_instruction_generation():
    """演示指令生成流程"""

    db = SessionLocal()
    commander = IntelligentCommander(db)

    print("=" * 70)
    print("🌅 场景：前一天 22:00 - 自动分析生产数据")
    print("=" * 70)

    # 模拟：假设分析发现 E04 温度异常
    print("\n📊 [数据分析] 发现异常：")
    print("  - 批次: BATCH-001")
    print("  - 工序: E04 醇提罐")
    print("  - 参数: 醇提温度")
    print("  - 问题: Cpk = 0.85 (低于临界值 1.33)")
    print("  - 根因: 蒸汽阀卡滞 (概率 80%)")

    # 模拟：生成指令
    print("\n🎯 [对策匹配] 查询对策库...")
    actions = db.query(models.ActionDef).filter(
        models.ActionDef.risk_code == "R_E04_TEMP_HIGH",
        models.ActionDef.active == True
    ).all()

    print(f"  找到 {len(actions)} 条相关对策：")
    for action in actions:
        print(f"  - [{action.target_role}] {action.name}")

    # 模拟：生成自然语言指令
    print("\n✍️  [指令生成] 填充模板...")
    instructions = []

    for action in actions:
        # 模拟模板变量
        template_vars = {
            "node_name": "E04 醇提罐",
            "current_value": 85.5,
            "target_value": 82.0,
            "batch_id": "BATCH-001",
            "cpk": 0.85,
            "current_valve": 50,
            "suggested_valve": 45,
            "root_cause": "蒸汽阀卡滞",
            "prob": 80
        }

        content = action.instruction_template.format(**template_vars)

        # 保存到数据库
        record = models.DailyInstruction(
            target_date="2023-10-25",
            role=action.target_role,
            content=content,
            priority=action.priority,
            evidence=template_vars,
            action_code=action.code,
            batch_id="BATCH-001",
            node_code="E04",
            param_code="temp",
            status="Pending"
        )
        db.add(record)
        instructions.append((action.target_role, content))

    db.commit()

    print("\n✅ 已生成并保存指令：")
    for role, content in instructions:
        print(f"\n【{role}】")
        print(f"  {content}")

    return instructions


def demo_instruction_push():
    """演示次日清晨推送"""

    print("\n\n" + "=" * 70)
    print("🌅 场景：次日 06:00 - 自动推送到各角色终端")
    print("=" * 70)

    db = SessionLocal()

    # 查询所有待推送指令
    all_instructions = db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == "2023-10-25",
        models.DailyInstruction.status == "Pending"
    ).all()

    print(f"\n📱 正在推送 {len(all_instructions)} 条指令...\n")

    # 按角色分组
    role_groups = {}
    for inst in all_instructions:
        if inst.role not in role_groups:
            role_groups[inst.role] = []
        role_groups[inst.role].append(inst)

    # 模拟推送到不同终端
    terminals = {
        "Operator": "🖥️  操作工工位终端",
        "QA": "💻  QA 质量管理系统",
        "TeamLeader": "📊 班长数字大屏",
        "Manager": "📱 经理手机APP"
    }

    for role, instructions in role_groups.items():
        terminal = terminals.get(role, "未知终端")
        print(f"{terminal} 【{role}】收到 {len(instructions)} 条指令：")
        print("-" * 70)

        for i, inst in enumerate(instructions, 1):
            print(f"{i}. [{inst.priority}] {inst.content}")

        print()

        # 标记为已推送
        for inst in instructions:
            inst.status = "Read"
            inst.sent_at = models.datetime.datetime.now()

    db.commit()

    print("✅ 推送完成！")


def demo_instruction_execution():
    """演示指令执行和反馈"""

    print("\n\n" + "=" * 70)
    print("🔄 场景：操作工执行指令并反馈")
    print("=" * 70)

    db = SessionLocal()

    # 获取一条操作工的指令
    inst = db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == "2023-10-25",
        models.DailyInstruction.role == "Operator"
    ).first()

    if inst:
        print(f"\n📌 指令内容：{inst.content}")
        print(f"   状态：{inst.status}")

        print("\n👷 操作工行动：")
        print("  1. 阅读指令 (09:00)")
        inst.read_at = models.datetime.datetime.now()

        print("  2. 执行调整：将蒸汽阀开度从 50% 调至 45%")
        print("  3. 观察效果：温度稳定在 82.0℃")

        print("\n✅ 操作工反馈：")
        feedback = "已调整蒸汽阀开度，温度已恢复正常"
        inst.feedback = feedback
        inst.status = "Done"
        inst.done_at = models.datetime.datetime.now()

        db.commit()

        print(f"  \"{feedback}\"")
        print(f"\n📊 指令状态更新：{inst.status}")
        print(f"   执行时间：{inst.done_at}")


if __name__ == "__main__":
    # 完整流程演示
    demo_instruction_generation()
    demo_instruction_push()
    demo_instruction_execution()

    print("\n\n" + "=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)
    print("""
这就是 PPT 中的核心流程：

  前一天 22:00
     ↓
  [数据引擎] 自动拉取生产数据
     ↓
  [智能编排器] SPC分析 → 故障树追溯 → 风险评估
     ↓
  [角色指令生成器] 匹配对策库 → 填充模板 → 生成指令
     ↓
  次日 06:00
     ↓
  [推送服务] 按角色推送到不同终端
     ↓
  [执行追踪] Pending → Read → Done + 反馈

💡 核心价值：不是生成报告，而是推送任务！
    """)
