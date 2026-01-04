# LSS 后端目录结构说明

## 概述

后端代码已重新组织为清晰的分层架构，分离关注点，使代码更易维护和扩展。

```
backend/
├── core/                    # 核心抽象和基础类
│   ├── base.py             # BaseTool 抽象基类
│   ├── registry.py         # ToolRegistry 工具注册中心
│   └── __init__.py
│
├── analysis/               # 智能编排层
│   ├── orchestrator.py     # BlackBeltCommander - 主入口
│   ├── workflows.py        # AnalysisWorkflow - 标准化分析流程
│   ├── decision_engine.py  # DecisionEngine - 可插拔决策逻辑
│   ├── report_formatter.py # ReportFormatter - 报告生成
│   └── __init__.py
│
├── tools/                  # 分析工具（按类别组织）
│   ├── descriptive/        # 描述性分析工具
│   │   ├── spc.py         # 统计过程控制
│   │   └── __init__.py
│   ├── diagnostic/         # 诊断性分析工具（未来）
│   ├── predictive/         # 预测性分析工具（未来）
│   └── prescriptive/       # 规范性分析工具（未来）
│
├── data/                   # 数据访问层
│   ├── providers.py        # 多维度数据提供者
│   └── __init__.py
│
├── agent/                  # 未来 LLM 集成
│   └── __init__.py
│
├── api/                    # API 层（未来）
│
├── main.py                 # FastAPI 应用 & REST 端点
├── models.py              # SQLAlchemy ORM 模型
├── database.py            # 数据库连接和会话管理
├── test_orchestrator.py   # 编排层测试套件
└── requirements.txt       # Python 依赖
```

## 各层职责

### 1. **core/** - 核心抽象
- **用途**: 整个系统使用的基础抽象
- **包含**: 基类、接口、注册表
- **依赖**: 最少的外部依赖
- **稳定性**: 高 - 此处的变更会影响整个系统

### 2. **analysis/** - 智能编排层
- **用途**: 协调分析工作流和决策逻辑
- **核心类**:
  - `BlackBeltCommander`: 主编排器，提供5种分析方法
  - `DecisionEngine`: 可插拔决策逻辑（规则 → LLM）
  - `AnalysisWorkflow`: 标准化分析流程
  - `ReportFormatter`: 将结果转换为结构化报告
- **依赖**: core/, data/
- **稳定性**: 中 - 随分析需求演进

### 3. **tools/** - 分析工具
- **用途**: 按类别组织的独立分析算法
- **分类**:
  - **descriptive**: SPC、统计、数据摘要
  - **diagnostic**: 根本原因分析、故障树（未来）
  - **predictive**: 趋势预测、异常检测（未来）
  - **prescriptive**: 优化建议（未来）
- **依赖**: core/
- **稳定性**: 低 - 频繁添加新工具

### 4. **data/** - 数据访问层
- **用途**: 跨多个维度的统一数据访问
- **核心类**:
  - `DataProvider`: 抽象基类
  - `PersonDataProvider`: 按操作工查询
  - `BatchDataProvider`: 按批次查询
  - `ProcessDataProvider`: 按工序节点查询
  - `WorkshopDataProvider`: 按车间/区块查询
  - `TimeDataProvider`: 按时间范围查询
  - `DataContext`: 统一查询结果结构
- **依赖**: models.py, database.py
- **稳定性**: 中 - 随数据模型变更演进

### 5. **agent/** - LLM 集成（未来）
- **用途**: LLM 智能体的工具包装和接口
- **计划内容**:
  - 函数调用模式
  - 工具输出格式化
  - 智能体编排逻辑
- **依赖**: tools/, analysis/
- **稳定性**: 高波动性 - 实验性

## 导入模式

### 从外部代码（main.py, tests）:
```python
# 智能编排层
from analysis import BlackBeltCommander, ReportFormatter

# 数据访问
from data import query_data_by_dimension, DataContext

# 工具
from tools.descriptive import SPCTool
```

### 在 analysis 层内部:
```python
# 本地导入（同目录）
from .decision_engine import DecisionEngine
from .workflows import WorkflowRegistry

# 跨层导入
from data import DataProviderFactory, DataContext
from core.registry import registry
```

### 在 tools 层:
```python
# 核心抽象
from core.base import BaseTool
from core.registry import registry
```

## 关键设计决策

### 1. 关注点分离
每层都有清晰、单一的职责：
- **core/**: 仅包含抽象
- **analysis/**: 业务逻辑和编排
- **tools/**: 分析算法
- **data/**: 数据访问

### 2. 依赖流向
```
main.py → analysis/ → data/
              ↓
           tools/ → core/
```

### 3. 可扩展性
- 添加新工具：在相应的 tools/ 子目录创建文件
- 添加新分析维度：扩展 data/ 和 analysis/
- 切换决策引擎：使用 DecisionEngineFactory（无需代码更改）

### 4. 面向未来
- **agent/** 目录为 LLM 集成做准备
- **tools/** 按分析类型分类
- 空的 **api/** 目录用于潜在的 API 层分离

## 迁移说明

所有文件已从 `core/` 迁移到新位置：

| 旧路径 | 新路径 |
|----------|----------|
| core/orchestrator.py | analysis/orchestrator.py |
| core/workflows.py | analysis/workflows.py |
| core/decision_engine.py | analysis/decision_engine.py |
| core/report_formatter.py | analysis/report_formatter.py |
| core/data_providers.py | data/providers.py |
| core/spc_tools.py | tools/descriptive/spc.py |

所有导入语句已相应更新。
