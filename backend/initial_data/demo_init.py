"""
演示数据初始化脚本

系统启动时自动调用，创建完整的演示环境：
- 历史测量数据（用于LSS工具箱分析）
- 今日工艺指令示例
"""
import os
import sys
import csv
from datetime import datetime, timedelta
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models


def init_demo_data(db_path: str = "lss.db"):
    """
    初始化演示数据
    """
    # 创建数据库连接
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("🚀 开始初始化演示数据...")

    # ========================================
    # 1. 检查测量数据是否已初始化
    # ========================================
    existing_measurements = db.query(models.Measurement).count()
    skip_measurements = False
    if existing_measurements > 100:
        print(f"✅ 测量数据已存在（{existing_measurements} 条记录），跳过创建")
        skip_measurements = True

    # ========================================
    # 2. 创建历史测量数据（过去7天）
    # ========================================
    if not skip_measurements:
        print("📊 创建历史测量数据...")

    nodes = ["E01", "E02", "E03", "E04", "P01", "P02", "C01", "C02"]
    params = ["temp", "pressure", "moisture", "time", "level"]

    # 创建一个批次
    batch = models.Batch(
        id=f"BATCH-DEMO-001",
        product_name="稳心颗粒",
        start_time=datetime.now() - timedelta(days=7),
        status="Completed"
    )
    if not skip_measurements:
        db.add(batch)

    # 生成过去7天的数据（每天100条，共700条）
    if not skip_measurements:
        base_time = datetime.now() - timedelta(days=7)

        for day in range(7):
            for i in range(100):
                timestamp = base_time + timedelta(days=day, hours=i * 0.24)  # 每15分钟一条

                # 随机选择节点和参数
                node = random.choice(nodes)
                param = random.choice(params)

                # 根据参数类型生成值
                if param == "temp":
                    # 温度：80-85之间，偶尔异常
                    if random.random() < 0.1:  # 10%概率异常
                        value = random.uniform(85, 92)
                    else:
                        value = random.uniform(80, 84)
                elif param == "pressure":
                    # 压力：1.0-2.0 MPa
                    if random.random() < 0.1:
                        value = random.uniform(2.0, 2.5)
                    else:
                        value = random.uniform(1.0, 1.8)
                elif param == "moisture":
                    # 水分：2-5%
                    if random.random() < 0.05:
                        value = random.uniform(5, 6)
                    else:
                        value = random.uniform(2, 4)
                elif param == "time":
                    # 时间：30-60分钟
                    value = random.uniform(30, 60)
                else:  # level
                    # 液位：20-80%
                    value = random.uniform(20, 80)

                meas = models.Measurement(
                    batch_id=batch.id,
                    node_code=node,
                    param_code=f"P_{node}_{param.upper()}",  # 使用P前缀格式: P_E04_TEMP
                    value=round(value, 2),
                    source_type="HISTORY",
                    timestamp=timestamp
                )
                db.add(meas)

        db.commit()
        print(f"✅ 已创建 {700} 条历史测量数据")
    else:
        print("⏭️  跳过创建历史测量数据")

    # ========================================
    # 3. 生成今日工艺指令
    # ========================================
    print("📋 创建今日工艺指令...")

    today = datetime.now().strftime("%Y-%m-%d")

    # 清空今日已有指令
    db.query(models.DailyInstruction).filter(
        models.DailyInstruction.target_date == today
    ).delete()

    # 创建今日指令
    instructions = [
        models.DailyInstruction(
            target_date=today,
            role="Operator",
            content="检测到E04 醇提罐温度异常（当前85.5℃），建议将蒸汽阀开度从50%调至45%",
            priority="HIGH",
            evidence={"current_value": 85.5, "target_value": 82.0, "cpk": 0.85},
            action_code="ADJUST_TEMP",
            batch_id="BATCH-DEMO-001",
            node_code="E04",
            param_code="temp",
            status="Pending"
        ),
        models.DailyInstruction(
            target_date=today,
            role="QA",
            content="E04 醇提罐温度Cpk=0.85低于临界值1.33，请对批次BATCH-DEMO-001启动偏差调查流程",
            priority="HIGH",
            evidence={"cpk": 0.85, "threshold": 1.33},
            action_code="DEV_INVESTIGATION",
            batch_id="BATCH-DEMO-001",
            node_code="E04",
            param_code="temp",
            status="Pending"
        ),
        models.DailyInstruction(
            target_date=today,
            role="Operator",
            content="C01 混合机液位偏低（当前35%），请检查进料阀是否正常",
            priority="MEDIUM",
            evidence={"current_value": 35, "threshold": 40},
            action_code="CHECK_LEVEL",
            batch_id="BATCH-DEMO-001",
            node_code="C01",
            param_code="level",
            status="Pending"
        ),
        models.DailyInstruction(
            target_date=today,
            role="TeamLeader",
            content="E03 投料站即将到清洁周期（已运行23小时），请安排清洁计划",
            priority="LOW",
            evidence={"run_hours": 23, "max_hours": 24},
            action_code="SCHEDULE_CLEAN",
            batch_id=None,
            node_code="E03",
            param_code=None,
            status="Pending"
        )
    ]

    for inst in instructions:
        db.add(inst)

    db.commit()
    print(f"✅ 已创建 {len(instructions)} 条今日工艺指令")

    # ========================================
    # 4. 初始化参数定义（如果没有）
    # ========================================
    param_count = db.query(models.ParameterDef).count()
    if param_count == 0:
        print("📐 初始化参数定义...")

        # 为每个节点创建参数定义
        param_definitions = [
            # E04 醇提罐参数
            {"code": "P_E04_TEMP", "name": "E04醇提罐温度", "unit": "℃", "usl": 90.0, "lsl": 75.0, "target": 82.0},
            {"code": "P_E04_PRESSURE", "name": "E04醇提罐压力", "unit": "MPa", "usl": 2.5, "lsl": 0.8, "target": 1.5},
            {"code": "P_E04_TIME", "name": "E04醇提罐时间", "unit": "min", "usl": 70.0, "lsl": 30.0, "target": 50.0},
            {"code": "P_E04_LEVEL", "name": "E04醇提罐液位", "unit": "%", "usl": 90.0, "lsl": 20.0, "target": 60.0},
            {"code": "P_E04_MOISTURE", "name": "E04醇提罐水分", "unit": "%", "usl": 5.0, "lsl": 1.0, "target": 3.0},

            # E01-E03 其他提取罐
            {"code": "P_E01_TEMP", "name": "E01提取罐温度", "unit": "℃", "usl": 90.0, "lsl": 75.0, "target": 82.0},
            {"code": "P_E01_PRESSURE", "name": "E01提取罐压力", "unit": "MPa", "usl": 2.5, "lsl": 0.8, "target": 1.5},
            {"code": "P_E02_TEMP", "name": "E02提取罐温度", "unit": "℃", "usl": 90.0, "lsl": 75.0, "target": 82.0},
            {"code": "P_E03_TEMP", "name": "E03提取罐温度", "unit": "℃", "usl": 90.0, "lsl": 75.0, "target": 82.0},

            # P01-P02 压制设备
            {"code": "P_P01_MOISTURE", "name": "P01压制机水分", "unit": "%", "usl": 5.0, "lsl": 1.0, "target": 3.0},
            {"code": "P_P01_PRESSURE", "name": "P01压制机压力", "unit": "MPa", "usl": 25.0, "lsl": 15.0, "target": 20.0},
            {"code": "P_P01_TIME", "name": "P01压制机时间", "unit": "s", "usl": 10.0, "lsl": 5.0, "target": 7.5},
            {"code": "P_P02_MOISTURE", "name": "P02压制机水分", "unit": "%", "usl": 5.0, "lsl": 1.0, "target": 3.0},

            # C01-C02 混合设备
            {"code": "P_C01_LEVEL", "name": "C01混合机液位", "unit": "%", "usl": 90.0, "lsl": 20.0, "target": 60.0},
            {"code": "P_C01_TEMP", "name": "C01混合机温度", "unit": "℃", "usl": 50.0, "lsl": 20.0, "target": 35.0},
            {"code": "P_C02_LEVEL", "name": "C02混合机液位", "unit": "%", "usl": 90.0, "lsl": 20.0, "target": 60.0},
        ]

        for param_def in param_definitions:
            param = models.ParameterDef(**param_def)
            db.add(param)

        db.commit()
        print(f"✅ 已初始化 {len(param_definitions)} 条参数定义")

    # ========================================
    # 5. 初始化对策库（如果没有）
    # ========================================
    action_count = db.query(models.ActionDef).count()
    if action_count == 0:
        print("📚 初始化对策库...")

        actions_csv = os.path.join(
            os.path.dirname(__file__),
            "actions.csv"
        )

        if os.path.exists(actions_csv):
            with open(actions_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                actions_data = list(reader)

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
            print(f"✅ 已初始化 {len(actions_data)} 条对策定义")

    # ========================================
    # 6. 初始化工艺流程图（如果没有）
    # ========================================
    process_node_count = db.query(models.ProcessNode).count()
    if process_node_count == 0:
        print("🏗️ 初始化工艺流程图...")

        # 导入seed函数
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seed_path = os.path.join(backend_dir, 'seed.py')

        if os.path.exists(seed_path):
            # 动态导入seed模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("seed", seed_path)
            seed_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(seed_module)

            # 调用seed_hierarchical函数
            seed_module.seed_hierarchical()
            print("✅ 工艺流程图初始化完成")

    db.close()
    print("\n🎉 演示数据初始化完成！")
    print("   - 700条历史测量数据")
    print("   - 4条今日工艺指令")
    print("   - 17条参数定义")
    print("   - 11条对策定义")
    print("   - 工艺流程图")


if __name__ == "__main__":
    init_demo_data()
