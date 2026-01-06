# LSS 智能工艺指挥系统 - 框架梳理与开发日志

**更新时间**: 2025年1月
**版本**: v2.0 - 智能指挥系统
**作者**: University Team

---

## 📋 目录

- [系统概览](#系统概览)
- [后端架构](#后端架构)
- [前端架构](#前端架构)
- [双频输出机制](#双频输出机制)
- [开发日志](#开发日志)
- [快速启动](#快速启动)

---

## 系统概览

### 定位演进

**v1.0**: 精益六西格玛分析工具箱
**v2.0**: 智能工艺指挥系统（AI黑带大脑）

核心转变：从"生成报告"到"推送任务"

### 技术栈

**后端**:
- FastAPI (Web框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- pandas, numpy, scipy (数据分析)
- networkx (图论分析)
- pgmpy (贝叶斯网络)
- pymoo (多目标优化)

**前端**:
- React 19 + Vite
- React Flow (图谱可视化)
- Ant Design 6 (UI组件)
- ECharts (数据可视化)

### 核心创新

**IDEF0 三层建模**:
- **Block (区块)**: 4大车间
- **Unit (单元)**: 具体设备
- **Parameter (参数)**: CPP/CQA参数

**双频输出机制**:
- **高频**: 每日指令给操作层
- **低频**: 周报洞察给决策层

---

## 后端架构

### 目录结构

```
backend/
├── core/                    # 核心抽象层
│   ├── base.py             # BaseTool基类
│   └── registry.py         # 工具注册中心
│
├── analysis/               # 智能编排层 ⭐
│   ├── orchestrator.py     # BlackBeltCommander (黑带分析器)
│   ├── commander.py        # IntelligentCommander (智能指挥官)
│   ├── decision_engine.py  # DecisionEngine (决策引擎)
│   ├── workflows.py        # AnalysisWorkflow (工作流)
│   └── report_formatter.py # ReportFormatter (报告格式化)
│
├── tools/                  # 分析工具箱 ⭐
│   ├── descriptive/        # L1: 描述性统计 (7工具)
│   │   └── spc.py         # ✅ SPC工具 (已实现)
│   ├── diagnostic/         # L2: 诊断性分析 (6工具) ⏳
│   ├── predictive/         # L3: 预测性分析 (5工具) ⏳
│   └── prescriptive/       # L4: 规范性分析 (5工具) ⏳
│
├── data/                   # 数据访问层
│   └── providers.py        # 5种DataProvider
│
├── agent/                  # LLM集成 (未来)
│
├── models.py               # 数据模型
├── main.py                 # FastAPI应用
├── database.py             # 数据库配置
├── seed.py                 # 数据导入脚本
├── demo_commander.py       # 指挥官演示脚本
└── requirements.txt        # Python依赖
```

### 核心数据模型

#### 1. 物理层 (ProcessNode)

```python
class ProcessNode(Base):
    """工艺节点"""
    code: str              # 节点代码
    name: str              # 节点名称
    type: str              # Block/Unit/Resource
    parent_id: int         # 父节点ID (层级关系)
```

**节点类型**:
- **Block**: 车间层级 (前处理/提取/制剂/包装)
- **Unit**: 工艺设备 (投料站/提取罐/制粒机)
- **Resource**: 基础设施 (环境监测)

#### 2. 感知层 (ParameterDef)

```python
class ParameterDef(Base):
    """参数定义"""
    node_code: str         # 所属节点
    code: str              # 参数代码
    name: str              # 参数名称
    role: str              # Input/Control/Output
    unit: str              # 计量单位
    target: float          # 目标值
    usl: float             # 上规格限
    lsl: float             # 下规格限
```

**参数角色**:
- **Input**: 输入物料 (可编辑)
- **Control**: 工艺控制 (可编辑)
- **Output**: 质量输出 (自动计算)

#### 3. 逻辑层 (RiskNode/RiskEdge)

```python
class RiskNode(Base):
    """风险节点 (故障树)"""
    code: str              # 风险代码
    name: str              # 风险名称
    category: str          # Top/Equipment/Material/Human/Environment/Method
    base_probability: float # 基础概率
```

**故障树层级**:
```
Top 事件 (如 EXT_FAIL)
  ├─ Category 因素 (如 EXT_FAC_E)
  │   ├─ Basic 底事件 (如 EXT_E1: 温度传感器异常, prob=0.02)
  │   └─ Basic 底事件 (如 EXT_E2: 液位计故障, prob=0.01)
  └─ ...
```

#### 4. 对策库 (ActionDef) ⭐

```python
class ActionDef(Base):
    """对策方案定义 (OCAP)"""
    code: str                      # 对策代码
    name: str                      # 对策名称
    risk_code: str                 # 关联风险代码
    target_role: str               # 目标角色 (Operator/QA/TeamLeader/Manager)
    instruction_template: str      # 指令模板 (支持变量替换)
    priority: str                  # CRITICAL/HIGH/MEDIUM/LOW
    category: str                  # Equipment/Material/Method/Man/Environment
```

**示例**:
```csv
code,name,risk_code,target_role,instruction_template,priority
ACTION_E04_TEMP_HIGH,E04温度偏高-操作工对策,R_E04_TEMP_HIGH,Operator,"检测到{node_name}温度异常（当前{current_value}℃），建议将蒸汽阀开度从{current_valve}%调至{suggested_valve}%",HIGH
```

#### 5. 指令记录 (DailyInstruction) ⭐

```python
class DailyInstruction(Base):
    """每日指令记录"""
    target_date: str       # 针对哪一天
    role: str              # 目标角色
    content: str           # 指令内容 (自然语言)
    status: str            # Pending/Read/Done
    evidence: JSON         # 证据 (Cpk、风险概率等)
    feedback: str          # 执行反馈
    instruction_type: str  # tactical/strategic
```

**生命周期**:
```
Pending (待处理)
  ↓ 点击"执行"
Read (进行中)
  ↓ 点击"完成" + 填写反馈
Done (已完成)
```

#### 6. 业务数据层

```python
class Batch(Base):
    """生产批次"""
    batch_id: str
    product_name: str
    start_time: datetime
    end_time: datetime

class Measurement(Base):
    """测量数据"""
    batch_id: str
    node_code: str
    param_code: str
    value: float
    timestamp: datetime
    source: str            # HISTORY/SIMULATION/SENSOR
```

### 智能编排层

#### 1. BlackBeltCommander (黑带分析器)

**职责**: 多维度数据分析

```python
class BlackBeltCommander:
    def analyze_by_batch(self, batch_id: str) -> AnalysisReport:
        """按批次分析"""

    def analyze_by_process(self, node_code: str) -> AnalysisReport:
        """按工序分析"""

    def analyze_by_time(self, date_range: tuple) -> AnalysisReport:
        """按时间分析"""
```

**分析流程**:
```
数据获取 → SPC检测 → 故障树追溯 → 贝叶斯推演
```

**输出**: AnalysisReport
```python
{
    "dimension": "batch",
    "key": "BATCH-001",
    "critical_issues": [...],
    "warnings": [...],
    "insights": [...]
}
```

#### 2. IntelligentCommander (智能指挥官) ⭐

**职责**: 从分析到行动的桥梁

```python
class IntelligentCommander:
    def generate_daily_orders(self, target_date: str, dimensions: List[str]) -> Dict[str, List[Instruction]]:
        """生成每日指令 (核心入口)

        流程:
            1. 调用 BlackBeltCommander 进行多维度分析
            2. 提取 critical_issues 和 warnings
            3. 匹配 ActionDef (对策库)
            4. 填充模板，生成自然语言指令
            5. 按角色分组
            6. 保存到 DailyInstruction 表
        """

    def generate_weekly_insights(self, week_start: str) -> List[Insight]:
        """生成周报洞察"""

    def get_instructions_by_role(self, role: str, target_date: str, status: str = None) -> List[DailyInstruction]:
        """查询指定角色的指令 (前端接口)"""
```

**指令生成流程**:
```
AnalysisReport
  ↓ 提取问题
匹配 ActionDef
  ↓ 填充模板
自然语言指令
  ↓ 按角色分组
Operator / QA / TeamLeader / Manager
  ↓ 持久化
DailyInstruction 表
```

#### 3. DecisionEngine (决策引擎)

**策略模式**: 支持可插拔的决策逻辑

```python
class DecisionEngine(ABC):
    @abstractmethod
    def generate_actions(self, issue: Issue) -> List[Action]:
        pass

class RuleBasedDecisionEngine(DecisionEngine):
    """基于规则的决策 (当前)"""
    def generate_actions(self, issue: Issue) -> List[Action]:
        # 查询 ActionDef 表
        # 匹配 risk_code
        # 返回对策列表

class LLMDecisionEngine(DecisionEngine):
    """基于LLM的决策 (未来)"""
    def generate_actions(self, issue: Issue) -> List[Action]:
        # 调用 GLM-4 API
        # 自然语言生成

class HybridDecisionEngine(DecisionEngine):
    """混合决策 (未来)"""
    def generate_actions(self, issue: Issue) -> List[Action]:
        # 规则 + LLM
```

### API 接口

#### 指令相关 (新增)

```python
GET  /api/instructions                      # 获取指令列表
POST /api/instructions/{id}/read            # 标记为进行中
POST /api/instructions/{id}/done            # 标记为完成
```

#### 监控相关 (新增)

```python
GET /api/monitor/node/{node_code}           # 获取节点监控数据
GET /api/monitor/latest                     # 获取所有节点最新状态
```

#### 分析相关 (已有)

```python
POST /api/analysis/person                   # 按人员分析
POST /api/analysis/batch                    # 按批次分析
POST /api/analysis/process                  # 按工序分析
POST /api/analysis/workshop                 # 按车间分析
POST /api/analysis/time                     # 按时间分析
```

#### 图谱相关 (已有)

```python
GET /api/graph/structure                    # 获取流程图结构
GET /api/graph/nodes/{code}/risks           # 获取节点风险
```

### CSV 数据结构

#### nodes.csv - 节点定义

```csv
code,name,type
P01_IN,原料入库(AGV),Unit
E03,投料站,Unit
P_ENV,前处理环境监测,Resource
```

#### params.csv - 参数定义

```csv
node,param,name,role,unit,target,usl,lsl,is_material,data_type
E03,w_sanqi,三七投料量,Input,g,100,102,98,TRUE,Scalar
E03,temp,提取温度,Control,℃,85,90,80,FALSE,Scalar
E21,yield,浸膏得率,Output,%,98,100,95,TRUE,Scalar
```

#### flows.csv - 管路连接

```csv
source,target,name
P01_IN,P02_OUT,库存管理
P03_WEIGH1,E03,党参/甘松/黄精直接去投料
E21,C04,稠膏去制剂混合
```

#### risks.csv - 风险节点

```csv
code,name,category,prob
EXT_FAIL,提取过程故障,Top,
EXT_FAC_E,提取设备因素,Equipment,
EXT_E1,温度传感器异常,Equipment,0.02
```

#### risk_edges.csv - 因果关系

```csv
source,target
EXT_E1,EXT_FAC_E
EXT_FAC_E,EXT_FAIL
```

---

## 前端架构

### 目录结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── ProcessFlow.jsx     # 工艺流程图
│   │   ├── MonitorPanel.jsx    # 实时监控面板 ⭐
│   │   └── ActionList.jsx      # 待办指令列表 ⭐
│   ├── App.jsx                 # 主应用 (驾驶舱布局)
│   └── main.jsx
└── package.json
```

### 驾驶舱布局

```
┌──────────────────────────────────────────────────────┐
│  🧪 稳心颗粒 - 智能工艺指挥台                        │
│  [仿真/实时] [系统状态] [重连]                       │
├──────────────────────────┬───────────────────────────┤
│                          │                           │
│  左侧：工艺流程图 (70%)  │  右侧：控制台 (30%)      │
│  ┌────────────────────┐ │  ┌──────────────────────┐│
│  │                    │ │  │ 上半部分：监控面板   ││
│  │   IDEF0 流程图      │ │  │ - 趋势图 (ECharts)  ││
│  │   · 点击区块展开    │ │  │ - Cpk分布           ││
│  │   · 双击节点配置    │ │  │ - 统计指标          ││
│  │   · 右键查看风险    │ │  │                      ││
│  │                    │ │  ├──────────────────────┤│
│  │                    │ │  │ 下半部分：指令列表   ││
│  │                    │ │  │ - 待办指令          ││
│  │                    │ │  │ - 执行按钮          ││
│  │                    │ │  │ - 反馈闭环          ││
│  └────────────────────┘ │  └──────────────────────┘│
│                          │                           │
├──────────────────────────┴───────────────────────────┤
│  LSS Engine v2.0 - 智能指挥系统 · AI黑带大脑        │
└──────────────────────────────────────────────────────┘
```

### 组件说明

#### 1. ProcessFlow.jsx - 工艺流程图

**功能**:
- IDEF0 层级图谱可视化
- 点击区块展开/折叠子节点
- 双击节点查看详情
- 右键节点查看风险

**Props**:
```javascript
<ProcessFlow
  isLiveMode={false}           // 实时模式开关
  onNodeSelect={handleSelect}  // 节点选中回调
/>
```

**双模式行为**:

**仿真模式** (isLiveMode=false):
- 双击节点 → 打开配置弹窗
- 数据来源：用户输入
- 节点颜色：仿真结果决定

**实时模式** (isLiveMode=true):
- 双击节点 → 查看监控面板 (只读)
- 数据来源：后端轮询
- 节点颜色：根据实时Cpk动态变化
  - 🟢 绿色：Cpk ≥ 1.33 (稳定)
  - 🟡 黄色：0.8 ≤ Cpk < 1.33 (警告)
  - 🔴 红色：Cpk < 0.8 (失控)

#### 2. MonitorPanel.jsx - 实时监控面板 ⭐

**位置**: 右上角
**功能**: 显示选中节点的实时监控数据

**三个Tab**:

**Tab 1: 趋势图**
```javascript
xAxis: 时间 (最近100个数据点)
yAxis: 温度 (℃)
series: 温度曲线 + 控制限 (上限/目标/下限)
```

**Tab 2: Cpk分布**
```javascript
xAxis: 批次号
yAxis: Cpk 值
series: 柱状图 (颜色表示状态)
  - 红色：Cpk < 0.8 (严重不足)
  - 黄色：0.8 ≤ Cpk < 1.33 (不足)
  - 绿色：Cpk ≥ 1.33 (良好)
```

**Tab 3: 统计指标**
- 当前Cpk
- 当前值
- 偏离度 (σ)

**API调用**:
```javascript
GET /api/monitor/node/{node_code}
```

#### 3. ActionList.jsx - 待办指令列表 ⭐

**位置**: 右下角
**功能**: 显示系统自动生成的工艺指令

**指令示例**:
```
┌─────────────────────────────────────────┐
│ 📋 今日工艺指令              [Badge: 3]  │
├─────────────────────────────────────────┤
│ ⏰ [HIGH] [Operator]                    │
│   检测到E04温度异常（当前85.5℃），       │
│   建议将蒸汽阀开度从50%调至45%          │
│   [执行]                                │
│                                         │
│ ✅ [MEDIUM] [QA]                        │
│   E04温度Cpk=0.85低于临界值，           │
│   请对批次BATCH-001启动偏差调查        │
│   [完成]                                │
│                                         │
│ ✓ 已调整，温度恢复正常                 │
└─────────────────────────────────────────┘
```

**功能**:
- 按优先级排序 (CRITICAL > HIGH > MEDIUM > LOW)
- 实时更新 (每30秒刷新)
- 执行闭环 (Pending → Read → Done)
- 反馈收集

**API调用**:
```javascript
GET /api/instructions?role=Operator&status=Pending,Read
POST /api/instructions/{id}/read
POST /api/instructions/{id}/done
```

### 交互流程

#### 仿真模式流程

```
用户操作
  ↓
双击节点 → 填写参数
  ↓
POST /api/simulate
  ↓
后端计算得率
  ↓
更新节点颜色 (红/绿)
```

#### 实时模式流程

```
SCADA 数据采集 (后台)
  ↓
写入 Measurement 表
  ↓
前端轮询 /api/monitor/latest
  ↓
更新节点颜色 (根据实时Cpk)
  ↓
用户点击节点 → 查看监控面板
```

#### 指令流程

```
后端定时任务 (每天22:00)
  ↓
IntelligentCommander.generate_daily_orders()
  ↓
写入 DailyInstruction 表
  ↓
前端轮询 /api/instructions
  ↓
显示在 ActionList
  ↓
用户点击"执行" → POST /api/instructions/{id}/read
  ↓
用户点击"完成" → POST /api/instructions/{id}/done
```

---

## 双频输出机制

### 高频输出 (执行层)

**受众**: 操作工、QA、班长
**频率**: 每天/每批次
**内容**: 具体的、可执行的指令

**示例**:
```
【Operator】🔧
  检测到E04醇提罐温度异常（当前85.5℃，标准82.0℃），
  建议将蒸汽阀开度从50%调至45%

【QA】📋
  E04醇提罐温度Cpk=0.85低于临界值1.33，
  请对批次BATCH-001启动偏差调查流程
```

### 低频输出 (决策层)

**受众**: 厂长、经理
**频率**: 每周/每月/重大风险实时
**内容**: 趋势、风险预警、资源建议

**示例**:
```
📊 **周报**: 本周提取工序Cpk连续3天下滑（1.45 → 1.33 → 1.21）
  · 根因分析：蒸汽阀老化，导致控制不稳定
  · 资源建议：建议下周一停机检修，预计影响产能10%
  · 风险评估：如不处理，下月产能下降15%
```

### 完整业务流程

#### 执行层流程 (每天)

```
前一天 22:00
  ↓
[数据引擎] 自动拉取全天生产数据
  ↓
[智能编排器] BlackBeltCommander.analyze_by_batch()
  → SPC检测: "E04温度Cpk=0.85, 失控"
  → 故障树追溯: "根因80%是蒸汽阀卡滞"
  → 贝叶斯推演: "如不及时处理,明天报废率90%"
  ↓
[角色指令生成器] IntelligentCommander.generate_daily_orders()
  → 查询 ActionDef: 找到 3 条相关对策
  → 填充模板: "检测到E04温度异常..."
  → 按角色分组: Operator / QA / TeamLeader
  ↓
[持久化] 保存到 DailyInstruction 表
  ↓
次日 06:00
  ↓
[推送服务] 按角色推送到不同终端
  → Operator: 工位终端 (ActionList组件)
  → QA: 质量管理系统
  → TeamLeader: 数字大屏
  ↓
[执行追踪] Pending → Read → Done + 反馈
```

#### 决策层流程 (每周)

```
每周五 16:00
  ↓
[趋势分析] 智能编排器分析最近7天数据
  → Cpk趋势: 1.45 → 1.33 → 1.21 (连续下滑)
  → 成本分析: 原料损耗率 8.5% (标准<5%)
  → 风险评估: 如不干预，下月产能下降15%
  ↓
[洞察生成] IntelligentCommander.generate_weekly_insights()
  → 聚合问题: "连续3批次E04温度异常"
  → 根因分析: "蒸汽阀老化，导致控制不稳定"
  → 资源建议: "建议下周一停机检修，预计影响产能10%"
  ↓
[推送服务] 推送到管理层终端
  → Manager: 手机APP / 邮件 / 数字驾驶舱
  ↓
[决策支持] 管理层查看后决定是否执行
```

---

## 开发日志

### v2.0 - 智能指挥系统 (2025年1月)

#### 新增功能

**后端**:
- ✅ IntelligentCommander (智能指挥官模块)
- ✅ ActionDef + DailyInstruction 数据模型
- ✅ 对策库种子数据 (11条示例)
- ✅ 完整流程演示 (demo_commander.py)
- ✅ 新增5个API接口 (指令/监控)

**前端**:
- ✅ 驾驶舱布局 (三区设计)
- ✅ ActionList 组件 (指令列表)
- ✅ MonitorPanel 组件 (监控面板)
- ✅ 双模式切换 (仿真/实时)
- ✅ 节点选中联动

**文档**:
- ✅ COMMANDER_IMPLEMENTATION.md (指挥官实现)
- ✅ FRONTEND_UPGRADE.md (前端升级)
- ✅ DIRECTORY_STRUCTURE.md (目录结构)
- ✅ QUICK_START.md (快速启动)
- ✅ CHECKLIST.md (验证清单)

#### 架构升级

**从"工具箱"到"指挥系统"**:
- 分析工具 → 智能编排
- 报告输出 → 指令推送
- 被动查询 → 主动推送
- 单一输出 → 双频输出

**技术债务清理**:
- 重组目录结构 (core/analysis/tools/data/agent)
- 统一数据访问接口 (DataProvider)
- 可插拔决策引擎 (DecisionEngine)

### v1.0 - 基础平台 (2024年12月)

#### 核心功能

**数据库模型**:
- ✅ 三层架构 (物理层/感知层/逻辑层)
- ✅ IDEF0层级建模
- ✅ 故障树数据结构

**前端界面**:
- ✅ React Flow图谱可视化
- ✅ 参数配置弹窗
- ✅ 风险分析面板

**数据导入**:
- ✅ CSV两阶段导入策略
- ✅ 支持跨车间连接
- ✅ 4大车间完整数据

**分析工具**:
- ✅ SPC统计过程控制
- ✅ 基础仿真算法

---

## 快速启动

### 环境验证

**运行自动验证脚本**:
```bash
cd /Users/zhoutengye/med/LSS
./verify_system.sh
```

脚本会自动检查：
- ✅ Python 环境 (conda、Python 版本)
- ✅ 后端依赖 (fastapi、uvicorn、sqlalchemy 等)
- ✅ 数据库文件和表结构
- ✅ Node.js 环境 (版本 >= 18)
- ✅ 前端依赖 (react、antd、echarts 等)
- ✅ 所有核心配置文件

### 后端启动

```bash
cd backend
conda activate med
pip install fastapi uvicorn sqlalchemy  # 首次运行
python main.py
```

服务地址：`http://127.0.0.1:8000`
API文档：`http://127.0.0.1:8000/docs`

### 前端启动

```bash
cd frontend
npm install  # 首次运行
npm run dev
```

访问地址：`http://localhost:5173`

### 测试指令功能

```bash
# 后端运行演示脚本，生成测试指令
cd backend
python demo_commander.py
```

**预期输出**:
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
3. 应该能看到刚才生成的指令
4. 点击"执行"按钮测试

---

## 后续规划

### Q2 (计划中)

- ⏳ SCADA 实时数据接入
- ⏳ 定时任务调度 (Celery/APScheduler)
- ⏳ 移动端适配 (响应式布局)

### Q3 (规划中)

- ⏳ LLM 集成 (自然语言生成优化)
- ⏳ 数字驾驶舱 (IDEF0 + 风险点闪烁)
- ⏳ 反馈学习 (根据执行反馈优化对策库)

### Q4 (愿景)

- ⏳ 预测性指令 (预防未来风险)
- ⏳ 自动优化 (系统推荐工艺参数)
- ⏳ 数字孪生 (虚拟环境验证)

---

**总结**: 这是一个从"分析工具"到"指挥系统"的完整升级，实现了真正的 **AI黑带大脑**，能够自动分析、自动决策、自动推送指令，形成完整的执行闭环。

---

## 🔧 LSS 工具箱完整规划

### 23工具全景图

**L1 描述性统计** (7个)
1. Cpk 过程能力分析 ⭐ Phase 1
2. I-MR 控制图 ⭐ Phase 1
3. 直方图 ⭐ Phase 1
4. Xbar-R 控制图
5. P图/U图
6. 箱线图
7. OEE 设备效率分析

**L2 诊断性分析** (6个)
8. 故障树分析 (FTA) ⭐ Phase 2
9. 帕累托图 ⭐ Phase 2
10. 鱼骨图
11. 相关性分析
12. 方差分析 (ANOVA)
13. 双样本T检验

**L3 预测性分析** (5个)
14. 贝叶斯网络 ⭐ Phase 3
15. 相关性热力图 ⭐ Phase 3
16. 多元回归 ⭐ Phase 3
17. 时序预测 (ARIMA)
18. Monte Carlo 仿真

**L4 规范性分析** (5个)
19. NSGA-II 多目标优化 ⭐ Phase 4
20. DOE 实验设计
21. 响应曲面法 (RSM)
22. 田口方法
23. 约束优化

**开发说明**:
- ✅ 已实现: SPC 工具
- ⭐ 优先开发: Phase 1-3 核心工具
- 其他工具可后续补充

### 工具目录结构

```
backend/tools/
├── descriptive/        # L1: 描述性统计 (7工具)
│   └── spc.py         # ✅ 已实现
├── diagnostic/         # L2: 诊断性分析 (6工具) ⏳
├── predictive/         # L3: 预测性分析 (5工具) ⏳
└── prescriptive/       # L4: 规范性分析 (5工具) ⏳
```

### 开发顺序

1. **Phase 1 - 监控三剑客**: Cpk, I-MR, 直方图
2. **Phase 2 - 诊断双子星**: FTA, 帕累托
3. **Phase 3 - 高阶杀手锏**: 相关性热力图, 多元回归
4. **Phase 4 - 优化工具**: NSGA-II, DOE, RSM 等
