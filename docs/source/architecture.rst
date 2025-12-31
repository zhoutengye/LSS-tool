系统架构
========

本系统采用**元数据驱动 (Metadata-Driven)** 的三位一体架构设计。

核心设计理念
------------

系统由三大支柱组成，形成**元数据驱动 (Metadata-Driven)** 的三位一体架构。

1. **知识图谱 (The Graph)**：系统的"法律与地图"

   定义工厂有什么设备、什么参数、什么风险
   （对应 PDF 第 2、3、4 章，存储在 CSV 文件中）

   **三层建模结构**：

   - **L1 物理层 (ProcessNode)**：定义"前处理 → 提取 → 制剂"的拓扑结构

     - Block（车间）：4 大车间（前处理、提取纯化、制剂成型、内包外包）

     - Unit（设备）：具体设备节点（如 E04 醇提罐、P03 称重台）

     - 父子关系：支持层级展开，点击 Block 显示下属 Unit

   - **L2 感知层 (ParameterDef)**：定义每个节点的参数（CPP/CQA）

     - **Input**：输入参数（如三七重量、黄精重量）

     - **Control**：控制参数（如温度、压力、湿度）

     - **Output**：输出参数（如重金属残留、皂苷含量）

     - **规格限**：USL（上限）、LSL（下限）、Target（目标值）

   - **L3 逻辑层 (RiskNode/RiskEdge)**：定义故障树和因果关系

     - 风险分类：人/机/料/法/环

     - 贝叶斯先验概率：支持风险推理计算

     - 因果关系：参数异常 → 风险节点

2. **数据引擎 (The Data)**：系统的"血液"

   负责海量数据的采集、清洗、存储与增量更新
   （生成 SQLite 数据库文件）

   **双模存储设计**：

   - **知识图谱 (Meta Data)**：静态配置

     - 数据来源：CSV 文件（``initial_data/`` 文件夹）

     - 更新频率：低（系统初始化或工艺变更时）

     - 数据量：小（几千行）

     - 表结构：``meta_process_nodes``、``meta_parameters``、``meta_risk_nodes`` 等

     - 查询模式：频繁读取，极少修改

   - **生产数据 (Instance Data)**：动态测量

     - 数据来源：实时采集（Excel/PLC/仿真）

     - 更新频率：高（每秒多次）

     - 数据量：大（历史累积）

     - 表结构：``data_batches``（批次索引）和 ``data_measurements``（测量流水）

     - 查询模式：批量查询统计分析

   **Auto-Create Batch 机制**：

   - 首次写入新批次号时自动创建 Batch 记录

   - 同一批次后续写入自动追加（增量更新）

   - 支持多源数据：HISTORY（历史）、SIMULATION（仿真）、SENSOR（实时）

3. **算法工具箱 (The Toolbox)**：系统的"大脑"

   插件化集成了从基础 SPC 到高级 AI 的所有分析工具
   （对应 PDF 第 6 章）

   **插件式架构**：

   - **BaseTool**：所有工具的抽象基类，定义统一接口

   - **ToolRegistry**：单例模式的工具注册中心

   - **DataIngestor**：数据采集器，为工具提供标准化数据

   **四层工具体系（按 DMAIC 改进循环分层）**：

   - **第一层：描述性统计 (Descriptive)** - 回答"发生了什么？"

     - SPC 统计过程控制（已实现）：控制图、Cpk 分析、异常检测

     - Pareto 帕累托图（规划中）：二八法则分析

     - Histogram 直方图（规划中）：分布拟合

     - OEE 设备综合效率（规划中）

   - **第二层：诊断性分析 (Diagnostic)** - 回答"为什么会发生？"

     - Correlation 相关性分析（规划中）：参数关系热力图

     - ANOVA 方差分析（规划中）：显著性差异判断

     - FTA 故障树分析（规划中）：根因反推

     - FMEA 失效模式分析（规划中）

   - **第三层：预测性分析 (Predictive)** - 回答"将来会发生什么？"

     - Bayesian Network 贝叶斯网络（规划中）：风险概率推演

     - Time Series 时序预测（规划中）：ARIMA/Prophet

     - Regression 回归分析（规划中）：建立 Y = f(X) 模型

   - **第四层：指导性优化 (Prescriptive)** - 回答"怎么做最好？"

     - NSGA-II 多目标优化（规划中）：寻找 Pareto 前沿

     - DOE 实验设计（规划中）：生成正交表

     - Recommendation 参数推荐（规划中）：智能建议

