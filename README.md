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
  - 父子关系：支持层级展开

- **L2 感知层 (ParameterDef)**: 定义每个节点的参数（CPP/CQA）
  - Input：输入参数
  - Control：控制参数
  - Output：输出参数
  - 规格限：USL/LSL/Target

- **L3 逻辑层 (RiskNode/RiskEdge)**: 定义故障树和因果关系
  - 风险分类：人/机/料/法/环
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

## API 端点

### 获取图谱结构
- **GET** `/api/graph/structure`
- 返回完整的知识图谱结构，包括所有节点和边

### 获取节点参数
- **GET** `/api/graph/nodes/{node_id}/parameters`
- 返回指定节点的所有参数定义

### 仿真接口
- **POST** `/api/simulate`
- 执行工艺参数仿真计算

### 工具箱接口
- **POST** `/api/tools/run/{tool_name}`
- 运行指定的分析工具

## 开发文档

详细的系统架构和开发指南请查看 [docs/source/](docs/source/)：

- [architecture.rst](docs/source/architecture.rst) - 系统架构详解
- [backend.rst](docs/source/backend.rst) - 后端开发指南
- [frontend.rst](docs/source/frontend.rst) - 前端开发指南
- [todo.rst](docs/source/todo.rst) - 开发路线图

## 开发路线图

- ✅ 阶段 1: 核心功能（数据库模型、知识图谱可视化、CSV 数据导入）
- 🚧 阶段 2: 仿真引擎（真实仿真算法、多参数耦合、结果可视化）
- 📊 阶段 3: SPC 统计分析（实时数据采集、控制图、过程能力分析）
- ⚠️ 阶段 4: 风险分析（故障树可视化、贝叶斯网络推理）
- 🎯 阶段 5: 优化模块（参数优化、多目标优化）

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
