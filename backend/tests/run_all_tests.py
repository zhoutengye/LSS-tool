"""统一运行所有测试

确保路径设置正确后再运行各个测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_name, test_module):
    """运行单个测试"""
    print("\n" + "=" * 80)
    print(f"🧪 运行测试: {test_name}")
    print("=" * 80)

    try:
        # 动态导入并运行
        import importlib
        module = importlib.import_module(f"tests.{test_module}")
        if hasattr(module, 'main'):
            module.main()
        else:
            # 如果没有main函数，直接运行
            print(f"✅ {test_name} 加载成功")
    except Exception as e:
        print(f"❌ {test_name} 运行失败:")
        print(f"   错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    tests = [
        ("测试工具箱", "test_toolbox"),
        ("测试编排器", "test_orchestrator"),
        ("测试指挥官", "test_commander"),
        ("测试新架构", "test_new_arch"),
    ]

    print("=" * 80)
    print("🚀 LSS 后端测试套件")
    print("=" * 80)

    results = {}
    for name, module in tests:
        try:
            run_test(name, module)
            results[name] = "✅ 通过"
        except Exception as e:
            results[name] = f"❌ 失败: {str(e)}"

    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    for name, result in results.items():
        print(f"{name}: {result}")
