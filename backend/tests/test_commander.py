"""测试智能工艺指挥官

验证完整的"分析 → 对策匹配 → 指令生成 → 角色推送"流程。
"""

import sys
sys.path.insert(0, '..')

from database import SessionLocal
from analysis import IntelligentCommander
import models


def test_daily_order_generation():
    """测试每日指令生成（核心场景）"""

    db = SessionLocal()

    print("=" * 60)
    print("🚀 测试智能工艺指挥官")
    print("=" * 60)

    # 初始化指挥官
    commander = IntelligentCommander(db)

    # 生成今日指令
    today = "2023-10-25"  # 使用测试日期
    print(f"\n📅 正在分析 {today} 的生产数据...\n")

    role_orders = commander.generate_daily_orders(
        target_date=today,
        dimensions=["batch"]  # 先测试批次维度
    )

    # 显示各角色收到的指令
    print("=" * 60)
    print("📋 指令分发结果")
    print("=" * 60)

    for role, instructions in role_orders.items():
        if instructions:
            print(f"\n【{role}】收到 {len(instructions)} 条指令：")
            print("-" * 60)

            for i, inst in enumerate(instructions[:3], 1):  # 只显示前3条
                print(f"{i}. [{inst.priority}] {inst.content}")
                print(f"   证据: Cpk={inst.evidence.get('cpk', 'N/A')}")
                print()

    # 查询数据库中的指令
    print("=" * 60)
    print("💾 数据库中的指令记录")
    print("=" * 60)

    all_instructions = db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == today
    ).all()

    print(f"\n共保存 {len(all_instructions)} 条指令\n")

    for inst in all_instructions[:5]:  # 显示前5条
        print(f"📌 [{inst.role}] {inst.content[:50]}...")
        print(f"   状态: {inst.status} | 优先级: {inst.priority}")
        print()


def test_role_query():
    """测试按角色查询指令（前端接口）"""

    db = SessionLocal()
    commander = IntelligentCommander(db)

    print("=" * 60)
    print("🔍 测试角色查询接口")
    print("=" * 60)

    # 模拟操作工查询自己的指令
    target_date = "2023-10-25"

    for role in ["Operator", "QA", "TeamLeader", "Manager"]:
        instructions = commander.get_instructions_by_role(
            role=role,
            target_date=target_date,
            status="Pending"
        )

        print(f"\n【{role}】的待处理指令: {len(instructions)} 条")

        if instructions:
            for inst in instructions[:2]:
                print(f"  - {inst.content[:60]}...")


def test_instruction_lifecycle():
    """测试指令生命周期（Pending → Read → Done）"""

    db = SessionLocal()
    commander = IntelligentCommander(db)

    print("\n" + "=" * 60)
    print("🔄 测试指令生命周期")
    print("=" * 60)

    # 获取一条待处理指令
    inst = db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == "2023-10-25",
        models.DailyInstruction.role == "Operator",
        models.DailyInstruction.status == "Pending"
    ).first()

    if inst:
        print(f"\n📌 原始指令: {inst.content}")
        print(f"   状态: {inst.status}")

        # 标记为已读
        commander.mark_instruction_read(inst.id)
        print(f"\n✅ 已标记为已读")
        db.refresh(inst)
        print(f"   状态: {inst.status} | 阅读时间: {inst.read_at}")

        # 标记为完成
        commander.mark_instruction_done(inst.id, feedback="已调整蒸汽阀开度")
        print(f"\n✅ 已标记为完成")
        db.refresh(inst)
        print(f"   状态: {inst.status} | 完成时间: {inst.done_at}")
        print(f"   反馈: {inst.feedback}")


def demo_instruction_push():
    """演示次日清晨推送场景"""

    print("\n" + "=" * 60)
    print("🌅 演示：次日清晨 06:00 自动推送")
    print("=" * 60)

    print("""
    场景：
    ------------------------------------------------------
    前一天 22:00
      ↓
    [数据引擎] 自动拉取全天生产数据
      ↓
    [智能编排器] 运行黑带分析流程
      → SPC检测: "E04温度Cpk=0.85, 失控"
      → 故障树追溯: "根因80%是蒸汽阀卡滞"
      → 贝叶斯推演: "如不及时处理,明天报废率90%"
      ↓
    [角色指令生成器]
      → 操作工: "今天E04蒸汽阀开度初始值设为45%"
      → QA: "请对BATCH-20231001启动偏差调查"
      → 班长: "早会后安排维修工检查蒸汽阀密封圈"
      ↓
    次日 06:00 自动推送到对应角色手机/工位终端
    ------------------------------------------------------

    代码实现：
    ```python
    # 定时任务（每天 22:00 执行）
    commander = IntelligentCommander(db)
    role_orders = commander.generate_daily_orders("2023-10-25")

    # 定时任务（次日 06:00 执行）
    for role in ["Operator", "QA", "TeamLeader", "Manager"]:
        instructions = commander.get_instructions_by_role(role, "2023-10-25")
        push_to_terminal(instructions)  # 推送到工位终端
    ```
    """)


if __name__ == "__main__":
    # 运行测试
    test_daily_order_generation()
    test_role_query()
    test_instruction_lifecycle()
    demo_instruction_push()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
