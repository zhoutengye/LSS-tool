API 参考
=========

REST API 端点
--------------

图谱结构
~~~~~~~~

.. http:get:: /api/graph/structure

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

仿真接口
~~~~~~~~

.. http:post:: /api/simulate

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
