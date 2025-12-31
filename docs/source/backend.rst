后端模块
========

FastAPI 主程序
---------------

.. automodule:: main
   :members:
   :undoc-members:
   :show-inheritance:

数据模型
--------

所有模型定义在 :py:mod:`models` 模块中，支持 IDEF0 层级结构和贝叶斯风险网络。

.. mermaid::
    :align: center

    classDiagram
        direction TB

        class ProcessNode {
            <<工序节点>>
            +id: int
            +code: str
            +name: str
            +parent_id: int
            +node_type: str
            +params: List
            +children: List
        }

        class ProcessEdge {
            <<流向连线>>
            +id: int
            +source_code: str
            +target_code: str
            +name: str
            +loss_rate: float
        }

        class ParameterDef {
            <<参数定义>>
            +id: int
            +node_id: int
            +code: str
            +name: str
            +unit: str
            +role: str
            +usl: float
            +lsl: float
            +target: float
            +data_type: str
        }

        ProcessNode "1" --o "many" ProcessEdge : 连接
        ProcessNode "1" *-- "many" ParameterDef : 包含

.. autoclass:: models.ProcessNode
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: models.ProcessEdge
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: models.ParameterDef
   :members:
   :undoc-members:
   :show-inheritance:

风险模型
--------

.. autoclass:: models.RiskNode
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: models.RiskEdge
   :members:
   :undoc-members:
   :show-inheritance:

测量数据与批次管理
------------------

.. autoclass:: models.Batch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: models.Measurement
   :members:
   :undoc-members:
   :show-inheritance:

数据采集
--------

.. automodule:: ingestion
   :members:
   :undoc-members:
   :show-inheritance:

LSS 工具箱核心
--------------

基础架构
~~~~~~~~

.. automodule:: core.base
   :members:
   :undoc-members:
   :show-inheritance:

工具注册中心
~~~~~~~~~~~~

.. automodule:: core.registry
   :members:
   :undoc-members:
   :show-inheritance:

SPC 分析工具
~~~~~~~~~~~~

.. automodule:: core.spc_tools
   :members:
   :undoc-members:
   :show-inheritance:

数据库配置
----------

.. automodule:: database
   :members:
   :undoc-members:
   :show-inheritance:

数据导入脚本
------------

.. automodule:: seed
   :members:
   :undoc-members:
   :show-inheritance:

API 端点
--------

获取图谱结构
~~~~~~~~~~~~

**接口**: ``GET /api/graph/structure``

**描述**: 获取完整的知识图谱结构，包括所有节点和边。

**返回格式**:

.. code-block:: json

   {
     "nodes": [
       {
         "id": "1",
         "data": {
           "label": "前处理车间",
           "type": "Block"
         },
         "position": {"x": 50, "y": 50}
       }
     ],
     "edges": [
       {
         "id": "block_edge_1_13",
         "source": "1",
         "target": "13",
         "label": "→"
       }
     ]
   }

**节点类型**:

- ``Block``: 四大车间 (前处理、提取纯化、制剂成型、内包外包)
- ``Unit``: 具体设备 (默认隐藏，点击父 Block 时显示)

仿真接口
~~~~~~~~

**接口**: ``POST /api/simulate``

**描述**: 执行工艺参数仿真计算 (临时版本)

**请求体**:

.. code-block:: json

   {
     "temperature": 85.0
   }

**返回**:

.. code-block:: json

   {
     "status": "ok",
     "result_yield": 98.0
   }

**注意**: 当前为临时逻辑，实际仿真算法需要根据工艺模型实现。

LSS 工具箱使用
--------------

工具箱采用插件式架构，所有工具继承自 :py:class:`~core.base.BaseTool`。

基本用法
^^^^^^^^

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
^^^^^^^^

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
^^^^^^^^^^^^

添加新工具需要三个步骤：

**1. 继承 BaseTool**

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

**2. 注册工具**

在 ``core/registry.py`` 中添加:

.. code-block:: python

   from .my_tool import MyTool

   registry.register("my_tool", MyTool())

**3. 使用工具**

.. code-block:: python

   from core.registry import get_tool

   tool = get_tool("my_tool")
   result = tool.run(data, config)

返回格式规范
^^^^^^^^^^^^

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

