"""LSS 工具箱综合测试脚本

测试所有已实现的LSS工具：SPC、Pareto、Histogram、Boxplot
"""

from database import SessionLocal
import models
from core.registry import registry, register_all_tools
import json


def test_all_tools():
    """测试所有LSS工具"""

    print("=" * 60)
    print("LSS 工具箱综合测试")
    print("=" * 60)
    print()

    # 注册所有工具
    register_all_tools()

    # 列出已注册工具
    tools = registry.list_tools()
    print(f"✅ 已注册 {len(tools)} 个工具:")
    for tool_key, tool_info in tools.items():
        print(f"   - {tool_info['name']} ({tool_key})")
    print()

    db = SessionLocal()

    try:
        # ==================== 测试1: SPC工具 ====================
        print("🔧 测试1: SPC过程能力分析")
        print("-" * 60)

        # 获取E01的温度数据
        measurements = db.query(models.Measurement).filter(
            models.Measurement.param_code == "P_E01_TEMP"
        ).limit(50).all()

        data = [m.value for m in measurements]
        spc_tool = registry.get_tool("spc")
        result = spc_tool.run(data, {"usl": 90.0, "lsl": 80.0})

        print(f"✅ SPC分析完成")
        print(f"   - Cpk: {result['result']['cpk']:.3f}")
        print(f"   - 均值: {result['result']['mean']:.2f}")
        print(f"   - 标准差: {result['result']['std']:.3f}")
        print(f"   - 违规点: {len(result['result']['violations'])}个")
        if result.get('insights'):
            print(f"   - 洞察: {result['insights'][0]}")
        print()

        # ==================== 测试2: 帕累托图工具 ====================
        print("🔧 测试2: 帕累托图分析")
        print("-" * 60)

        # 使用故障类别数据
        fault_data = [
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

        pareto_tool = registry.get_tool("pareto")
        result = pareto_tool.run(fault_data, {"threshold": 0.8})

        print(f"✅ 帕累托分析完成")
        print(f"   - 总类别: {result['result']['total_categories']}个")
        print(f"   - 关键少数: {result['result']['key_few_count']}个")
        print(f"   - 贡献率: {result['result']['key_few_contribution']:.1f}%")
        print(f"   - A类问题: {', '.join(result['result']['abc_classification']['A'][:3])}")
        if result.get('insights'):
            for insight in result['insights'][:3]:
                print(f"   - {insight}")
        print()

        # ==================== 测试3: 直方图工具 ====================
        print("🔧 测试3: 直方图分析")
        print("-" * 60)

        # 获取C01温度数据
        measurements = db.query(models.Measurement).filter(
            models.Measurement.param_code == "P_C01_TEMP"
        ).limit(50).all()

        data = [m.value for m in measurements]
        hist_tool = registry.get_tool("histogram")
        result = hist_tool.run(data, {"bins": 10, "usl": 70.0, "lsl": 60.0})

        print(f"✅ 直方图分析完成")
        print(f"   - 样本数: {result['result']['n']}")
        print(f"   - 均值: {result['result']['mean']:.2f}")
        print(f"   - 标准差: {result['result']['std']:.3f}")
        print(f"   - 分布类型: {result['result']['distribution_type']}")
        print(f"   - 正态性: {'是' if result['result']['is_normal'] else '否'}")
        if result.get('insights'):
            for insight in result['insights'][:3]:
                print(f"   - {insight}")
        print()

        # ==================== 测试4: 箱线图工具 ====================
        print("🔧 测试4: 箱线图分析（多车间对比）")
        print("-" * 60)

        # 对比E01-E04的温度
        multi_series_data = {}
        for node_code in ["E01", "E02", "E03", "E04"]:
            measurements = db.query(models.Measurement).filter(
                models.Measurement.node_code == node_code,
                models.Measurement.param_code.like("%TEMP%")
            ).all()

            if measurements:
                multi_series_data[f"{node_code}温度"] = [m.value for m in measurements]

        boxplot_tool = registry.get_tool("boxplot")
        result = boxplot_tool.run(multi_series_data, {})

        print(f"✅ 箱线图分析完成")
        print(f"   - 对比组数: {len(multi_series_data)}")
        print(f"   - 总异常值: {result['result']['total_outliers']}个")
        print(f"   - 最大波动: {result['result']['comparison']['most_variable']}")
        if result['result'].get('insights'):
            for insight in result['result']['insights'][:3]:
                print(f"   - {insight}")
        print()

        # ==================== 总结 ====================
        print("=" * 60)
        print("✅ 所有工具测试完成!")
        print("=" * 60)
        print()
        print("📊 工具演示场景建议:")
        print("1. 帕累托图 → 用于QA会议，展示故障分布")
        print("2. 直方图 → 用于工艺分析，查看参数分布")
        print("3. 箱线图 → 用于车间对比，识别最佳实践")
        print("4. SPC分析 → 用于日常监控，预警过程异常")
        print()

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    test_all_tools()
