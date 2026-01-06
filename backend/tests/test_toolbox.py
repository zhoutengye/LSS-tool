"""测试 LSS 超级工具箱架构

验证：
1. 工具注册中心
2. BaseTool 接口
3. SPC 工具功能
4. 统一调用接口
"""

import sys
sys.path.insert(0, "..")

from database import SessionLocal
from ingestion import DataIngestor
from core.registry import registry, get_tool, list_tools
import models


def test_toolbox_architecture():
    print("=" * 70)
    print("🧪 测试 LSS 超级工具箱架构")
    print("=" * 70)

    # ============================================================
    # 测试 1: 工具注册中心
    # ============================================================
    print("\n📦 测试 1: 工具注册中心")
    print("-" * 70)

    tools = list_tools()
    print(f"已注册工具数: {len(tools)}")

    for key, info in tools.items():
        print(f"  [{key}]")
        print(f"    名称: {info['name']}")
        print(f"    分类: {info['category']}")
        print(f"    描述: {info['description']}")
        print(f"    数据类型: {info['required_data_type']}")

    # ============================================================
    # 测试 2: 获取工具实例
    # ============================================================
    print("\n🔧 测试 2: 获取工具实例")
    print("-" * 70)

    spc_tool = get_tool("spc")
    if spc_tool:
        print(f"✅ 成功获取 SPC 工具")
        print(f"   类型: {type(spc_tool).__name__}")
        print(f"   名称: {spc_tool.name}")
        print(f"   分类: {spc_tool.category}")

    # ============================================================
    # 测试 3: 数据采集
    # ============================================================
    print("\n📊 测试 3: 数据采集")
    print("-" * 70)

    db = SessionLocal()
    ingestor = DataIngestor(db)

    # 模拟采集温度数据
    temp_data = [85.0, 86.0, 85.5, 87.0, 85.8, 84.5, 86.2, 85.9, 85.3, 86.1]

    for temp in temp_data:
        ingestor.ingest_single_point(
            batch_id="TEST_TOOLBOX",
            node_code="E04",
            param_code="temp",
            value=temp,
            source="SIMULATION"
        )

    print(f"✅ 已写入 {len(temp_data)} 条温度数据")

    # 查询数据
    measurements = ingestor.get_batch_measurements("TEST_TOOLBOX", "E04", "temp")
    data_values = [m.value for m in measurements]
    print(f"   数据: {[round(v, 1) for v in data_values]}")

    # ============================================================
    # 测试 4: 使用工具进行 SPC 分析
    # ============================================================
    print("\n📈 测试 4: SPC 分析")
    print("-" * 70)

    config = {
        "usl": 90.0,
        "lsl": 75.0,
        "target": 82.5
    }

    print(f"配置参数:")
    print(f"  USL (规格上限): {config['usl']}℃")
    print(f"  LSL (规格下限): {config['lsl']}℃")
    print(f"  Target (目标值): {config['target']}℃")

    # 调用工具
    result = spc_tool.run(data_values, config)

    print(f"\n分析结果:")
    print(f"  成功: {result['success']}")
    print(f"  警告: {len(result['warnings'])} 条")
    print(f"  错误: {len(result['errors'])} 条")

    if result['success']:
        print(f"\n关键指标:")
        for key, value in result['metrics'].items():
            print(f"  {key}: {value}")

        print(f"\n详细结果:")
        print(f"  平均值: {result['result']['mean']:.2f}℃")
        print(f"  标准差: {result['result']['std']:.3f}")
        print(f"  最小值: {result['result']['min']:.1f}℃")
        print(f"  最大值: {result['result']['max']:.1f}℃")
        print(f"  Cpk: {result['result']['cpk']}")
        print(f"  Cpu: {result['result']['cpu']}")
        print(f"  Cpl: {result['result']['cpl']}")

        # 判断过程能力等级
        cpk = result['result']['cpk']
        if cpk >= 2.0:
            grade = "优秀 (≥ 2.0)"
        elif cpk >= 1.67:
            grade = "良好 (≥ 1.67)"
        elif cpk >= 1.33:
            grade = "合格 (≥ 1.33)"
        elif cpk >= 1.0:
            grade = "需改进 (≥ 1.0)"
        else:
            grade = "不合格 (< 1.0)"

        print(f"\n过程能力等级: {grade}")

        # 违规点
        violations = result['result']['violations']
        if violations:
            print(f"\n⚠️  发现 {len(violations)} 个违规点:")
            for v in violations:
                print(f"  数据点 {v['index']}: {v['value']}℃ -> {v['type']}")
        else:
            print(f"\n✅ 无违规点")

    # 警告信息
    if result['warnings']:
        print(f"\n⚠️  警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    # ============================================================
    # 测试 5: 可视化数据生成
    # ============================================================
    print("\n📊 测试 5: 可视化数据生成")
    print("-" * 70)

    plot_data = result.get('plot_data', {})
    if plot_data:
        print(f"图表类型: {plot_data['type']}")
        print(f"数据点数: {len(plot_data['data'])}")
        print(f"参考线:")
        for key, line in plot_data['lines'].items():
            if line:
                print(f"  {key}: {line['y']:.2f} ({line['label']})")

    # ============================================================
    # 测试 6: 错误处理
    # ============================================================
    print("\n🚨 测试 6: 错误处理")
    print("-" * 70)

    # 空数据
    result_empty = spc_tool.run([], config)
    print(f"空数据测试: {'❌ 失败' if not result_empty['success'] else '✅ 通过'}")
    if result_empty['errors']:
        print(f"  错误: {result_empty['errors']}")

    # 单点数据
    result_single = spc_tool.run([85.0], config)
    print(f"单点数据测试: {'❌ 失败' if not result_single['success'] else '✅ 通过'}")
    if result_single['errors']:
        print(f"  错误: {result_single['errors']}")

    # ============================================================
    # 清理
    # ============================================================
    db.close()

    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)


