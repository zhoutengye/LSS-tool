# LSS - 药品制造工艺仿真系统

Update: Zhouteng Ye(December 31st, 2025)

基于知识图谱的药品制造工艺仿真与优化平台，采用元数据驱动的三位一体架构设计。

## 系统概览

LSS 系统通过 IDEF0 层级建模方法，将药品制造过程分解为：
- **Block (区块)**: 四大车间（前处理、提取纯化、制剂成型、内包外包）
- **Unit (单元)**: 每个车间内的具体设备
- **Parameter (参数)**: 每个设备的工艺参数（控制、输出、输入）

### 核心功能

- 知识图谱可视化（React Flow）
- 动态参数配置与仿真
- 实时数据监控与批次管理
- LSS 超级工具箱（SPC、风险分析、优化）

### 技术栈

**后端**:
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- pandas, numpy, scipy (数据分析)
- networkx (图论分析)
- pgmpy (贝叶斯网络)
- pymoo (多目标优化)

**前端**:
- React 19 + Vite
- React Flow (图谱可视化)
- Ant Design 6 (UI 组件)

## 快速开始

### 1. 前置要求

- **Python**: 3.9+ (推荐使用 Conda 管理)
- **Node.js**: v20+ (推荐使用 `nvm` 管理)

### 2. 后端配置

```bash
# 进入后端目录
cd backend

# 创建/激活 Conda 环境
conda create -n med python=3.9
conda activate med

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（导入知识图谱）
python seed.py

# 启动后端服务
uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 访问地址: http://127.0.0.1:8000
# API 文档: http://127.0.0.1:8000/docs
```

