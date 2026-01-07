"""生成Demo演示用的DailyInstruction数据

运行此脚本后，操作工报告将能看到真实的指令数据
"""

from datetime import datetime, timedelta
from database import SessionLocal
import models

def generate_demo_instructions():
    """生成演示用的DailyInstruction数据"""

    db = SessionLocal()

    try:
        # 清空现有指令
        db.query(models.DailyInstruction).delete()
        db.commit()

        # 生成不同角色的指令
        instructions_data = [
            # 操作工指令
            {
                "role": "Operator",
                "priority": "HIGH",
                "status": "Pending",
                "content": "E04醇提罐今日温度出现异常波动，请检查加热系统并记录温度数据",
                "instruction_date": datetime.now(),
                "target_date": datetime.now().strftime("%Y-%m-%d"),
                "node_code": "E04"
            },
            {
                "role": "Operator",
                "priority": "MEDIUM",
                "status": "Pending",
                "content": "C01浓缩罐液位偏低，请调整进料流量至目标范围",
                "instruction_date": datetime.now() - timedelta(hours=2),
                "target_date": datetime.now().strftime("%Y-%m-%d"),
                "node_code": "C01"
            },
            {
                "role": "Operator",
                "priority": "LOW",
                "status": "Pending",
                "content": "定期清洁提醒：E03提取罐需要进行本周清洁验证",
                "instruction_date": datetime.now() - timedelta(hours=4),
                "target_date": datetime.now().strftime("%Y-%m-%d"),
                "node_code": "E03"
            },

            # 经理/厂长指令
            {
                "role": "Manager",
                "priority": "HIGH",
                "status": "Pending",
                "content": "本周Cpk指标未达标，需要召开质量分析会",
                "instruction_date": datetime.now() - timedelta(days=1),
                "target_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            },
            {
                "role": "Manager",
                "priority": "MEDIUM",
                "status": "Pending",
                "content": "设备E04故障率上升，建议安排预防性维护",
                "instruction_date": datetime.now() - timedelta(days=2),
                "target_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "node_code": "E04"
            },

            # QA指令
            {
                "role": "QA",
                "priority": "HIGH",
                "status": "Pending",
                "content": "批料B20250103皂苷含量检测不合格，需要重新取样",
                "instruction_date": datetime.now() - timedelta(hours=6),
                "target_date": datetime.now().strftime("%Y-%m-%d"),
                "batch_id": "B20250103"
            },
            {
                "role": "QA",
                "priority": "MEDIUM",
                "status": "Pending",
                "content": "验证清洁程序的有效性，完成微生物限度检测",
                "instruction_date": datetime.now() - timedelta(hours=12),
                "target_date": datetime.now().strftime("%Y-%m-%d")
            },

            # 班长指令
            {
                "role": "TeamLeader",
                "priority": "HIGH",
                "status": "Pending",
                "content": "班组人员培训：新SOP操作流程学习",
                "instruction_date": datetime.now() - timedelta(days=1),
                "target_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            },
            {
                "role": "TeamLeader",
                "priority": "MEDIUM",
                "status": "Pending",
                "content": "排班调整：下周夜班人员安排确认",
                "instruction_date": datetime.now() - timedelta(days=3),
                "target_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            }
        ]

        # 批量创建指令
        instructions = []
        for data in instructions_data:
            inst = models.DailyInstruction(**data)
            instructions.append(inst)

        db.add_all(instructions)
        db.commit()

        print(f"✅ 成功生成 {len(instructions)} 条演示指令")
        print(f"   - Operator: {sum(1 for i in instructions if i.role == 'Operator')} 条")
        print(f"   - Manager: {sum(1 for i in instructions if i.role == 'Manager')} 条")
        print(f"   - QA: {sum(1 for i in instructions if i.role == 'QA')} 条")
        print(f"   - TeamLeader: {sum(1 for i in instructions if i.role == 'TeamLeader')} 条")

        return True

    except Exception as e:
        print(f"❌ 生成指令失败: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    print("开始生成Demo指令数据...")
    generate_demo_instructions()
    print("完成!")