.. mermaid::
    :align: center

    graph TB
        subgraph 前端
            F[React + ReactFlow<br/>知识图谱可视化]
        end

        subgraph 后端
            API[FastAPI 主程序<br/>RESTful API 网关]

            subgraph 知识图谱层
                direction TB
                G_L1[L1 物理层<br/>ProcessNode<br/>Block/Unit 拓扑]
                G_L2[L2 感知层<br/>ParameterDef<br/>Input/Control/Output]
                G_L3[L3 逻辑层<br/>RiskNode/RiskEdge<br/>故障树与贝叶斯]
                G_L1 --> G_L2
                G_L2 --> G_L3
            end

            subgraph 数据引擎层
                direction TB
                D_Meta[知识图谱<br/>Meta Data<br/>静态配置<br/>CSV 加载]
                D_Inst[生产数据<br/>Instance Data<br/>动态测量<br/>实时采集]
                DI[DataIngestor<br/>ETL 适配器<br/>Auto-Create Batch]
                DI --> D_Meta
                DI --> D_Inst
            end

            subgraph 工具箱层
                direction TB
                T_L1[第一层: 描述性<br/>SPC/Pareto/Histogram]
                T_L2[第二层: 诊断性<br/>Correlation/ANOVA/FTA]
                T_L3[第三层: 预测性<br/>Bayesian/Time Series]
                T_L4[第四层: 指导性<br/>NSGA-II/DOE]
                T_L1 --> T_L2
                T_L2 --> T_L3
                T_L3 --> T_L4
                TR[ToolRegistry<br/>工具注册中心<br/>BaseTool 基类]
                TR -.-> T_L1
                TR -.-> T_L2
                TR -.-> T_L3
                TR -.-> T_L4
            end
        end

        subgraph 存储
            CSV[initial_data/<br/>CSV 源文件]
            DB[lss_factory.db<br/>SQLite 数据库]
            DB_Meta[(meta_ 表<br/>知识图谱)]
            DB_Data[(data_ 表<br/>生产数据)]
        end

        F -->|HTTP/JSON| API
        API --> G_L1
        API --> D_Meta
        API --> T_L1

        G_L1 -->|seed.py 加载| CSV
        G_L1 --> DB_Meta
        D_Meta -.-> DB_Meta

        DI --> D_Inst
        D_Inst --> DB_Data

        T_L1 -->|查询标准| G_L2
        T_L1 -->|查询数据| D_Inst
        T_L2 -->|查询数据| D_Inst
        T_L3 -->|查询数据| D_Inst

        DB_Meta -.-> DB
        DB_Data -.-> DB


1. 整体架构与目录结构
----------------------

1.1 技术架构
^^^^^^^^^^^^

系统采用前后端分离的 Web 架构：

.. mermaid::
    :align: center

    graph LR
        F[前端 React<br/>ReactFlow] -->|HTTP/JSON| B[后端 FastAPI<br/>Python]
        B -->|SQLAlchemy| D[数据库 SQLite]

**前端职责**：
- 知识图谱可视化（React Flow）
- 动态参数配置界面
- 分析结果展示（ECharts）

**后端职责**：
- 知识图谱查询（节点、边、参数）
- 批次数据管理
- 分析工具调度
- RESTful API 提供

1.2 项目目录结构
^^^^^^^^^^^^^^^^