### 3. 前端配置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 访问地址: http://localhost:5173
```

### 前端交互指南

#### 1. 流程图导航

- **点击区块节点**（如"提取车间"）: 展开/折叠子节点
- **双击 Unit 节点**（如"E03 投料站"）: 打开参数配置弹窗
- **右键点击 Unit 节点**: 打开风险分析面板

#### 2. 参数配置

双击节点后，可以修改工艺参数：

- **Input 参数**（橙色标签）: 物料输入，可编辑
- **Control 参数**（蓝色标签）: 工艺控制，可编辑
- **Output 参数**（绿色标签）: 质量输出，自动计算，不可编辑

配置完成后点击"确定"，系统会：
1. 调用后端仿真接口
2. 计算输出结果（如得率）
3. 更新节点显示
4. 得率 < 90% 时显示红色边框警告

#### 3. 风险分析

右键点击任意 Unit 节点，查看该工序的潜在风险：

- **Top 事件**（红色）: 顶层故障（如"提取过程故障"）
- **Category 因素**（蓝色/绿色等）: 中间层分类（如"设备因素"、"物料因素"）
- **Basic 底事件**: 具体风险点，显示发生概率（如"温度传感器异常 2.0%"）

风险分类：
- 🔵 Equipment: 设备因素
- 🟢 Material: 物料因素
- 🟣 Human: 人员因素
- 🔵 Environment: 环境因素
- 🟠 Method: 方法/法规因素

#### 4. Resource 节点

环境监测节点（如 `P_ENV`）始终显示在区块上方，不参与展开/折叠操作。

## 项目结构

```
LSS/
├── backend/                # 后端代码
│   ├── main.py            # FastAPI 主程序
│   ├── models.py          # 数据库模型
│   ├── database.py        # 数据库配置
│   ├── ingestion.py       # 数据采集接口
│   ├── seed.py            # 数据导入脚本
│   ├── requirements.txt   # Python 依赖
│   │
│   ├── core/              # LSS 工具箱
│   │   ├── base.py        # BaseTool 基类
│   │   ├── registry.py    # 工具注册中心
│   │   ├── spc_tools.py   # SPC 分析工具
│   │   ├── optimization.py # 优化工具
│   │   └── risk_engine.py  # 风险分析
│   │
│   └── initial_data/      # 知识图谱源文件 (CSV)
│       ├── master_flow.csv    # 总流程
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
├── docs/                  # 文档
│   └── source/            # Sphinx 源文件
│       ├── index.rst
│       ├── architecture.rst
│       ├── backend.rst
│       ├── frontend.rst
│       └── todo.rst
│
├── .gitignore
└── README.md
```

## 主要功能模块

### 1. 知识图谱管理

系统采用三层建模结构：

- **L1 物理层 (ProcessNode)**: 定义"前处理 → 提取 → 制剂"的拓扑结构
  - Block（车间）：4 大车间
  - Unit（设备）：具体设备节点
  - Resource（资源）：环境监测等基础设施
  - 父子关系：支持层级展开

- **L2 感知层 (ParameterDef)**: 定义每个节点的参数（CPP/CQA）
  - Input：输入参数
  - Control：控制参数
  - Output：输出参数
  - 规格限：USL/LSL/Target

- **L3 逻辑层 (RiskNode/RiskEdge)**: 定义故障树和因果关系
  - 风险分类：人/机/料/法/环
  - 故障树层级：Top 事件 → Category 因素 → Basic 底事件
  - 贝叶斯先验概率：支持风险推理计算

### 2. 数据采集与批次管理

- **Auto-Create Batch**: 首次写入新批次号时自动创建 Batch 记录
- **增量更新**: 同一批次后续写入自动追加
- **多源数据**: 支持 HISTORY（历史）、SIMULATION（仿真）、SENSOR（实时）

### 3. LSS 工具箱

按 DMAIC 改进循环分为四层：

- **第一层：描述性统计** - 回答"发生了什么？"
  - SPC 统计过程控制（已实现）
  - Pareto 帕累托图（规划中）
  - Histogram 直方图（规划中）

- **第二层：诊断性分析** - 回答"为什么会发生？"
  - Correlation 相关性分析（规划中）
  - ANOVA 方差分析（规划中）
  - FTA 故障树分析（规划中）

- **第三层：预测性分析** - 回答"将来会发生什么？"
  - Bayesian Network 贝叶斯网络（规划中）
  - Time Series 时序预测（规划中）
  - Regression 回归分析（规划中）

- **第四层：指导性优化** - 回答"怎么做最好？"
  - NSGA-II 多目标优化（规划中）
  - DOE 实验设计（规划中）

## CSV 数据结构规范

每个车间的数据存储在独立文件夹中，包含以下 CSV 文件：

### 1. nodes.csv - 节点定义

定义车间内的所有节点（Unit/Resource）。

```csv
code,name,type
P01_IN,原料入库(AGV),Unit
P02_OUT,库存出库(AGV),Unit
P_ENV,前处理环境监测,Resource
```

**字段说明**:
- `code`: 节点代码（唯一标识符）
- `name`: 节点名称
- `type`: 节点类型
  - `Block`: 车间层级（仅在 master_flow.csv 中定义）
  - `Unit`: 工艺设备单元
  - `Resource`: 基础设施（如环境监测）

### 2. params.csv - 参数定义

定义每个节点的工艺参数（CPP/CQA）。

```csv
node,param,name,role,unit,target,usl,lsl,is_material,data_type
E03,w_sanqi,三七投料量,Input,g,100,102,98,TRUE,Scalar
E03,temp,提取温度,Control,℃,85,90,80,FALSE,Scalar
E21,yield,浸膏得率,Output,%,98,100,95,TRUE,Scalar
```

**字段说明**:
- `node`: 所属节点代码
- `param`: 参数代码（节点内唯一）
- `name`: 参数名称
- `role`: 参数角色
  - `Input`: 输入物料参数
  - `Control`: 工艺控制参数
  - `Output`: 质量输出参数
- `unit`: 计量单位
- `target`: 目标值
- `usl`: 上规格限
- `lsl`: 下规格限
- `is_material`: 是否为物料参数（TRUE/FALSE）
- `data_type`: 数据类型
  - `Scalar`: 标量值
  - `Spectrum`: 光谱/指纹图谱
  - `Image`: 图像数据
  - `grade`: 等级/分类

### 3. flows.csv - 管路连接

定义节点之间的物料流向关系（支持跨车间连接）。

```csv
source,target,name
P01_IN,P02_OUT,库存管理
P03_WEIGH1,E03,党参/甘松/黄精直接去投料
E21,C04,稠膏去制剂混合
```

**字段说明**:
- `source`: 源节点代码
- `target`: 目标节点代码
- `name`: 连线名称（物料描述）

**跨车间连接**:
- 支持直接连接到其他车间的 Unit 节点（如 `P05_WEIGH2 → C04`）
- 所有节点在导入时已创建，因此跨车间引用不会失败

### 4. risks.csv - 风险节点定义

定义故障树的风险节点（按车间组织）。

```csv
code,name,category,prob
EXT_FAIL,提取过程故障,Top,
EXT_FAC_E,提取设备因素,Equipment,
EXT_E1,温度传感器异常,Equipment,0.02
EXT_M1,药材掺有杂质,Material,0.05
EXT_H1,操作人员不熟练,Human,0.15
```

**字段说明**:
- `code`: 风险节点代码（前缀标识车间，如 `EXT_`=提取车间）
- `name`: 风险名称
- `category`: 风险分类
  - `Top`: 顶层故障事件
  - `Equipment`: 设备因素
  - `Material`: 物料因素
  - `Human`: 人员因素
  - `Environment`: 环境因素
  - `Method`: 方法/法规因素
- `prob`: 基础发生概率（0-1 之间的浮点数，空值表示未定义）

**故障树层级**:
```
Top 事件（如 EXT_FAIL）
  ├─ Category 因素（如 EXT_FAC_E）
  │   ├─ Basic 底事件（如 EXT_E1: 温度传感器异常, prob=0.02）
  │   └─ Basic 底事件（如 EXT_E2: 液位计故障, prob=0.01）
  ├─ Category 因素（如 EXT_FAC_M）
  └─ ...
