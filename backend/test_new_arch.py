"""测试新架构：数据采集 + SPC 分析

这个脚本演示了完整的"数据漏斗"到"LSS工具箱"的流程。
"""

from database import SessionLocal
from ingestion import DataIngestor
from core.spc_tools import SPCToolbox
import models

def test_architecture():
    print("=" * 60)
    print("🧪 测试新架构：批次管理 + 数据采集 + SPC 分析")
    print("=" * 60)

    db = SessionLocal()
    ingestor = DataIngestor(db)

    # ============================================================
    # 步骤 1: 模拟数据采集 (会自动创建批次 BATCH_001)
    # ============================================================
    print("\n📊 步骤 1: 模拟采集 E04 醇提罐的温度数据...")

    temp_data = [85.0, 86.0, 85.5, 87.0, 85.8, 84.5, 86.2, 85.9]

    for i, temp in enumerate(temp_data):
        ingestor.ingest_single_point(
            batch_id="BATCH_001",
            node_code="E04",
            param_code="temp",
            value=temp,
            source="SIMULATION"
        )
        print(f"  [{i+1}] 写入温度: {temp}℃")

    # ============================================================
    # 步骤 2: 查询批次信息
    # ============================================================
    print("\n📦 步骤 2: 查询批次信息...")
    batch = db.query(models.Batch).filter(models.Batch.id == "BATCH_001").first()

    if batch:
        print(f"  批号: {batch.id}")
        print(f"  产品: {batch.product_name}")
        print(f"  状态: {batch.status}")
        print(f"  开始时间: {batch.start_time}")
        print(f"  测量数据条数: {len(batch.measurements)}")

    # ============================================================
    # 步骤 3: 查询特定参数的数据
    # ============================================================
    print("\n🔍 步骤 3: 查询 E04 温度数据...")
    measurements = ingestor.get_batch_measurements(
        batch_id="BATCH_001",
        node_code="E04",
        param_code="temp"
    )

    data_values = [m.value for m in measurements]
    print(f"  数据点数: {len(data_values)}")
    print(f"  数据: {[round(v, 1) for v in data_values]}")

    # ============================================================
    # 步骤 4: SPC 工具箱分析
    # ============================================================
    print("\n📈 步骤 4: SPC 过程能力分析...")

    # 从知识图谱中获取 temp 参数的规格 (假设 USL=90, LSL=75)
    usl = 90.0
    lsl = 75.0

    result = SPCToolbox.calculate_capability(data_values, usl, lsl)

    print(f"  平均值: {result['mean']}℃")
    print(f"  标准差: {result['std']}")
    print(f"  Cpk: {result['cpk']}")

    # 判断过程能力等级
    if result['cpk'] >= 2.0:
        grade = "优秀 (≥ 2.0)"
    elif result['cpk'] >= 1.67:
        grade = "良好 (≥ 1.67)"
    elif result['cpk'] >= 1.33:
        grade = "合格 (≥ 1.33)"
    else:
        grade = "需改进 (< 1.33)"

    print(f"  过程能力等级: {grade}")

    # ============================================================
    # 步骤 5: 报警判定
    # ============================================================
    print("\n🚨 步骤 5: 实时报警判定...")
    for temp in data_values:
        status = SPCToolbox.check_rules(temp, usl, lsl)
        status_emoji = "✅" if status == "NORMAL" else "⚠️"
        print(f"  {status_emoji} {temp}℃ -> {status}")

    # ============================================================
    # 步骤 6: 测试增量更新 (同一批次追加数据)
    # ============================================================
    print("\n➕ 步骤 6: 测试增量更新 (追加新数据)...")

    new_temps = [85.3, 86.1]
    for temp in new_temps:
        ingestor.ingest_single_point(
            batch_id="BATCH_001",
            node_code="E04",
            param_code="temp",
            value=temp,
            source="SIMULATION"
        )
        print(f"  追加温度: {temp}℃")

    # 重新查询
    measurements_updated = ingestor.get_batch_measurements("BATCH_001", "E04", "temp")
    print(f"  总数据点数: {len(measurements_updated)} (原来 {len(measurements)} + 新增 {len(new_temps)})")

    # ============================================================
    # 步骤 7: 测试新建批次
    # ============================================================
    print("\n🆕 步骤 7: 测试新建批次...")

    ingestor.ingest_single_point(
        batch_id="BATCH_002",
        node_code="E04",
        param_code="temp",
        value=88.5,
        source="SIMULATION"
    )
    print("  已创建新批次 BATCH_002")

    batch_count = db.query(models.Batch).count()
    print(f"  数据库中总批次数: {batch_count}")

    # ============================================================
    # 清理
    # ============================================================
    db.close()
    print("\n✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_architecture()