.. code-block:: text

   LSS/
   ├── backend/                # 后端代码
   │   ├── main.py            # FastAPI 主程序 (网关)
   │   ├── models.py          # 数据库模型
   │   ├── database.py        # 数据库配置 (基建)
   │   ├── ingestion.py       # 数据采集接口 (ETL漏斗)
   │   ├── seed.py            # 数据导入脚本 (构建者)
   │   │
   │   ├── core/              # LSS 工具箱 (算法大脑)
   │   │   ├── base.py        # BaseTool 基类
   │   │   ├── registry.py    # 工具注册中心
   │   │   ├── spc_tools.py   # SPC 分析工具
   │   │   ├── optimization.py # 优化工具 (规划中)
   │   │   └── risk_engine.py  # 风险分析 (规划中)
   │   │
   │   └── initial_data/      # 知识图谱源文件 (CSV)
   │       ├── master_flow.csv    # 总流程 (4个Block)
   │       ├── 01_PreTreatment/  # 前处理车间
   │       ├── 02_Extraction/    # 提取纯化车间
   │       ├── 03_Preparation/   # 制剂成型车间
   │       └── 04_Packaging/     # 内包外包车间
   │
   ├── frontend/              # 前端代码
   │   ├── src/
   │   │   ├── components/ProcessFlow.jsx  # 流程图组件
   │   │   ├── App.jsx
   │   │   └── main.jsx
   │   └── package.json
   │
   └── docs/                  # 文档
       ├── source/            # Sphinx 源文件
       └── build/             # 生成的 HTML


2. 数据模型设计
----------------

2.1 知识图谱模型 (静态骨架)
~~~~~~~~~~~~~~~~~~~~~~~~~~

知识图谱定义了系统的"法律与地图"，从 CSV 文件加载而来。

**L1 物理层 (ProcessNode)**

定义"前处理 → 提取 → 制剂"的拓扑结构。

.. list-table:: ProcessNode 属性
   :widths: 30 70
   :header-rows: 1

   * - 属性
     - 说明

   * - ``code``
     - 节点唯一编码（如 BLOCK_P, E04）

   * - ``name``
     - 节点显示名称

   * - ``node_type``
     - 节点类型：Block (车间) / Unit (设备)

   * - ``parent_id``
     - 父节点 ID，支持层级结构

**L2 感知层 (ParameterDef)**

定义每个节点上的参数（CPP/CQA）。

.. list-table:: ParameterDef 属性
   :widths: 30 70
   :header-rows: 1

   * - 属性
     - 说明

   * - ``code``
     - 参数编码（如 temp, pressure）

   * - ``role``
     - 参数角色：Input (输入) / Control (控制) / Output (输出)

   * - ``usl / lsl``
     - 规格上限/下限（用于 SPC 控制）

   * - ``target``
     - 目标值

   * - ``data_type``
     - 数据类型：Scalar (标量) / Spectrum (光谱)

**L3 逻辑层 (RiskNode / RiskEdge)**

定义故障树和因果关系（支持贝叶斯推理）。

.. list-table:: RiskNode 属性
   :widths: 30 70
   :header-rows: 1

   * - 属性
     - 说明

   * - ``category``
     - 风险类别：人/机/料/法/环

   * - ``base_probability``
     - 贝叶斯先验概率

知识图谱关系图：

.. mermaid::
    :align: center

    classDiagram
        class ProcessNode {
            +int id
            +str code
            +str name
            +int parent_id
            +str node_type
        }

        class ProcessEdge {
            +int id
            +str source_code
            +str target_code
            +str name
            +float loss_rate
        }

        class ParameterDef {
            +int id
            +int node_id
            +str code
            +str name
            +str role
            +float usl
            +float lsl
            +float target
        }

        class RiskNode {
            +int id
            +str code
            +str name
            +str category
            +float base_probability
        }

        class RiskEdge {
            +int id
            +str source_code
            +str target_code
            +float weight
        }

        ProcessNode "1" --> "many" ParameterDef : 包含
        ProcessNode "1" --> "many" ProcessNode : 父子关系
        ProcessNode --> ProcessEdge : 连接
        RiskNode --> RiskEdge : 关联
        RiskNode --> ParameterDef : 触发


2.2 生产数据模型 (动态血肉)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

生产数据来自实时采集，存储在 SQLite 数据库中。

**批次索引表 (Batch)**

