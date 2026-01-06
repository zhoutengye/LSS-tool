"""测试智能编排层框架

验证 BlackBeltCommander 的多维度分析功能。
"""

from database import SessionLocal
from analysis import BlackBeltCommander


def test_batch_analysis():
    """测试批次分析"""
    print("=" * 60)
    print("测试 1: 批次分析")
    print("=" * 60)

    db = SessionLocal()

    try:
        commander = BlackBeltCommander(db)

        # 分析 BATCH_001
        print("\n📊 分析 BATCH_001...")
        report = commander.analyze_by_batch("BATCH_001")

        print(f"\n✅ 分析完成!")
        print(f"维度: {report.dimension}")
        print(f"状态: {report.overall_status}")
        print(f"分析ID: {report.analysis_id}")

        print(f"\n📈 关键指标:")
        print(f"  - 总参数数: {report.analysis_metadata.get('total_parameters', 0)}")
        print(f"  - 分析参数数: {report.analysis_metadata.get('analyzed_parameters', 0)}")
        print(f"  - 问题参数数: {report.analysis_metadata.get('problem_parameters', 0)}")

        if report.critical_issues:
            print(f"\n🔴 紧急问题 ({len(report.critical_issues)}):")
            for issue in report.critical_issues[:3]:
                print(f"  - {issue.get('description', '')}")

        if report.warnings:
            print(f"\n⚠️  警告 ({len(report.warnings)}):")
            for warning in report.warnings[:3]:
                print(f"  - {warning.get('description', '')}")

        if report.priority_actions:
            print(f"\n✅ 优先级行动建议:")
            for i, action in enumerate(report.priority_actions[:3], 1):
                print(f"  {i}. {action['action']}")
                print(f"     优先级: {action.get('priority', '')}")
                print(f"     预期: {action.get('estimated_impact', '')}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def test_process_analysis():
    """测试工序分析"""
    print("\n\n")
    print("=" * 60)
    print("测试 2: 工序分析")
    print("=" * 60)

    db = SessionLocal()

    try:
        commander = BlackBeltCommander(db)

        # 分析 E04 醇提罐
        print("\n📊 分析 E04 醇提罐 (最近7天)...")
        report = commander.analyze_by_process("E04", time_window=7)

        print(f"\n✅ 分析完成!")
        print(f"维度: {report.dimension}")
        print(f"状态: {report.overall_status}")

        print(f"\n📈 关键指标:")
        print(f"  - 总参数数: {report.analysis_metadata.get('total_parameters', 0)}")
        print(f"  - 分析参数数: {report.analysis_metadata.get('analyzed_parameters', 0)}")

        if report.priority_actions:
            print(f"\n✅ 改进建议:")
            for action in report.priority_actions[:3]:
                print(f"  - {action['action']}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def test_workshop_analysis():
    """测试车间分析"""
    print("\n\n")
    print("=" * 60)
    print("测试 3: 车间分析")
    print("=" * 60)

    db = SessionLocal()

    try:
        commander = BlackBeltCommander(db)

        # 分析提取车间
        print("\n📊 分析提取车间 (BLOCK_E)...")
        report = commander.analyze_by_workshop("BLOCK_E", date="2025-01-03")

        print(f"\n✅ 分析完成!")
        print(f"维度: {report.dimension}")
        print(f"状态: {report.overall_status}")

        print(f"\n📈 关键指标:")
        print(f"  - 总参数数: {report.analysis_metadata.get('total_parameters', 0)}")
        print(f"  - 问题参数数: {report.analysis_metadata.get('problem_parameters', 0)}")

        if report.critical_issues:
            print(f"\n🔴 紧急问题:")
            for issue in report.critical_issues[:5]:
                print(f"  - {issue.get('description', '')}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def test_quick_actions():
    """测试快速行动建议 API"""
    print("\n\n")
    print("=" * 60)
    print("测试 4: 快速行动建议")
    print("=" * 60)

    db = SessionLocal()

    try:
        commander = BlackBeltCommander(db)

        print("\n📊 获取 BATCH_001 的快速行动建议...")
        actions = commander.get_recommended_actions("BATCH_001", max_actions=3)

        print(f"\n✅ 找到 {len(actions)} 个行动建议:")
        for i, action in enumerate(actions, 1):
            print(f"\n{i}. {action['action']}")
            print(f"   优先级: {action.get('priority', '')}")
            print(f"   预期效果: {action.get('estimated_impact', '')}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 开始测试智能编排层框架\n")

    # 运行所有测试
    test_batch_analysis()
    test_process_analysis()
    test_workshop_analysis()
    test_quick_actions()

    print("\n\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
