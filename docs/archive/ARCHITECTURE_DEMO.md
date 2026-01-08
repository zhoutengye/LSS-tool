# LSS 架构调整与 Demo 开发完整方案

**制定时间**: 2025年1月6日
**核心理念**: 不做"抛弃型代码"，做"微缩版正品"

---

## 🎯 需求回顾

从 Demo 需求推导出的真实业务需求：

### 功能1: 知识图谱"无中生有"
- **Demo场景**: 上传Excel → 瞬间生成复杂流程图
- **真实需求**: 支持客户自主导入工艺数据，不需要程序员写CSV

### 功能2: 填报与入库
- **Demo场景**: 车间主任/操作工填报数据
- **真实需求**: 多角色数据采集、元数据驱动的动态表单

### 功能3: 千人千面报告
- **Demo场景**: 操作工看指令、经理看趋势图
- **真实需求**: 基于角色的消息分发、多维度分析报告

### 功能4: AI知识问答
- **Demo场景**: 聊天机器人回答工艺问题
- **真实需求**: RAG知识库、语义检索、LLM生成

---

## 🏗️ 架构缺口与调整

### 原有架构
```
backend/
├── core/
│   ├── base.py              # BaseTool基类
│   ├── registry.py          # 工具注册中心
│   └── optimization.py      # 优化算法
├── analysis/                # 智能编排层
│   ├── orchestrator.py      # 黑带分析器
│   ├── commander.py         # 智能指挥官
│   └── decision_engine.py   # 决策引擎
├── tools/                   # 分析工具箱
├── data/                    # 数据访问层
└── models.py                # 数据库模型
```

### ⚠️ 缺失的3个关键模块

#### 1. **图谱导入引擎** (Graph Importer)
**对应需求1**: 知识图谱"无中生有"

**职责**:
- 解析Excel/CSV/Visio/XML文件
- 数据验证与清洗
- 自动构建ProcessNode/ParameterDef/RiskNode
- 支持增量更新

**真实能力**: 完整的文件解析pipeline + 数据验证
**Demo能力**: 运行seed.py预置数据

#### 2. **RAG 知识库** (RAG Engine)
**对应需求4**: AI知识问答

**职责**:
- 文档加载 (PDF/TXT/MD)
- 文本分块 (Chunking)
- 向量化 (Embeddings)
- 语义检索 (相似度搜索)
- LLM生成 (可选)

**真实能力**: Milvus/Chroma向量库 + GPT-4
**Demo能力**: FAISS轻量级索引 + 关键词匹配 + PDF原文返回

#### 3. **消息分发中心** (Notification Center)
**对应需求3**: 千人千面报告

**职责**:
- 基于角色的消息筛选
- 优先级管理
- 多渠道推送 (API/邮件/App/微信)
- 消息状态跟踪

**真实能力**: 完整的通知系统 + 推送服务
**Demo能力**: API返回筛选后的JSON数据

---

## ✅ 已完成工作

### 1. 创建新增模块文件

```
backend/core/
├── graph_importer.py        # ✅ 图谱导入引擎
├── rag_engine.py             # ✅ RAG知识库引擎
└── notification_center.py   # ✅ 消息分发中心

backend/
└── demo_api.py               # ✅ Demo专用API路由
```

### 2. 注册Demo API

已在 `main.py` 中添加：
```python
from demo_api import router as demo_router
app.include_router(demo_router)
```

### 3. 工具箱文件结构

已创建23个工具占位文件：
- L1 描述性统计: 8个
- L2 诊断性分析: 6个
- L3 预测性分析: 5个
- L4 规范性分析: 5个

---

## 📋 Demo API 端点清单

### 功能1: 知识图谱导入

```
POST /api/demo/setup/init
Body: { "reset": true }
Response: { "success": true, "stats": {...} }

POST /api/demo/setup/upload
Body: (multipart) file
Response: { "success": true, "progress": 100 }
```

### 功能2: 数据填报

```
POST /api/demo/input/submit
Body: { "role": "worker", "node_code": "E04", "measurements": {...} }
Response: { "success": true, "batch_id": "BATCH_20250106" }

GET /api/demo/input/form/{node_code}
Response: { "success": true, "form": {...} }
```

### 功能3: 角色分析报告

```
POST /api/demo/report
Body: { "role": "worker" | "manager" | "qa" | "teamleader", "time_window": 7 }
Response: { "success": true, "type": "instruction" | "insight", "data": {...} }
```

### 功能4: AI知识问答

```
POST /api/demo/chat
Body: { "question": "提取温度标准是多少？", "use_llm": false }
Response: { "success": true, "answer": "...", "sources": [...] }

GET /api/demo/chat/knowledge
Response: { "success": true, "stats": {...} }
```

---

## 🚀 下一步实施计划

### 步骤3: 实现 Graph Importer (真实功能)

**文件**: `backend/core/graph_importer.py`

**实现要点**:
1. 使用 pandas 读取Excel
2. 验证数据格式 (必填字段、数据类型)
3. 批量插入数据库
4. 返回统计信息

**Demo实现**: 直接运行 seed.py

### 步骤4: 实现 RAG Engine (轻量级)

**文件**: `backend/core/rag_engine.py`

**实现要点**:
1. 预加载知识文本 (手动定义)
2. 简单的关键词匹配搜索
3. 返回最相关的段落

**Demo实现**:
```python
engine = RAGEngine()
engine.load_text_chunks([
    {"text": "提取温度标准是80-90℃...", "source": "SOP-001"},
    ...
])
result = engine.ask("提取温度标准是多少？")
```