生产任务的"户口本"，支持增量更新。

.. list-table:: Batch 属性
   :widths: 30 70
   :header-rows: 1

   * - 属性
     - 说明

   * - ``id``
     - 批次号（主键）

   * - ``product_name``
     - 产品名称（如"稳心颗粒"）

   * - ``start_time``
     - 开始时间

   * - ``status``
     - 批次状态（Running / Completed）

**测量流水表 (Measurement)**

时序数据的"大仓库"，所有测量数据的统一存储。

.. list-table:: Measurement 属性
   :widths: 30 70
   :header-rows: 1

   * - 属性
     - 说明

   * - ``batch_id``
     - 所属批次（外键）

   * - ``node_code``
     - 工序节点编码（关联知识图谱）

   * - ``param_code``
     - 参数编码（关联知识图谱）

   * - ``value``
     - 测量值（浮点数）

   * - ``timestamp``
     - 测量时间戳

   * - ``source_type``
     - 数据来源：HISTORY / SIMULATION / SENSOR

生产数据关系图：

.. mermaid::
    :align: center

    classDiagram
        class Batch {
            +str id
            +str product_name
            +datetime start_time
            +str status
        }

        class Measurement {
            +int id
            +str batch_id
            +str node_code
            +str param_code
            +float value
            +datetime timestamp
            +str source_type
        }

        Batch "1" --> "many" Measurement : 包含


3. 工艺流程层级结构
------------------

3.1 四大车间层级
~~~~~~~~~~~~~~~~

.. mermaid::
    :align: center

    graph TB
        subgraph 四大车间
            B1[BLOCK_P<br/>前处理车间]
            B2[BLOCK_E<br/>提取纯化车间]
            B3[BLOCK_C<br/>制剂成型车间]
            B4[BLOCK_B<br/>内包外包车间]
        end

        B1 --> B2
        B2 --> B3
        B3 --> B4

3.2 前处理车间设备示例
~~~~~~~~~~~~~~~~~~~~~~

以前处理车间为例，展示 CSV 数据文件的实际结构。

**节点定义 (nodes.csv)**

.. code-block:: text

    code,name,type
    P01_IN,原料入库,Unit
    P02_OUT,库存出库(AGV),Unit
    P03_WEIGH1,称重1 (P3电子秤),Unit
    P04_CRUSH,粉碎 (P4粉碎机),Unit
    P05_WEIGH2,称重2 (P5电子秤),Unit
    P_ENV,前处理环境监测,Unit

**流向定义 (flows.csv)**

.. code-block:: text

    source,target,name
    P01_IN,P02_OUT,库存管理
    P02_OUT,P03_WEIGH1,原料领用
    P03_WEIGH1,P04_CRUSH,三七/琥珀投料
    P04_CRUSH,P05_WEIGH2,粉末收集
    P05_WEIGH2,BLOCK_E,合格粉末去提取

**参数定义示例 (params.csv)**

.. code-block:: text

    node,param,name,role,unit,usl,lsl,target
    P03_WEIGH1,w_sanqi,三七重量,Input,kg,102,98,100
    P03_WEIGH1,w_huangjing,黄精重量,Input,kg,28,26,27
    P05_WEIGH2,heavy_metal,重金属残留量,Output,ppm,10,,,
    P05_WEIGH2,c_sanqi_r1,三七皂苷R1含量,Output,mg/g,0.8,0.5,,
    P_ENV,env_temp,洁净区温度,Control,℃,26,18,22

**设备流程图**：

.. mermaid::
    :align: center

    graph TB
        B1[BLOCK_P<br/>前处理车间] --> P01[P01_IN<br/>原料入库]
        P01 --> P02[P02_OUT<br/>库存出库]
        P02 --> P03[P03_WEIGH1<br/>称重1]
        P03 --> P04[P04_CRUSH<br/>粉碎机]
        P04 --> P05[P05_WEIGH2<br/>称重2]
        P05 --> E[去提取车间]

        B1 --> P_ENV[P_ENV<br/>环境监测]

3.3 其他车间
^^^^^^^^^^^^

