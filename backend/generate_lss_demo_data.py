"""生成完整的LSS Demo测试数据

生成多车间的工艺参数测量数据，用于演示LSS工具箱。
"""

from datetime import datetime, timedelta
import random
import numpy as np
from database import SessionLocal
import models


def generate_measurement_data():
    """生成多车间测量数据"""

    db = SessionLocal()

    try:
        # 清空现有数据
        db.query(models.Measurement).delete()
        db.query(models.Batch).delete()
        db.commit()

        # 定义车间设备配置
        # 基于seed.py中的节点结构
        nodes_config = {
            # 提取车间 - E系列（醇提罐）
            "E01": {
                "name": "E01醇提罐",
                "params": {
                    "P_E01_TEMP": {"name": "提取温度", "unit": "℃", "target": 85.0, "usl": 90.0, "lsl": 80.0, "std": 1.5},
                    "P_E01_PRESSURE": {"name": "提取压力", "unit": "MPa", "target": 2.0, "usl": 2.5, "lsl": 1.5, "std": 0.15},
                    "P_E01_TIME": {"name": "提取时间", "unit": "min", "target": 120.0, "usl": 130.0, "lsl": 110.0, "std": 5.0},
                }
            },
            "E02": {
                "name": "E02醇提罐",
                "params": {
                    "P_E02_TEMP": {"name": "提取温度", "unit": "℃", "target": 85.0, "usl": 90.0, "lsl": 80.0, "std": 1.2},
                    "P_E02_PRESSURE": {"name": "提取压力", "unit": "MPa", "target": 2.0, "usl": 2.5, "lsl": 1.5, "std": 0.12},
                }
            },
            "E03": {
                "name": "E03醇提罐",
                "params": {
                    "P_E03_TEMP": {"name": "提取温度", "unit": "℃", "target": 85.0, "usl": 90.0, "lsl": 80.0, "std": 2.0},  # 波动较大
                    "P_E03_PH": {"name": "pH值", "unit": "", "target": 7.0, "usl": 8.0, "lsl": 6.0, "std": 0.3},
                }
            },
            "E04": {
                "name": "E04醇提罐",
                "params": {
                    "P_E04_TEMP": {"name": "提取温度", "unit": "℃", "target": 85.0, "usl": 90.0, "lsl": 80.0, "std": 1.8},
                    "P_E04_FLOW": {"name": "溶剂流量", "unit": "L/h", "target": 500.0, "usl": 550.0, "lsl": 450.0, "std": 25.0},
                }
            },

            # 浓缩车间 - C系列（浓缩罐）
            "C01": {
                "name": "C01浓缩罐",
                "params": {
                    "P_C01_TEMP": {"name": "浓缩温度", "unit": "℃", "target": 65.0, "usl": 70.0, "lsl": 60.0, "std": 2.0},
                    "P_C01_VACUUM": {"name": "真空度", "unit": "MPa", "target": 0.08, "usl": 0.085, "lsl": 0.075, "std": 0.003},
                    "P_C01_DENSITY": {"name": "浓缩液密度", "unit": "g/mL", "target": 1.15, "usl": 1.18, "lsl": 1.12, "std": 0.02},
                }
            },
            "C02": {
                "name": "C02浓缩罐",
                "params": {
                    "P_C02_TEMP": {"name": "浓缩温度", "unit": "℃", "target": 65.0, "usl": 70.0, "lsl": 60.0, "std": 1.5},
                    "P_C02_VACUUM": {"name": "真空度", "unit": "MPa", "target": 0.08, "usl": 0.085, "lsl": 0.075, "std": 0.002},
                }
            },
        }

        # 生成批料
        batches = []
        base_date = datetime.now() - timedelta(days=14)  # 最近14天

        for i in range(20):  # 20个批料
            batch_date = base_date + timedelta(days=i * 0.7)
            batch_id = f"B2025{batch_date.strftime('%m%d')}{i:02d}"

            batch = models.Batch(
                id=batch_id,
                product_name="皂苷提取物",
                start_time=batch_date,
                status="Completed"
            )
            batches.append(batch)

        db.add_all(batches)
        db.commit()

        # 为每个节点和参数生成测量数据
        measurements = []
        measurement_count = 0
        base_time = datetime.now() - timedelta(days=14)

        for node_code, node_config in nodes_config.items():
            for param_code, param_config in node_config["params"].items():
                # 每个参数生成30-50个测量点
                n_samples = random.randint(30, 50)

                for i in range(n_samples):
                    # 生成测量时间（14天内均匀分布）
                    offset_minutes = random.randint(0, 14 * 24 * 60)
                    measure_time = base_time + timedelta(minutes=offset_minutes)

                    # 生成测量值（正态分布，target为中心，std为标准差）
                    target = param_config["target"]
                    std = param_config["std"]

                    # 5%的概率生成异常值（超规格）
                    if random.random() < 0.05:
                        # 超规格值
                        if random.random() < 0.5:
                            value = target + random.uniform(std * 2, std * 4)  # 超上限
                        else:
                            value = target - random.uniform(std * 2, std * 4)  # 超下限
                    else:
                        # 正常值
                        value = random.gauss(target, std)

                    # 10%的概率生成批次异常（均值偏移）
                    if random.random() < 0.10:
                        value += random.choice([-1, 1]) * random.uniform(std * 0.5, std * 1.5)

                    # 关联随机批料
                    batch_id = random.choice(batches).id

                    measurement = models.Measurement(
                        node_code=node_code,
                        param_code=param_code,
                        value=round(value, 2),
                        timestamp=measure_time,
                        batch_id=batch_id,
                        source_type="SIMULATION"
                    )
                    measurements.append(measurement)
                    measurement_count += 1

                    # 每100条commit一次，避免内存占用
                    if len(measurements) >= 100:
                        db.add_all(measurements)
                        db.commit()
                        measurements = []

        # 提交剩余数据
        if measurements:
            db.add_all(measurements)
            db.commit()

        print(f"✅ 成功生成 {measurement_count} 条测量数据")
        print(f"   - 车间设备: {len(nodes_config)} 个")
        print(f"   - 参数种类: {sum(len(n['params']) for n in nodes_config.values())} 个")
        print(f"   - 批料数量: {len(batches)} 个")
        print(f"   - 时间跨度: 14天")

        # 生成帕累托图用的类别数据（故障统计）
        fault_categories = [
            {"category": "温度异常", "count": 45},
            {"category": "压力异常", "count": 28},
            {"category": "液位异常", "count": 22},
            {"category": "流量异常", "count": 18},
            {"category": "pH值异常", "count": 15},
            {"category": "真空度异常", "count": 12},
            {"category": "密度异常", "count": 10},
            {"category": "设备故障", "count": 8},
            {"category": "人为误差", "count": 6},
            {"category": "其他原因", "count": 5},
        ]

        print(f"\n📊 故障类别统计（用于帕累托图）:")
        total = sum(item["count"] for item in fault_categories)
        for item in sorted(fault_categories, key=lambda x: x["count"], reverse=True):
            pct = item["count"] / total * 100
            print(f"   - {item['category']}: {item['count']}次 ({pct:.1f}%)")

        return True

    except Exception as e:
        print(f"❌ 生成数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("开始生成LSS Demo测试数据...")
    generate_measurement_data()
    print("完成!")
