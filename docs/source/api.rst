API 参考
=========

系统采用 **Router Modularization（路由模块化）** 架构，所有 API 端点按功能模块组织。

**API 模块组织**:

- ``/api/graph/*`` - 工艺图谱相关（routers/graph.py）
- ``/api/analysis/*`` - 智能分析相关（routers/analysis.py）
- ``/api/instructions/*`` - 指令管理相关（routers/instructions.py）
- ``/api/monitor/*`` - 监控数据相关（routers/monitoring.py）
- ``/api/demo/*`` - 演示管理相关（routers/demo.py）
- ``/api/tools/*`` - LSS 工具箱相关（routers/lss_tools.py）

REST API 端点
--------------

工艺图谱 API (routers/graph.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**GET /api/graph/structure**

获取完整的知识图谱结构，包括所有节点和边。

**返回字段**:

- ``nodes`` (list): 节点列表

  - ``id`` (str): 节点唯一标识
  - ``data`` (dict): 节点数据

    - ``label`` (str): 显示名称
    - ``type`` (str): 节点类型 (Block/Unit)
    - ``params`` (list): 参数列表

  - ``position`` (dict): 画布位置
  - ``style`` (dict): 样式配置
  - ``hidden`` (bool): 是否隐藏

- ``edges`` (list): 边列表

  - ``id`` (str): 边唯一标识
  - ``source`` (str): 源节点 ID
  - ``target`` (str): 目标节点 ID
  - ``label`` (str): 连线标签
  - ``animated`` (bool): 是否动画
  - ``style`` (dict): 样式配置

**GET /api/graph/risks/tree**

获取完整的故障树结构。

**返回字段**:

- ``risks`` (list): 风险节点列表

  - ``id`` (str): 风险节点 ID
  - ``data`` (dict): 风险节点数据

    - ``label`` (str): 风险名称
    - ``category`` (str): 风险类别 (Top/Equipment/Material/Human/Environment/Method)
    - ``probability`` (float): 基础概率

  - ``type`` (str): 节点类型
  - ``position`` (dict): 画布位置

- ``edges`` (list): 风险因果关系边列表

**GET /api/graph/nodes/{node_code}/risks**

获取指定节点的相关风险。

**路径参数**:

- ``node_code`` (str): 节点代码（如 E04）

**返回字段**:

- ``risks`` (list): 相关风险节点列表

智能分析 API (routers/analysis.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**POST /api/analysis/person**

分析指定操作工的绩效。

**请求体**:

.. code-block:: json

   {
     "operator_id": "WORKER_007",
     "start_date": "2025-01-01",
     "end_date": "2025-01-08"
   }

**返回字段**: 分析报告（JSON 格式）

**POST /api/analysis/batch**

分析指定批次的质量表现。

**请求体**:

.. code-block:: json

   {
     "batch_id": "BATCH_001"
   }

**POST /api/analysis/process**

分析指定工序的统计特性。

**请求体**:

.. code-block:: json

   {
     "node_code": "E04",
     "param_code": "temp"
   }

**POST /api/analysis/workshop**

分析车间级别的整体绩效。

**请求体**:

.. code-block:: json

   {
     "workshop": "BLOCK_E"
   }

**POST /api/analysis/time**

分析时间维度的趋势变化。

**请求体**:

.. code-block:: json

   {
     "start_date": "2025-01-01",
     "end_date": "2025-01-08"
   }

**POST /api/analysis/daily**

生成每日生产日报。

**请求体**:

.. code-block:: json

   {
     "date": "2025-01-08"
   }

指令管理 API (routers/instructions.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**GET /api/instructions**

获取指令列表。

**查询参数**:

- ``role`` (str): 用户角色（worker/supervisor/manager）
- ``status`` (str, optional): 指令状态（Pending/Read/Done）

**返回字段**:

- ``instructions`` (list): 指令列表
  - ``id`` (int): 指令 ID
  - ``content`` (str): 指令内容
  - ``priority`` (str): 优先级（High/Medium/Low）
  - ``status`` (str): 状态（Pending/Read/Done）
  - ``created_at`` (datetime): 创建时间

**POST /api/instructions/{instruction_id}/read**

标记指令为已读（进行中）。

**路径参数**:

- ``instruction_id`` (int): 指令 ID

**POST /api/instructions/{instruction_id}/done**

标记指令为完成。

**路径参数**:

- ``instruction_id`` (int): 指令 ID

**请求体**:

.. code-block:: json

   {
     "feedback": "已完成调整"
   }

**POST /api/instructions/generate-today**

生成今日工艺指令（演示用）。

**返回字段**:

- ``generated_count`` (int): 生成的指令数量

监控数据 API (routers/monitoring.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**GET /api/monitor/node/{node_code}**

获取节点监控数据（实时 SCADA 或历史数据）。

**路径参数**:

- ``node_code`` (str): 节点代码

**查询参数**:

- ``hours`` (int, optional): 查询最近 N 小时数据（默认 24）

**返回字段**:

- ``node_code`` (str): 节点代码
- ``data`` (list): 监控数据点列表

**GET /api/monitor/latest**

获取所有节点的最新状态（用于节点颜色更新）。

**返回字段**:

- ``nodes`` (list): 节点状态列表
  - ``node_code`` (str): 节点代码
  - ``status`` (str): 状态（Normal/Warning/Error）
  - ``last_update`` (datetime): 最后更新时间

演示管理 API (routers/demo.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DELETE /api/demo/reset**

重置演示环境（回到初始状态）。

**返回字段**:

- ``success`` (bool): 操作是否成功
- ``message`` (str): 提示信息

**POST /api/demo/init-actions**

初始化对策库数据（演示用）。

**返回字段**:

- ``success`` (bool): 操作是否成功
- ``count`` (int): 初始化的对策数量

**POST /api/demo/shift-report**

下工填报单（工人填写生产数据）。

**请求体**:

.. code-block:: json

   {
     "batch_id": "BATCH_001",
     "operator_id": "WORKER_007",
     "measurements": [
       {
         "node_code": "E04",
         "param_code": "temp",
         "value": 98.5
       }
     ]
   }

**POST /api/demo/login**

工人上工登录（刷卡）。

**请求体**:

.. code-block:: json

   {
     "operator_id": "WORKER_007"
   }

**返回字段**:

- ``success`` (bool): 登录是否成功
- ``instructions`` (list): 今日指令列表

LSS 工具箱 API (routers/lss_tools.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**POST /api/tools/spc/control-chart**

SPC 控制图分析。

**请求体**:

.. code-block:: json

   {
     "batch_id": "BATCH_001",
     "node_code": "E04",
     "param_code": "temp"
   }

**POST /api/tools/pareto**

帕累托图分析。

**POST /api/tools/histogram**

直方图分析。

**POST /api/tools/boxplot**

箱线图分析。

基础接口
~~~~~~~~

**GET /**

系统状态检查。

**返回字段**:

- ``status`` (str): 系统状态
- ``modules`` (list): 可用模块列表

**GET /api/test**

后端连接测试。

**POST /api/simulate**

执行工艺参数仿真计算。

**请求体**:

.. code-block:: json

   {
     "temperature": 85.0
   }

**返回字段**:

- ``status`` (str): 状态标识
- ``result_yield`` (float): 仿真得率 (%)

数据模型
--------

ProcessNode
~~~~~~~~~~~

.. py:class:: ProcessNode

   工序节点模型，支持层级结构 (Block → Unit)。

   :param id: 主键
   :type id: int
   :param code: 节点代码 (如: E04)
   :type code: str
   :param name: 节点名称 (如: 醇提1)
   :type name: str
   :param parent_id: 父节点 ID
   :type parent_id: int
   :param node_type: 节点类型 (Block/Unit)
   :type node_type: str

ProcessEdge
~~~~~~~~~~~

.. py:class:: ProcessEdge

   工艺流向连线。

   :param id: 主键
   :type id: int
   :param source_code: 源节点代码
   :type source_code: str
   :param target_code: 目标节点代码
   :type target_code: str
   :param name: 流动物料名
   :type name: str
   :param loss_rate: 传输损耗率
   :type loss_rate: float

ParameterDef
~~~~~~~~~~~~

.. py:class:: ParameterDef

   参数定义。

   :param id: 主键
   :type id: int
   :param node_id: 关联节点 ID
   :type node_id: int
   :param code: 参数代码
   :type code: str
   :param name: 参数名称
   :type name: str
   :param unit: 单位
   :type unit: str
   :param role: 角色 (Control/Output/Input)
   :type role: str
   :param usl: 规格上限
   :type usl: float
   :param lsl: 规格下限
   :type lsl: float
   :param target: 目标值
   :type target: float
   :param is_material: 是否物料参数
   :type is_material: bool
   :param data_type: 数据类型 (Scalar/Spectrum/Image)
   :type data_type: str

错误处理
--------

所有 API 端点在发生错误时返回标准错误格式：

.. code-block:: json

   {
      "detail": "错误描述信息"
   }

常见 HTTP 状态码：

- ``200 OK``: 请求成功
- ``400 Bad Request``: 请求参数错误
- ``404 Not Found``: 资源不存在
- ``500 Internal Server Error``: 服务器内部错误