其他车间（提取纯化、制剂成型、内包外包）的结构类似，通过 CSV 文件定义：
- 每个车间有独立的文件夹：``02_Extraction/``, ``03_Preparation/``, ``04_Packaging/``
- 文件夹内包含 ``nodes.csv``, ``flows.csv``, ``params.csv``
- 通过 ``seed.py`` 统一加载到数据库


4. 数据流转全流程
------------------

4.1 知识图谱构建流程
~~~~~~~~~~~~~~~~~~~~

.. mermaid::
    :align: center

    sequenceDiagram
        participant CSV as initial_data/<br/>CSV文件
        participant Seed as seed.py<br/>构建脚本
        participant KG as meta_*<br/>知识图谱表

        CSV->>Seed: 读取 CSV
        Seed->>Seed: 数据验证<br/>类型转换
        Seed->>KG: 写入 ProcessNode
        Seed->>KG: 写入 ParameterDef
        Seed->>KG: 写入 RiskNode
        Note over KG: 静态配置完成

**关键点**：
- 知识图谱只构建一次（系统初始化时）
- 数据来源：``backend/initial_data/`` 文件夹中的 CSV 文件
- 修改图谱需要重新运行 ``python seed.py``

4.2 生产数据采集流程
~~~~~~~~~~~~~~~~~~~~

.. mermaid::
    :align: center

    sequenceDiagram
        participant Source as 数据源<br/>(Excel/PLC/模拟)
        participant Ingestor as DataIngestor<br/>ETL适配器
        participant Batch as data_batches<br/>批次索引
        participant Meas as data_measurements<br/>测量流水
        participant KG as 知识图谱<br/>参数标准

        Source->>Ingestor: 原始数据
        Ingestor->>Batch: 查询批次是否存在

        alt 批次不存在
            Ingestor->>Batch: Auto-Create<br/>(自动创建)
        end

        Ingestor->>KG: 查询参数标准<br/>(USL/LSL)
        KG-->>Ingestor: 返回规格

        Ingestor->>Meas: 写入标准化数据<br/>(batch_id+node_code+param_code+value)

        Note over Ingestor,Meas: 支持增量更新

**关键特性**：

**Auto-Create Batch**：自动创建批次

.. code-block:: python

   ingestor.ingest_single_point(
       batch_id="BATCH_001",  # 首次使用时自动创建
       node_code="E04",
       param_code="temp",
       value=85.5,
       source="SENSOR"
   )

**增量更新**：同一批次追加数据

.. code-block:: python

   # 第一次写入 - 创建批次
   ingestor.ingest_single_point("BATCH_001", "E04", "temp", 85.0, "SENSOR")

   # 第二次写入 - 追加数据
   ingestor.ingest_single_point("BATCH_001", "E04", "temp", 86.0, "SENSOR")

**多源数据统一**：支持 HISTORY, SIMULATION, SENSOR

4.3 分析工具调用流程
~~~~~~~~~~~~~~~~~~~~~

.. mermaid::
    :align: center

    sequenceDiagram
        participant Front as 前端界面
        participant API as FastAPI
        participant Tool as LSS工具箱
        participant Data as data_*/<br/>生产数据
        participant KG as meta_*/<br/>知识图谱

        Front->>API: 请求分析<br/>(工具名+批次+参数)
        API->>Tool: 调用工具.run()

        Tool->>Data: 查询测量数据
        Data-->>Tool: 返回时序数据

        Tool->>KG: 查询参数标准
        KG-->>Tool: 返回规格(USL/LSL)

        Tool->>Tool: 执行分析算法<br/>(SPC/风险/优化)

        Tool-->>API: 返回结果+图表
        API-->>Front: JSON响应

**示例：SPC 分析流程**

1. 定义（Define）：管理员在 CSV 中定义 `提取温度` 规格为 80-90
2. 采集（Measure）：传感器收到 `Batch001, Temp=95`，自动写入数据库
3. 分析（Analyze）：

   - SPC 工具查询数据得到 `95`

   - 查询知识图谱得到标准 `90`

   - 计算得出 `Out of Spec` (超标)