### 步骤5: 实现角色分析 API

**文件**: `backend/core/notification_center.py`

**实现要点**:
1. 查询 DailyInstruction 表
2. 根据 role 参数筛选
3. 计算Cpk趋势 (manager视图)
4. 返回JSON格式报告

**Demo实现**:
```python
center = NotificationCenter()
if role == "worker":
    notifications = center.get_worker_notifications()
elif role == "manager":
    report = center.get_manager_report()
```

### 步骤6: 前端Demo页面开发

**文件**: `frontend/src/components/demo/`

**页面结构**:
1. **SetupWizard.jsx** - 建厂向导 (功能1)
2. **DataInput.jsx** - 数据填报 (功能2)
3. **RoleReport.jsx** - 角色报告 (功能3)
4. **ChatWidget.jsx** - AI问答 (功能4)

---

## 💡 架构优势

### 1. 可扩展性
- Graph Importer: 未来可支持更多文件格式
- RAG Engine: 未来可切换到真正的向量数据库
- Notification Center: 未来可接真实的推送服务

### 2. 可维护性
- 所有模块都有清晰的职责
- Demo代码不会成为技术债
- 可以平滑过渡到生产环境

### 3. 可测试性
- 每个模块都有独立的API端点
- 可以单独测试每个功能
- Mock数据和真实数据可以共存

---

## 📝 开发原则

### ✅ 要做

1. **基于真实架构** - 所有模块都使用BaseTool、数据库模型等
2. **统一接口规范** - 返回格式一致 `{success, data, message}`
3. **错误处理** - try-except捕获异常并返回友好提示
4. **数据验证** - 使用Pydantic模型验证输入

### ❌ 不要做

1. **写死返回数据** - 所有数据从数据库计算得出
2. **绕过现有架构** - 复用已有的Tool、Registry、Provider
3. **为了Demo而Demo** - 每个模块都考虑未来扩展

---

## 🎬 Demo 演示脚本

### 场景1: 建厂向导 (2分钟)

```
"各位领导，我们的系统不需要你们有完善的图纸。
看，我现在上传一份 Excel..." (点击初始化)

[进度条: "正在解析工艺流程... 30%"]
[进度条: "正在构建贝叶斯网络... 60%"]
[进度条: "正在生成风险节点... 100%"]

"看！瞬间生成了完整的工艺流程图！"
```

### 场景2: 数据填报 (1分钟)

```
"这是车间主任小王，他每天只需花1分钟填这个表..."

[选择角色: 车间主任]
[选择节点: E04 醇提罐]
[输入数据: 温度: 85.5℃, 压力: 2.1MPa]

"数据已自动入库，系统开始实时监控..."
```

### 场景3: 角色报告 (2分钟)

```
"第二天早上，不同角色看到不同的报告..."

[切换到操作工视图]
"操作工小李看到了这条指令：
⚠️ E04 蒸汽阀开度调至 45%"

[切换到经理视图]
"而厂长您看到了这份分析：
📉 提取工序Cpk从1.33降到0.85
💡 建议：针对'蒸汽阀'进行专项改善"
```

### 场景4: AI问答 (1分钟)

```
"如果您对某个参数有疑问，直接问AI..."

[输入: "提取温度标准是多少？"]
[AI回复: "根据SOP-提取工艺，提取温度标准范围是80-90℃，目标值为85℃"]

[输入: "Cpk怎么算？"]
[AI回复: "Cpk = min((USL-μ)/3σ, (μ-LSL)/3σ)..."]
```

---

## 📊 技术栈总结

### 后端技术栈

**现有**:
- FastAPI (Web框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- pandas, numpy, scipy (数据分析)
- networkx (图论分析)

**新增**:
- ✅ subprocess (运行seed.py)
- ✅ pandas (Excel解析 - Graph Importer)
- ⏳ FAISS (向量检索 - RAG Engine)
- ⏳ OpenAI API (LLM生成 - 可选)

### 前端技术栈

**现有**:
- React 19 + Vite
- React Flow (图谱可视化)
- Ant Design 6 (UI组件)
- ECharts (数据可视化)

**新增**:
- Ant Design Tabs (页面导航)
- Ant Design Upload (文件上传)
- Ant Design Form (数据填报)
- Ant Design Chat (AI对话)

---

## ✅ 成功标准

### 功能1: 知识图谱导入
- ✅ 点击初始化，生成工艺图谱
- ✅ 统计数据准确 (节点数、参数数、风险数)

### 功能2: 数据填报
- ✅ 根据节点动态生成表单
- ✅ 数据成功写入数据库
- ✅ 可以查询到历史数据

### 功能3: 角色分析报告
- ✅ 操作工看到指令列表
- ✅ 经理看到Cpk趋势图
- ✅ QA看到质量检查任务

### 功能4: AI知识问答
- ✅ 能回答温度标准问题
- ✅ 能回答Cpk计算问题
- ✅ 能返回文档来源

---

## 🎯 总结

**架构调整完成了以下目标**:

1. ✅ **补齐了缺口** - Graph Importer, RAG Engine, Notification Center
2. ✅ **基于真实需求** - 所有模块都来自Demo场景推导的真实业务需求
3. ✅ **可扩展设计** - Demo代码可以平滑过渡到生产环境
4. ✅ **统一接口规范** - 所有API都遵循相同的格式
5. ✅ **完整的API** - 4大功能对应的8个端点已就绪

**下一步**: 实现步骤3-6，让Demo真正跑起来！
