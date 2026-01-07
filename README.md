# LSS - 药品制造智能工艺指挥系统

**Update**: 2025年1月
**版本**: v2.0 - 智能指挥系统

基于知识图谱的药品制造工艺仿真与优化平台，从"精益六西格玛分析工具"升级为"AI黑带大脑"智能指挥系统。

---

## 系统概览

LSS v2.0 通过 IDEF0 层级建模方法，将药品制造过程分解为：
- **Block (区块)**: 四大车间（前处理、提取纯化、制剂成型、内包外包）
- **Unit (单元)**: 每个车间内的具体设备
- **Parameter (参数)**: 每个设备的工艺参数（控制、输出、输入）

**核心创新**: 双频输出机制
- **高频输出**: 每日指令给操作层（操作工、QA、班长）
- **低频输出**: 周报洞察给决策层（厂长、经理）

从"生成报告"到"推送任务"的完整升级。

---

## 技术栈

**后端**:
- FastAPI (Web框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- pandas, numpy, scipy (数据分析)
- pydantic (数据验证)
- networkx (图论分析)
- pgmpy (贝叶斯网络)
- pymoo (多目标优化)

**前端**:
- React 19.2.0 + Vite 7.2.4
- React Flow 11.11.4 (图谱可视化)
- Ant Design 6.1.3 (UI组件)
- @ant-design/icons 6.1.0 (图标库)
- ECharts 6.0.0 (数据可视化)
- echarts-for-react 3.0.5 (ECharts React封装)
- axios 1.13.2 (HTTP客户端)

---

## 快速启动

### 1. 环境验证 (推荐)

```bash
./verify_system.sh
```

自动检查 Python/Node.js 环境、依赖安装、数据库配置等。

### 2. 后端启动

```bash
cd backend
conda activate med
pip install -r requirements.txt  # 首次运行，安装所有依赖
python main.py
```

服务地址：`http://127.0.0.1:8000`
API文档：`http://127.0.0.1:8000/docs`

**依赖说明**:
- fastapi - Web框架
- uvicorn - ASGI服务器
- sqlalchemy - ORM
- pandas - 数据分析
- numpy - 数值计算
- scipy - 科学计算
- pydantic - 数据验证
- networkx - 图论分析
- pgmpy - 贝叶斯网络
- pymoo - 多目标优化

### 3. 前端启动

```bash
cd frontend
# 确保使用 Node.js 20.19+ (Vite 7.2.4 要求)
source ~/.nvm/nvm.sh  # 如果使用 nvm
nvm use 20
npm install          # 首次运行，安装所有依赖
npm run dev
```

访问地址：`http://localhost:5173`

**依赖说明**:
- react 19.2.0 - UI框架
- react-dom 19.2.0 - React DOM
- vite 7.2.4 - 构建工具
- antd 6.1.3 - UI组件库
- @ant-design/icons 6.1.0 - 图标库
- reactflow 11.11.4 - 流程图组件
- echarts 6.0.0 - 图表库
- echarts-for-react 3.0.5 - ECharts React封装
- axios 1.13.2 - HTTP客户端

---

## 前端交互指南

### 驾驶舱布局

```
┌──────────────────────────────────────────────────────┐
│  🧪 稳心颗粒 - 智能工艺指挥台                        │
│  [仿真/实时] [系统状态] [重连]                       │
├──────────────────────────┬───────────────────────────┤
│                          │                           │
│  左侧：工艺流程图 (70%)  │  右侧：控制台 (30%)      │
│  · 点击区块展开/折叠     │  ┌──────────────────────┐│
│  · 双击节点配置/查看     │  │ 上半部分：监控面板   ││
│  · 右键节点查看风险      │  │ 下半部分：指令列表   ││
│                          │  └──────────────────────┘│
└──────────────────────────┴───────────────────────────┘
```

### 仿真模式 (默认)

- **点击区块节点** (如"提取车间"): 展开/折叠子节点
- **双击 Unit 节点** (如"E03 投料站"): 打开参数配置弹窗
  - Input 参数 (橙色): 物料输入，可编辑
  - Control 参数 (蓝色): 工艺控制，可编辑
  - Output 参数 (绿色): 质量输出，自动计算
- **右键点击 Unit 节点**: 打开风险分析面板

### 实时监控模式

- **切换开关**: 顶部切换到"实时"
- **双击节点**: 查看监控面板 (只读)
- **节点颜色**: 根据实时 Cpk 变化
  - 🟢 绿色：Cpk ≥ 1.33 (稳定)
  - 🟡 黄色：0.8 ≤ Cpk < 1.33 (警告)
  - 🔴 红色：Cpk < 0.8 (失控)

### 指令系统

右下角显示系统自动生成的工艺指令：
- 按优先级排序 (CRITICAL > HIGH > MEDIUM > LOW)
- 点击"执行"按钮标记为进行中
- 点击"完成"按钮填写反馈

---

## 测试指令功能

### 生成测试指令

```bash
cd backend
python demo_commander.py
```

### 预期输出

```
📊 [数据分析] 发现异常：
  - 批次: BATCH-001
  - 工序: E04 醇提罐
  - 问题: Cpk = 0.85

✅ 已生成指令：

【Operator】
  检测到E04 醇提罐温度异常（当前85.5℃），
  建议将蒸汽阀开度从50%调至45%

【QA】
  E04 醇提罐温度Cpk=0.85低于临界值1.33，
  请对批次BATCH-001启动偏差调查流程
```

### 前端验证

1. 刷新浏览器页面
2. 查看右下角指令列表
3. 点击"执行"按钮测试

---

## 项目结构

```
LSS/
├── backend/                # 后端代码
│   ├── core/              # 核心抽象层
│   ├── analysis/          # 智能编排层 ⭐
│   ├── tools/             # 分析工具 (SPC/诊断/预测/优化)
│   ├── data/              # 数据访问层
│   ├── agent/             # LLM集成 (未来)
│   ├── models.py          # 数据库模型
│   ├── main.py            # FastAPI应用
│   └── initial_data/      # 知识图谱源文件 (CSV)
│
├── frontend/              # 前端代码
│   └── src/
│       ├── components/
│       │   ├── ProcessFlow.jsx   # 工艺流程图
│       │   ├── MonitorPanel.jsx  # 实时监控面板 ⭐
│       │   └── ActionList.jsx    # 待办指令列表 ⭐
│       └── App.jsx        # 驾驶舱布局
│
├── verify_system.sh       # 系统验证脚本
├── README.md              # 本文件
├── DEVELOPMENT_LOG.md     # 框架梳理与开发日志 ⭐
└── QUICK_START.md         # 快速启动指南
```

---

## 核心功能模块

### 1. 知识图谱管理

三层建模结构：
- **L1 物理层** (ProcessNode): 定义"前处理 → 提取 → 制剂"的拓扑结构
- **L2 感知层** (ParameterDef): 定义每个节点的参数 (CPP/CQA)
- **L3 逻辑层** (RiskNode/RiskEdge): 定义故障树和因果关系

### 2. 智能编排层 ⭐

- **BlackBeltCommander**: 多维度数据分析 (批次/工序/时间/人员/车间)
- **IntelligentCommander**: 从分析到行动的桥梁 (生成每日指令)
- **DecisionEngine**: 可插拔决策引擎 (规则 → LLM → 混合)

### 3. 双频输出 ⭐

- **高频**: 每日指令给操作层
- **低频**: 周报洞察给决策层

### 4. LSS 工具箱

按 DMAIC 改进循环分为四层：

**第一层：描述性统计** (✅ 已实现4个工具)
- SPC控制图 - 过程能力分析、Cpk计算、Nelson Rules违规检测
- 帕累托图 - 识别"关键少数"问题，80/20法则分析
- 直方图 - 频数分布、正态性检验、偏度和峰度
- 箱线图 - 多车间对比、异常值识别

**第二层：诊断性分析** (规划中)
- 故障树分析 (FTA)
- 鱼骨图
- 相关性分析
- 方差分析 (ANOVA)

**第三层：预测性分析** (规划中)
- 贝叶斯网络
- 时序预测 (ARIMA)
- 多元回归

**第四层：指导性优化** (规划中)
- NSGA-II 多目标优化
- DOE 实验设计
- 响应曲面法 (RSM)

---

## API 端点

### 指令相关 (新增)

```
GET  /api/instructions              # 获取指令列表
POST /api/instructions/{id}/read    # 标记为进行中
POST /api/instructions/{id}/done    # 标记为完成
```

### 监控相关 (新增)

```
GET /api/monitor/node/{node_code}  # 获取节点监控数据
GET /api/monitor/latest             # 获取所有节点最新状态
```

### 分析相关 (已有)

```
POST /api/analysis/person           # 按人员分析
POST /api/analysis/batch            # 按批次分析
POST /api/analysis/process          # 按工序分析
POST /api/analysis/workshop         # 按车间分析
POST /api/analysis/time             # 按时间分析
```

### 图谱相关 (已有)

```
GET /api/graph/structure            # 获取流程图结构
GET /api/graph/nodes/{code}/risks   # 获取节点风险
```

---

## 常见问题

### 后端启动失败

确保已安装所有依赖：
```bash
pip install fastapi uvicorn sqlalchemy
```

### 前端显示"离线"

检查后端是否正常运行：`http://127.0.0.1:8000/docs`

### 指令列表是空的

运行测试脚本生成数据：
```bash
cd backend
python demo_commander.py
```

---

## 详细文档

- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)**: 框架梳理与开发日志 ⭐ (推荐阅读)
- **[QUICK_START.md](QUICK_START.md)**: 快速启动指南
- **[CHECKLIST.md](CHECKLIST.md)**: 前后端联调检查清单

---

## 开发路线图

- ✅ **v1.0**: 基础平台 (三层建模、图谱可视化、SPC分析)
- ✅ **v2.0**: 智能指挥系统 (双频输出、指令推送、监控面板)
- ⏳ **v2.1**: SCADA实时数据接入
- ⏳ **v2.2**: LLM自然语言生成
- ⏳ **v3.0**: 预测性指令与自动优化

---

**总结**: 从"分析工具"到"指挥系统"的完整升级，实现了真正的 **AI黑带大脑**。
