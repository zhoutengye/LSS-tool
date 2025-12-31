前端模块
========

React 组件
-----------

ProcessFlow 组件
~~~~~~~~~~~~~~~~~

主要流程图组件，负责可视化知识图谱。

**主要功能**:

- 可折叠的区块展示
- 动态加载子节点
- 参数配置弹窗
- 仿真结果可视化

**状态管理**:

.. code-block:: javascript

   const [nodes, setNodes] = useState([]);
   const [edges, setEdges] = useState([]);
   const [expandedBlocks, setExpandedBlocks] = useState(new Set());

**关键方法**:

- ``onNodeClick``: 处理节点点击事件（展开/折叠）
- ``onNodeDoubleClick``: 处理节点双击事件（打开参数配置）
- ``handleOk``: 执行仿真计算

App 组件
~~~~~~~~~

应用根组件。

样式设计
--------

区块节点 (Block Node)
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   border: 3px solid #1890ff;
   background: #e6f7ff;
   borderRadius: 12px;
   fontSize: 18px;
   fontWeight: bold;

单元节点 (Unit Node)
~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   border: 2px solid #52c41a;
   background: white;
   borderRadius: 8px;
   fontSize: 14px;
