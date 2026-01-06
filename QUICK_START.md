# 🚀 快速启动指南

## 系统能否运行？能！

前端和后端都已经配置完成，现在可以正常运行。

---

## 📋 前置条件检查

### 1. Python 环境
```bash
# 检查 conda 环境
conda activate med
python --version  # 应该是 Python 3.x
```

### 2. Node.js 环境
```bash
# 检查 Node.js 版本
node --version  # 应该 >= 18.x
npm --version
```

### 3. 依赖已安装
```bash
# Python 依赖（后端）
cd backend
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

# npm 依赖（前端）
cd frontend
npm list | grep -E "(react|antd|axios|echarts)"
```

---

## 🎯 启动步骤

### 步骤 1：启动后端

```bash
# 进入后端目录
cd backend

# 激活 conda 环境
source ~/.zshrc
conda activate med

# 启动 FastAPI 服务器
python main.py
```

✅ 成功标志：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

后端地址：`http://127.0.0.1:8000`

API文档：`http://127.0.0.1:8000/docs`

### 步骤 2：启动前端（新终端窗口）

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev
```

✅ 成功标志：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

前端地址：`http://localhost:5173`

---

## ✅ 功能验证

### 1. 检查系统连接
- 打开前端：`http://localhost:5173`
- 查看右上角：应该显示"系统状态: 在线 (XX℃)"
- 如果是"离线"，点击"重连"按钮

### 2. 测试仿真模式（默认）
- **操作**：点击流程图中的区块（如"提取车间"）
- **预期**：展开显示下属工序节点
- **操作**：双击某个 Unit 节点（如 E04）
- **预期**：打开配置弹窗，可以输入温度参数

### 3. 测试实时模式切换
- **操作**：点击顶部"仿真"开关，切换到"实时"
- **预期**：显示提示"已切换到实时监控模式"
- **操作**：双击 Unit 节点
- **预期**：不再打开配置弹窗，而是显示"已选中 E04 - 查看右侧监控面板"

### 4. 查看监控面板
- **操作**：点击任意 Unit 节点
- **预期**：右上角监控面板显示该节点的趋势图、Cpk分布、统计指标

### 5. 查看指令列表
- **位置**：右下角
- **内容**：应该显示"今日工艺指令"列表
- **注意**：如果是空列表，说明没有待处理指令（系统运行正常）

---

## 🎨 界面布局

```
┌──────────────────────────────────────────────────────┐
│  🧪 稳心颗粒 - 智能工艺指挥台                      │
│  [仿真/实时] [系统状态] [重连]                       │
├─────────────────────────────┬────────────────────────┤
│                             │                        │
│  左侧：工艺流程图            │  右侧：控制台          │
│  - 点击区块展开/折叠        │  - 上半部分：监控面板 │
│  - 双击节点配置/查看        │  - 下半部分：指令列表 │
│                             │                        │
└─────────────────────────────┴────────────────────────┘
```

---

## 🔍 常见问题

### Q1: 前端显示"离线"
**解决方法**：
1. 检查后端是否启动：`http://127.0.0.1:8000/docs`
2. 检查控制台是否有 CORS 错误
3. 点击"重连"按钮

### Q2: 指令列表是空的
**原因**：这是正常的！系统只在检测到异常时才生成指令
**验证方法**：
```bash
# 后端运行演示脚本，生成测试指令
cd backend
python demo_commander.py
```

### Q3: 监控面板没有数据
**原因**：数据库中暂无测量数据
**解决方法**：
```bash
# 导入种子数据
cd backend
python seed.py  # 导入基础数据
```

### Q4: 实时模式不工作
**原因**：SCADA 数据采集脚本未运行
**说明**：实时模式需要 SCADA 接入，目前是预留接口

### Q5: 节点颜色不变化
**原因**：节点颜色基于 Cpk 值，需要足够的测量数据
**正常情况**：
- 🟢 绿色：Cpk ≥ 1.33
- 🟡 黄色：0.8 ≤ Cpk < 1.33
- 🔴 红色：Cpk < 0.8

---

## 📊 可用的 API 端点

### 分析相关
```
POST /api/analysis/person      # 按人员分析
POST /api/analysis/batch       # 按批次分析
POST /api/analysis/process     # 按工序分析
POST /api/analysis/workshop    # 按车间分析
POST /api/analysis/time        # 按时间分析
POST /api/analysis/daily       # 每日生产报告
```

### 指令相关（新增）
```
GET /api/instructions              # 获取指令列表
POST /api/instructions/{id}/read    # 标记为进行中
POST /api/instructions/{id}/done    # 标记为完成
```

### 监控相关（新增）
```
GET /api/monitor/node/{node_code}  # 获取节点监控数据
GET /api/monitor/latest             # 获取所有节点最新状态
```

### 图谱相关
```
GET /api/graph/structure            # 获取流程图结构
GET /api/graph/nodes/{code}/risks    # 获取节点风险
```

---

## 🧪 测试流程

### 完整测试流程

1. **启动系统**
   ```bash
   # 终端1：后端
   cd backend && conda activate med && python main.py

   # 终端2：前端
   cd frontend && npm run dev
   ```

2. **验证连接**
   - 打开浏览器：`http://localhost:5173`
   - 确认右上角显示"在线"

3. **测试仿真模式**
   - 点击"提取车间"区块 → 展开工序
   - 双击"E04"节点 → 打开配置弹窗
   - 输入温度值 → 点击确定

4. **测试实时模式**
   - 切换到"实时"模式
   - 双击节点 → 查看监控面板
   - 点击不同节点 → 监控面板更新

5. **测试指令功能**
   ```bash
   # 终端3：生成测试指令
   cd backend
   python demo_commander.py
   ```
   - 回到前端，刷新页面
   - 右下角应该显示测试指令

6. **测试指令操作**
   - 点击"执行"按钮 → 状态变为"进行中"
   - 点击"完成"按钮 → 状态变为"已完成"

---

## 🎉 成功标志

当你看到以下界面，说明系统运行正常：

### 仿真模式
```
✅ 流程图显示正常（3个区块）
✅ 点击区块能展开/折叠
✅ 双击节点打开配置弹窗
✅ 输入参数后能仿真计算
✅ 系统状态显示"在线"
```

### 实时模式
```
✅ 切换开关显示"实时监控"
✅ 双击节点不打开弹窗
✅ 右侧监控面板显示趋势图
✅ 监控面板有3个Tab（趋势/Cpk/统计）
✅ 节点颜色根据数据变化
```

### 指令系统
```
✅ 右下角显示指令列表
✅ 指令有优先级标签
✅ 点击"执行"有效
✅ 点击"完成"有效
✅ 状态正确更新
```

---

## 📝 下一步

系统已经可以正常运行！接下来你可以：

1. **导入真实数据**：
   ```bash
   cd backend
   python seed.py  # 导入种子数据
   ```

2. **生成测试指令**：
   ```bash
   python demo_commander.py  # 生成测试指令
   ```

3. **开发新功能**：
   - 添加新的分析工具
   - 扩展对策库（actions.csv）
   - 实现定时任务调度

4. **接入 SCADA**：
   - 编写采集脚本
   - 配置映射表
   - 启动实时监控

---

**总结**：✅ 前后端配合完全正常，可以运行！