4. 改进（Improve）：触发风险工具，弹窗提示异常


5. 存储架构对比
----------------

5.1 知识图谱存储
~~~~~~~~~~~~~~~~

.. list-table:: meta_ 表结构（CSV 加载）
   :widths: 25 50 25
   :header-rows: 1

   * - 表名
     - 用途
     - 对应模型

   * - ``meta_process_nodes``
     - 工序节点 (Block/Unit)
     - :py:class:`~models.ProcessNode`

   * - ``meta_process_flows``
     - 工艺流向连线
     - :py:class:`~models.ProcessEdge`

   * - ``meta_parameters``
     - 参数定义 (SPC控制)
     - :py:class:`~models.ParameterDef`

   * - ``meta_risk_nodes``
     - 风险节点 (故障树)
     - :py:class:`~models.RiskNode`

   * - ``meta_risk_edges``
     - 风险关系 (贝叶斯)
     - :py:class:`~models.RiskEdge`

**特点**：
- 数据来源：CSV 文件（``initial_data/`` 文件夹）
- 更新频率：低（系统初始化或工艺变更时）
- 数据量：小（几千行）
- 查询模式：频繁读取，极少修改

5.2 生产数据存储
~~~~~~~~~~~~~~~~

.. list-table:: data_ 表结构（实时采集）
   :widths: 25 50 25
   :header-rows: 1

   * - 表名
     - 用途
     - 对应模型

   * - ``data_batches``
     - 批次管理 (户口本)
     - :py:class:`~models.Batch`

   * - ``data_measurements``
     - 测量数据 (流水账)
     - :py:class:`~models.Measurement`

**特点**：
- 数据来源：实时采集（Excel/PLC/仿真）
- 更新频率：高（每秒多次）
- 数据量：大（历史累积）
- 查询模式：批量查询统计分析

5.3 区别总结
~~~~~~~~~~~~

.. list-table:: 知识图谱 vs 生产数据
   :widths: 20 30 30
   :header-rows: 1

   * - 维度
     - 知识图谱
     - 生产数据

   * - **本质**
     - 静态配置
     - 动态测量

   * - **来源**
     - CSV 文件
     - 实时采集

   * - **更新**
     - 工艺变更时
     - 持续增量

   * - **存储**
     - SQLite 表
     - SQLite 表

   * - **用途**
     - 定义标准
     - 记录事实


6. LSS 工具箱架构概览
---------------------

工具按**分析深度**分为四层，对应 LSS DMAIC 改进循环。

6.1 工具分类体系
~~~~~~~~~~~~~~~~

**第一层：描述性统计 (Descriptive)**

用途：回答"发生了什么？"

- SPC 统计过程控制（已实现）
- Pareto 帕累托图（规划中）
- Histogram 直方图（规划中）

**第二层：诊断性分析 (Diagnostic)**

用途：回答"为什么会发生？"

- Correlation 相关性分析（规划中）
- ANOVA 方差分析（规划中）
- FTA 故障树分析（规划中）

**第三层：预测性分析 (Predictive)**

用途：回答"将来会发生什么？"

- Bayesian Network 贝叶斯推理（规划中）
- Time Series 时序预测（规划中）
- Regression 回归分析（规划中）

**第四层：指导性优化 (Prescriptive)**

用途：回答"怎么做最好？"

- NSGA-II 多目标优化（规划中）
- DOE 实验设计（规划中）
- Recommendation 参数推荐（规划中）

6.2 设计模式
~~~~~~~~~~~~

.. mermaid::
    :align: center

    classDiagram
        class BaseTool {
            <<abstract>>
            +name: str
            +category: str
            +run(data, config) dict
        }

        class SPCToolbox {
            +name: "SPC 分析"
            +category: "Descriptive"
        }

        class ToolRegistry {
            -_tools: dict
            +register(key, tool)
            +get_tool(key) BaseTool
        }

        BaseTool <|-- SPCToolbox
        ToolRegistry --> BaseTool : 管理工具

详细的使用示例和开发指南请参考 :doc:`backend`。