```

### 5. risk_edges.csv - 风险因果关系

定义故障树中节点之间的因果连接。

```csv
source,target
EXT_E1,EXT_FAC_E
EXT_E2,EXT_FAC_E
EXT_FAC_E,EXT_FAIL
```

**字段说明**:
- `source`: 原因节点代码（子节点）
- `target`: 结果节点代码（父节点）

**边的方向**: 从底事件指向顶事件（如：`EXT_E1 → EXT_FAC_E → EXT_FAIL`）

### 数据导入逻辑

系统采用**两阶段导入策略**（`seed.py`）：

1. **Phase 1 - 构建节点**:
   - 读取所有车间的 `nodes.csv`
   - 创建所有 Block、Unit、Resource 节点
   - 此时跨车间引用的目标节点已存在

2. **Phase 2 - 填充细节**:
   - 读取 `params.csv`：为节点添加参数定义
   - 读取 `flows.csv`：建立管路连接（包括跨车间连接）
   - 读取 `risks.csv` + `risk_edges.csv`：构建故障树

**优势**:
- 支持任意复杂的跨车间物料流向
- 避免因节点不存在而导致的连线失败
- 易于扩展新车间

### 示例：添加新车间

1. 创建文件夹 `backend/initial_data/05_NewWorkshop/`
2. 编写 `nodes.csv`、`params.csv`、`flows.csv`
3. 如有风险分析，添加 `risks.csv`、`risk_edges.csv`
4. 在 `master_flow.csv` 中添加车间定义
5. 运行 `python seed.py` 重新导入

## API 端点

### 知识图谱接口

#### 获取图谱结构
- **GET** `/api/graph/structure`
- 返回完整的知识图谱结构，包括所有节点和边
- 响应示例：
  ```json
  {
    "nodes": [
      {"id": "1", "data": {"code": "E03", "name": "投料站", "type": "Unit"}, ...},
      {"id": "2", "data": {"code": "E04", "name": "提取罐1", "type": "Unit"}, ...}
    ],
    "edges": [
      {"source": "1", "target": "2", "label": "三七粉投料"}
    ]
  }
  ```

#### 获取节点参数
- **GET** `/api/graph/nodes/{node_code}/parameters`
- 返回指定节点的所有参数定义
- 响应示例：
  ```json
  [
    {"code": "w_sanqi", "name": "三七投料量", "role": "Input", "unit": "g", "target": 100, "usl": 102, "lsl": 98},
    {"code": "temp", "name": "提取温度", "role": "Control", "unit": "℃", "target": 85, "usl": 90, "lsl": 80}
  ]
  ```

### 风险分析接口

#### 获取完整故障树
- **GET** `/api/graph/risks/tree`
- 返回所有风险节点和因果关系边
- 响应示例：
  ```json
  {
    "risks": [
      {"id": 1, "code": "EXT_FAIL", "name": "提取过程故障", "category": "Top", "base_probability": null},
      {"id": 2, "code": "EXT_E1", "name": "温度传感器异常", "category": "Equipment", "base_probability": 0.02}
    ],
    "edges": [
      {"id": "r1", "source": "EXT_E1", "target": "EXT_FAC_E", "animated": true, "style": {"stroke": "#ff4d4f"}}
    ]
  }
  ```

#### 获取节点相关风险
- **GET** `/api/graph/nodes/{node_code}/risks`
- 返回指定工艺节点的相关风险
- 匹配规则：
  - `E*` 节点 → `EXT_*`, `CONC_*`, `PREC_*` 风险（提取车间）
  - `C*` 节点 → `GRAN_*` 风险（制剂车间）
- 响应示例：
  ```json
  {
    "risks": [
      {"code": "EXT_FAIL", "name": "提取过程故障", "category": "Top"},
      {"code": "EXT_E1", "name": "温度传感器异常", "category": "Equipment", "base_probability": 0.02}
    ]
  }
  ```

### 仿真接口

#### 执行工艺仿真
- **POST** `/api/simulate`
- 执行工艺参数仿真计算
- 请求体：
  ```json
  {
    "temperature": 85,
    "time": 120
  }
  ```
- 响应：
  ```json
  {
    "result_yield": 98.5,
    "result_quality": "A"
  }
  ```

### 工具箱接口

#### 运行分析工具
- **POST** `/api/tools/run/{tool_name}`
- 运行指定的 LSS 分析工具
- 可用工具：`spc_control_chart`, `pareto`, `correlation`, `doe`

## 开发文档

详细的系统架构和开发指南请查看 [docs/source/](docs/source/)：

- [architecture.rst](docs/source/architecture.rst) - 系统架构详解
- [backend.rst](docs/source/backend.rst) - 后端开发指南
- [frontend.rst](docs/source/frontend.rst) - 前端开发指南
- [todo.rst](docs/source/todo.rst) - 开发路线图

## 开发路线图

- ✅ **阶段 1: 核心功能**（已完成）
  - 数据库模型（三层架构：物理层、感知层、逻辑层）
  - 知识图谱可视化（React Flow）
  - CSV 数据导入（两阶段策略，支持跨车间连接）
  - 参数配置与仿真（基础版本）
  - 风险数据模型（故障树节点与边）

- ✅ **阶段 2: 风险分析**（已完成）
  - 故障树数据导入（提取、制剂车间）
  - 风险节点分类（人/机/料/法/环）
  - 前端风险面板（右键菜单 + Drawer 展示）
  - 节点风险匹配 API

- 🚧 **阶段 3: 仿真引擎**（开发中）
  - 真实仿真算法（多参数耦合模型）
  - 结果可视化（得率、质量等级）
  - 批次管理与数据采集

- 📊 **阶段 4: SPC 统计分析**（规划中）
  - 实时数据采集接口
  - 控制图（Xbar-R、P图、U图）
  - 过程能力分析（Cp、Cpk）
  - Pareto 帕累托图

- ⚠️ **阶段 5: 高级风险分析**（规划中）
  - 贝叶斯网络推理引擎
  - 动态风险评估
  - 风险预警系统

- 🎯 **阶段 6: 优化模块**（规划中）
  - NSGA-II 多目标优化
  - DOE 实验设计
  - 参数优化建议

## 常见问题

### 后端启动失败

确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### 前端连接后端失败

检查后端是否正常运行，并确认 CORS 配置正确。

### 数据库初始化

首次运行需要执行 `python seed.py` 导入知识图谱数据。