def test_architecture_summary():
    """架构总结"""
    print("\n" + "=" * 70)
    print("📋 LSS 超级工具箱架构总结")
    print("=" * 70)

    print("""
✅ 已实现功能:

1. 基础架构 (core/base.py)
   - BaseTool 抽象基类
   - 统一的 run() 接口
   - 标准化的返回格式
   - 输入验证机制

2. 工具注册中心 (core/registry.py)
   - 单例模式管理工具
   - 工具注册与查询
   - 按分类筛选工具

3. SPC 工具 (core/spc_tools.py)
   - 过程能力指数计算 (Cpk, Cpu, Cpl)
   - 违规点检测
   - 控制图数据生成
   - 统计量计算

4. 数据采集 (ingestion.py)
   - 批次自动创建
   - 增量数据更新
   - 批次数据查询

🚀 未来扩展方向:

   第一层 (Descriptive):
   - 帕累托图 (Pareto)
   - 直方图 (Histogram)
   - 箱线图 (Box Plot)
   - OEE 分析

   第二层 (Diagnostic):
   - 相关性分析 (Correlation)
   - 方差分析 (ANOVA)
   - 假设检验 (Hypothesis Testing)
   - FMEA 分析

   第三层 (Predictive):
   - 贝叶斯网络 (Bayesian)
   - 时序预测 (Time Series)
   - 回归分析 (Regression)

   第四层 (Prescriptive):
   - 多目标优化 (NSGA-II)
   - 实验设计 (DOE)
   - 参数推荐 (Recommendation)

💡 设计优势:

   - 插件式架构，易于扩展
   - 统一接口，前端调用简单
   - 模块隔离，互不影响
   - 标准化输出格式
    """)


if __name__ == "__main__":
    test_toolbox_architecture()
    test_architecture_summary()
