LSS 工具箱
=========

概述
-----

LSS 工具箱采用**插件式架构**，支持扩展多种精益六西格玛分析工具。

设计模式
--------

.. mermaid::
    :align: center

    classDiagram
        class BaseTool {
            <<abstract>>
            +name: str
            +category: str
            +required_data_type: str
            +run(data, config) dict
            +validate_input(data, config)
            +format_result(...)
        }

        class SPCToolbox {
            +name: "SPC 统计过程控制分析"
            +category: "Descriptive"
            +run(data, config) dict
            -_calculate_cpk(data, usl, lsl)
            -_check_violations(data, usl, lsl)
            -_generate_control_chart_data(...)
        }

        class ToolRegistry {
            -_tools: dict
            +register(key, tool)
            +get_tool(key) BaseTool
            +list_tools() dict
        }

        class DataIngestor {
            -db: Session
            +ingest_single_point(...)
            +get_batch_measurements(...)
        }

        BaseTool <|-- SPCToolbox
        ToolRegistry --> BaseTool : 管理工具
        DataIngestor ..> SPCToolbox : 提供数据

工具分类
--------

第一层：描述性统计 (Descriptive) - 7工具
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**用途**: 回答"发生了什么？"

.. list-table:: 描述性统计工具
   :widths: 30 70
   :header-rows: 1

   * - 工具
     - 功能说明

   * - SPC ✅ 已实现
     - 统计过程控制分析，计算 Cpk、控制限，判定过程是否受控

   * - 帕累托图 (Pareto) ✅ 已实现
     - 识别"关键少数"问题，80/20法则分析，累计贡献率计算

   * - 直方图 (Histogram) ✅ 已实现
     - 频数分布统计、正态性检验 (Shapiro-Wilk)、偏度和峰度计算

   * - 箱线图 (Boxplot) ✅ 已实现
     - 多车间对比分析，识别异常值，寻找最佳实践标杆

   * - Cpk 过程能力分析
     - 过程能力指数计算 (Cpk, Cp, Ppk)、置信区间、能力等级判定

   * - I-MR 控制图
     - 单值-移动极差控制图、Nelson Rules 异常检测、控制限计算

   * - Xbar-R 控制图
     - 均值-极差控制图，适用于子组数据

   * - P图/U图
     - 不合格品率/单位缺陷数控制图

   * - OEE 设备效率分析
     - 设备综合效率计算

第二层：诊断性分析 (Diagnostic) - 6工具
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**用途**: 回答"为什么会发生？"

.. list-table:: 诊断性分析工具
   :widths: 30 70
   :header-rows: 1

   * - 工具
     - 功能说明

   * - FTA 故障树分析
     - 最小割集识别 (MCS)、概率重要度计算、自动匹配 ActionDef 对策库

   * - 鱼骨图
     - 因果分析图，人机料法环

   * - 相关性分析
     - 参数关系分析

   * - ANOVA 方差分析
     - 判断显著性差异

   * - 双样本T检验
     - 比较两组数据差异

第三层：预测性分析 (Predictive) - 5工具
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**用途**: 回答"将来会发生什么？"

.. list-table:: 预测性分析工具
   :widths: 30 70
   :header-rows: 1

   * - 工具
     - 功能说明

   * - 贝叶斯网络
     - 贝叶斯风险推演，预测故障概率

   * - 相关性热力图
     - 多变量相关性矩阵、Pearson/Spearman 相关系数、显著性检验

   * - 多元回归
     - 回归分析，建立 Y = f(X) 模型、模型性能评估 (R², RMSE)

   * - 时序预测 (ARIMA)
     - ARIMA/Prophet 时序预测

   * - Monte Carlo 仿真
     - 蒙特卡洛模拟

第四层：规范性分析 (Prescriptive) - 5工具
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**用途**: 回答"怎么做最好？"

.. list-table:: 规范性分析工具
   :widths: 30 70
   :header-rows: 1

   * - 工具
     - 功能说明

   * - NSGA-II 多目标优化
     - 多目标优化，寻找 Pareto 前沿

   * - DOE 实验设计
     - 实验设计，生成正交表

   * - 响应曲面法 (RSM)
     - 响应曲面分析

   * - 田口方法
     - 稳健参数设计

   * - 约束优化
     - 参数推荐引擎

**说明**:
- ✅ 已实现 (4个LSS基础工具)
- 其他工具可后续补充

使用示例
--------

基本用法
~~~~~~~

.. code-block:: python

   from core.registry import get_tool

   # 获取工具
   spc = get_tool("spc")

   # 准备数据和配置
   data = [85.0, 86.0, 85.5, 87.0, 85.8]
   config = {
       "usl": 90.0,
       "lsl": 75.0,
       "target": 82.5
   }

   # 运行分析
   result = spc.run(data, config)

   # 查看结果
   print(result["success"])  # True
   print(result["metrics"]["cpk"])  # 2.045
   print(result["warnings"])  # []


数据采集
~~~~~~~

.. code-block:: python

   from database import SessionLocal
   from ingestion import DataIngestor

   db = SessionLocal()
   ingestor = DataIngestor(db)

   # 采集数据 (自动创建批次)
   ingestor.ingest_single_point(
       batch_id="BATCH_001",
       node_code="E04",
       param_code="temp",
       value=85.5,
       source="SENSOR"
   )

   # 查询数据
   measurements = ingestor.get_batch_measurements(
       batch_id="BATCH_001",
       node_code="E04",
       param_code="temp"
   )

   data = [m.value for m in measurements]

   db.close()


工具开发指南
--------------

添加新工具
~~~~~~~~~~

1. **继承 BaseTool**

   .. code-block:: python

      from core.base import BaseTool
      from typing import Dict, List

      class MyTool(BaseTool):
          @property
          def name(self) -> str:
              return "我的分析工具"

          @property
          def category(self) -> str:
              return "Descriptive"

          @property
          def required_data_type(self) -> str:
              return "TimeSeries"

          def run(self, data: List[float], config: Dict) -> Dict:
              # 验证输入
              is_valid, errors = self.validate_input(data, config)
              if not is_valid:
                  return self.format_result(errors=errors)

              # 实现分析逻辑
              result = {"my_metric": ...}

              # 返回标准格式
              return self.format_result(
                  result=result,
                  metrics={"my_metric": ...}
              )

2. **注册工具**

   在 ``core/registry.py`` 中添加:

   .. code-block:: python

      from .my_tool import MyTool

      registry.register("my_tool", MyTool())

3. **使用工具**

   .. code-block:: python

      from core.registry import get_tool

      tool = get_tool("my_tool")
      result = tool.run(data, config)


返回格式规范
~~~~~~~~~~~~

所有工具必须返回统一格式:

.. code-block:: json

   {
       "success": true,
       "result": {
           "详细分析结果..."
       },
       "plot_data": {
           "type": "control_chart",
           "data": [...],
           "lines": {...}
       },
       "metrics": {
           "cpk": 2.045,
           "mean": 85.73
       },
       "warnings": [
           "过程能力不足"
       ],
       "errors": []
   }
