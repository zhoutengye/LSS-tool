前端模块
========

前端采用 React 19.2.0 + Vite 7.2.4 + Ant Design 6.1.3 技术栈，提供三大功能页面。

三大功能页面
------------

1. 工艺监控页面
~~~~~~~~~~~~~~~

**核心组件**: ProcessFlow + MonitorPanel + ActionList

**主要功能**:

- 知识图谱可视化（React Flow）
  - 可折叠的区块展示（Block → Unit 层级结构）
  - 动态加载子节点
  - 节点点击交互（展开/折叠、查看详情、风险分析）

- 实时数据监控（MonitorPanel）
  - 时序趋势图（ECharts）
  - 控制限监控（USL/LSL/Target）
  - 统计摘要（均值、标准差、Cpk）

- 工艺指令系统（ActionList）
  - 今日工艺指令列表
  - 支持多状态过滤（Pending, Read）
  - 指令执行和完成操作

**状态管理**:

.. code-block:: javascript

   const [nodes, setNodes] = useState([]);
   const [edges, setEdges] = useState([]);
   const [expandedBlocks, setExpandedBlocks] = useState(new Set());
   const [selectedNode, setSelectedNode] = useState(null);
   const [isLiveMode, setIsLiveMode] = useState(false);

**交互设计**:

- 单击节点: 展开/折叠子节点
- 双击节点: 查看节点详情和参数监控
- 右键节点: 查看风险分析

2. LSS工具箱页面
~~~~~~~~~~~~~~~~

**核心组件**: LSSToolsPage + 4个LSS可视化组件

**主要功能**:

- **帕累托图 (ParetoChart)**
  - 识别"关键少数"问题（80/20法则）
  - 累计贡献率曲线
  - ABC分类

- **直方图 (HistogramChart)**
  - 频数分布柱状图
  - 正态分布拟合曲线
  - 统计检验（Shapiro-Wilk、偏度、峰度）

- **箱线图 (BoxplotChart)**
  - 多车间对比分析
  - 异常值识别
  - 统计摘要（中位数、四分位数、最大最小值）

- **SPC控制图 (SPCChart)**
  - 单值-移动极差控制图
  - 控制限（UCL/LCL）和规格限（USL/LSL）
  - Nelson Rules违规点检测
  - 过程能力分析（Cpk/Cp）

**技术特点**:

- 所有图表使用 ECharts 6.0.0 渲染
- 支持数据缩放和拖拽
- 交互式tooltip显示详细信息
- 响应式布局设计

3. AI黑带专家页面
~~~~~~~~~~~~~~~~~

**核心组件**: IntelligentAnalysisPage

**主要功能**:

- **自动工具链编排**
  - 步骤1: 帕累托图分析 → 识别关键问题
  - 步骤2: SPC控制图 → 评估过程能力
  - 步骤3: 直方图分析 → 检验数据分布
  - 步骤4: 箱线图对比 → 车间对比分析
  - 步骤5: 综合诊断 → 生成改进方案

- **智能诊断报告**
  - 过程能力等级判定（A/B/C/D级）
  - 根因分析（影响程度排序）
  - 风险评估（紧急/高/中/低优先级）

- **DMAIC改进路径**
  - Define阶段: 聚焦关键问题，设定改进目标
  - Measure阶段: 建立测量系统分析
  - Analyze阶段: 验证根本原因
  - Improve阶段: 优化工艺参数，实施SPC
  - Control阶段: 建立控制计划，持续改进

- **可视化报告**
  - 过程健康度雷达图
  - 能力等级统计卡片
  - 根因分析时间线
  - 预期收益评估

**使用流程**:

1. 点击"启动黑带分析流程"按钮
2. 系统自动执行5个分析步骤（显示进度条）
3. 分析完成后，自动生成综合诊断报告
4. 查看DMAIC改进路径和预期收益

详细文档请参考 :doc:`ai_expert`。

页面导航
--------

系统通过顶部导航栏实现三大功能页面的切换：

.. code-block:: javascript

   const [currentPage, setCurrentPage] = useState('home');
   // 'home' (工艺监控) | 'lss-tools' (LSS工具箱) | 'intelligent-analysis' (AI黑带专家)

   <Button onClick={() => setCurrentPage('home')}>工艺监控</Button>
   <Button onClick={() => setCurrentPage('lss-tools')}>LSS工具箱</Button>
   <Button onClick={() => setCurrentPage('intelligent-analysis')}>AI黑带专家</Button>

**模式切换**:

- 实时监控模式 - 显示实时数据更新
- 仿真模式 - 使用历史/仿真数据

组件结构
--------

.. code-block:: text

   src/
   ├── components/
   │   ├── ProcessFlow.jsx        # 工艺流程图
   │   ├── MonitorPanel.jsx       # 监控面板
   │   ├── ActionList.jsx         # 工艺指令列表
   │   └── lss/                   # LSS可视化组件
   │       ├── ParetoChart.jsx    # 帕累托图
   │       ├── HistogramChart.jsx # 直方图
   │       ├── BoxplotChart.jsx   # 箱线图
   │       └── SPCChart.jsx       # SPC控制图
   ├── pages/
   │   ├── LSSToolsPage.jsx       # LSS工具箱页面
   │   └── IntelligentAnalysisPage.jsx  # AI黑带专家页面
   └── App.jsx                    # 应用根组件（导航）

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
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   border: 2px solid #52c41a;
   background: white;
   borderRadius: 8px;
   fontSize: 14px;

图表组件
~~~~~~~~

所有LSS可视化组件采用统一样式：

- 使用 Ant Design Card 组件包裹
- 图表高度统一为 400px
- 颜色方案符合Ant Design规范
- 支持响应式布局

启动方式
--------

.. code-block:: bash

   cd frontend
   source ~/.nvm/nvm.sh  # 如果使用 nvm
   nvm use 20           # Vite 7.2.4 需要 Node 20.19+
   npm install
   npm run dev

**注意事项**:

- 必须使用 Node.js 20.19+ 版本
- 如果遇到版本不匹配，使用 ``nvm use 20`` 切换
- 前端默认运行在 ``http://localhost:5173``
- 后端API默认运行在 ``http://127.0.0.1:8000``
