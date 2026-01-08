"""LSS 系统主程序

FastAPI 后端服务，提供 RESTful API 接口。

主要功能:
- 知识图谱查询 (工序节点、工艺流向)
- 批次数据管理
- 分析工具调用
- 前端可视化数据支持

API 端点:
- GET /api/graph/structure: 获取工艺图谱结构
- POST /api/tools/run/{tool_name}: 运行分析工具

Example:
    >>> import uvicorn
    >>> uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import engine, get_db
import models

# 导入编排层
from analysis import BlackBeltCommander, ReportFormatter

# 启动时自动建表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wexin LSS Engine")


# ============================================
# 启动事件：初始化演示数据
# ============================================

@app.on_event("startup")
async def startup_event():
    """应用启动时自动初始化演示数据"""
    import os
    from initial_data.demo_init import init_demo_data

    # 获取数据库路径（与 database.py 中的配置保持一致）
    db_path = os.path.join(os.path.dirname(__file__), "lss.db")

    print("\n" + "="*60)
    print("🚀 LSS 系统启动中...")
    print("="*60)

    # 初始化演示数据
    init_demo_data(db_path)

    print("="*60)
    print("✅ LSS 系统启动完成！")
    print("="*60 + "\n")

# 跨域配置 (让前端能连上)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 当使用 "*" 时必须设为 False
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)


@app.get("/")
def root():
    """系统状态检查端点

    Returns:
        系统状态信息
    """
    return {
        "status": "System Online",
        "modules": ["SPC", "Risk", "Optimization"]
    }


@app.get("/api/test")
def test_connection():
    """测试连接端点

    用于临时兼容前端 Demo。

    Returns:
        测试响应数据
    """
    return {"node": "Backend Ready", "temperature": 25.0}


@app.post("/api/simulate")
def simple_simulation(data: dict):
    """简单仿真端点 (临时接口)

    临时逻辑，为了不让前端报错。

    Args:
        data: 包含 temperature 的字典

    Returns:
        仿真结果
    """
    temp = data.get("temperature", 0)
    res = 98.0 - abs(temp - 85) * 1.5
    return {"status": "ok", "result_yield": round(res, 2)}


@app.get("/api/graph/structure")
def get_graph_structure(db: Session = Depends(get_db)):
    """获取工艺图谱结构

    返回所有节点和连线数据，用于前端绘制 ReactFlow 图谱。

    Args:
        db: 数据库会话

    Returns:
        包含 nodes 和 edges 的字典:
        - nodes: 节点列表，包含位置、样式、数据
        - edges: 连线列表，包含源节点、目标节点、标签
    """
    # 查出所有节点和连线
    nodes = db.query(models.ProcessNode).all()
    edges = db.query(models.ProcessEdge).all()

    # 构建节点映射 (code -> id)
    code_to_id = {node.code: node.id for node in nodes}

    # 分离区块、单元和资源
    blocks = [n for n in nodes if n.node_type == "Block"]
    units = [n for n in nodes if n.node_type == "Unit"]
    resources = [n for n in nodes if n.node_type == "Resource"]

    flow_nodes = []
    flow_edges = []

    # 先放置区块（水平排列，间距大）
    block_spacing = 500
    for idx, block in enumerate(blocks):
        flow_nodes.append({
            "id": str(block.id),
            "data": {
                "label": f"{block.code}\n{block.name}",
                "code": block.code,
                "name": block.name,
                "type": "Block",
                "params": [],
                "isExpanded": False,
                "children": [str(u.id) for u in units if u.parent_id == block.id]
            },
            "position": {"x": 50 + idx * block_spacing, "y": 50},
            "style": {
                "width": 200,
                "height": 80,
                "border": "3px solid #1890ff",
                "background": "#e6f7ff",
                "borderRadius": "12px",
                "fontSize": "18px",
                "fontWeight": "bold",
                "cursor": "pointer"
            },
            "className": "block-node"
        })

    # Unit 节点默认隐藏
    for unit in units:
        # 找到父区块的位置
        parent_block = next((b for b in blocks if b.id == unit.parent_id), None)
        if parent_block:
            parent_idx = blocks.index(parent_block)
            base_x = 50 + parent_idx * block_spacing

            flow_nodes.append({
                "id": str(unit.id),
                "data": {
                    "label": f"{unit.code}\n{unit.name}",
                    "code": unit.code,
                    "name": unit.name,
                    "type": "Unit",
                    "parentId": str(unit.parent_id),
                    "hidden": True,
                    "params": [
                        {
                            "code": p.code,
                            "name": p.name,
                            "unit": p.unit,
                            "role": p.role,
                            "usl": p.usl,
                            "lsl": p.lsl,
                            "target": p.target
                        }
                        for p in unit.params
                    ]
                },
                "position": {"x": base_x, "y": 200},
                "style": {
                    "width": 180,
                    "border": "2px solid #52c41a",
                    "background": "white",
                    "borderRadius": "8px",
                    "fontSize": "14px"
                },
                "className": "unit-node",
                "hidden": True
            })

    # Resource 节点（环境监测等）默认可见，放在画布右上角
    for idx, resource in enumerate(resources):
        # 找到父区块
        parent_block = next((b for b in blocks if b.id == resource.parent_id), None)
        if parent_block:
            parent_idx = blocks.index(parent_block)
            base_x = 50 + parent_idx * 500

            flow_nodes.append({
                "id": str(resource.id),
                "data": {
                    "label": f"{resource.code}\n{resource.name}",
                    "code": resource.code,
                    "name": resource.name,
                    "type": "Resource",
                    "parentId": str(resource.parent_id),
                    "params": [
                        {
                            "code": p.code,
                            "name": p.name,
                            "unit": p.unit,
                            "role": p.role,
                            "usl": p.usl,
                            "lsl": p.lsl,
                            "target": p.target
                        }
                        for p in resource.params
                    ]
                },
                "position": {"x": base_x + 10, "y": -100},  # 放在区块上方居中
                "style": {
                    "width": 180,
                    "border": "2px solid #faad14",
                    "background": "#fffbe6",
                    "borderRadius": "8px",
                    "fontSize": "14px"
                },
                "className": "resource-node"
            })

    # 连线（Unit 之间的流向）
    for edge in edges:
        source_id = code_to_id.get(edge.source_code)
        target_id = code_to_id.get(edge.target_code)

        if source_id and target_id:
            # 只有当两个都是 Unit 时才连线
            source_node = next((n for n in units if n.id == source_id), None)
            target_node = next((n for n in units if n.id == target_id), None)

            if source_node and target_node:
                flow_edges.append({
                    "id": f"e{source_id}-{target_id}",
                    "source": str(source_id),
                    "target": str(target_id),
                    "label": edge.name,
                    "animated": True,
                    "style": {"stroke": "#1890ff", "strokeWidth": 2},
                    "hidden": True
                })

    # 区块间的主流程连线
    for idx in range(len(blocks) - 1):
        source_id = blocks[idx].id
        target_id = blocks[idx + 1].id
        flow_edges.append({
            "id": f"block_edge_{source_id}_{target_id}",
            "source": str(source_id),
            "target": str(target_id),
            "label": "→",
            "animated": True,
            "style": {"stroke": "#1890ff", "strokeWidth": 3, "strokeDasharray": "5 5"}
        })

    return {"nodes": flow_nodes, "edges": flow_edges}


@app.get("/api/graph/risks/tree")
def get_risk_tree(db: Session = Depends(get_db)):
    """获取完整的故障树结构

    返回所有风险节点和因果关系边，用于前端构建故障树可视化。

    Args:
        db: 数据库会话

    Returns:
        包含 risks 和 edges 的字典
    """
    risks = db.query(models.RiskNode).all()
    edges = db.query(models.RiskEdge).all()

    risk_nodes = [{
        "id": risk.id,
        "code": risk.code,
        "name": risk.name,
        "category": risk.category,
        "base_probability": risk.base_probability
    } for risk in risks]

    risk_edges = [{
        "id": f"r{edge.id}",
        "source": edge.source_code,
        "target": edge.target_code,
        "animated": True,
        "style": {"stroke": "#ff4d4f", "strokeWidth": 2}
    } for edge in edges]

    return {"risks": risk_nodes, "edges": risk_edges}


@app.get("/api/graph/nodes/{node_code}/risks")
def get_node_risks(node_code: str, db: Session = Depends(get_db)):
    """获取指定节点的相关风险

    根据节点编码（如 E04, C05）查找相关的风险节点。

    Args:
        node_code: 节点编码
        db: 数据库会话

    Returns:
        该节点相关的风险列表
    """
    # 查询所有风险节点
    all_risks = db.query(models.RiskNode).all()

    # 根据节点编码匹配相关风险
    # 提取车间节点 (E01-E21) 匹配 EXT_*, CONC_*, PREC_*
    # 制剂车间节点 (C01-C09) 匹配 GRAN_*
    related_risks = []
    for risk in all_risks:
        if node_code.startswith('E') and risk.code.startswith(('EXT_', 'CONC_', 'PREC_')):
            related_risks.append({
                "id": risk.id,
                "code": risk.code,
                "name": risk.name,
                "category": risk.category,
                "base_probability": risk.base_probability
            })
        elif node_code.startswith('C') and risk.code.startswith('GRAN_'):
            related_risks.append({
                "id": risk.id,
                "code": risk.code,
                "name": risk.name,
                "category": risk.category,
                "base_probability": risk.base_probability
            })

    return {"risks": related_risks}


# ============================================
# 新增：智能编排层 API 端点
# ============================================

# 请求模型
class PersonAnalysisRequest(BaseModel):
    """按人员分析请求"""
    operator_id: str
    date_range: Optional[List[str]] = None  # ["2025-01-01", "2025-01-31"]


class BatchAnalysisRequest(BaseModel):
    """按批次分析请求"""
    batch_id: str
    include_risks: Optional[bool] = True
    include_recommendations: Optional[bool] = True


class ProcessAnalysisRequest(BaseModel):
    """按工序分析请求"""
    node_code: str
    time_window: Optional[int] = 7  # 最近7天


class WorkshopAnalysisRequest(BaseModel):
    """按车间分析请求"""
    block_id: str
    date: Optional[str] = None  # YYYY-MM-DD，默认今天


class TimeAnalysisRequest(BaseModel):
    """按时间分析请求"""
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    granularity: Optional[str] = "day"  # day/week/month


class DailyAnalysisRequest(BaseModel):
    """每日生产报告请求"""
    date: str  # YYYY-MM-DD


@app.post("/api/analysis/person")
def analyze_person(request: PersonAnalysisRequest, db: Session = Depends(get_db)):
    """
    分析指定操作工的绩效

    POST /api/analysis/person
    {
        "operator_id": "USER_001",
        "date_range": ["2025-01-01", "2025-01-31"]
    }
    """
    try:
        commander = BlackBeltCommander(db)

        # 转换日期范围
        date_range = None
        if request.date_range and len(request.date_range) == 2:
            from datetime import datetime
            start = datetime.strptime(request.date_range[0], "%Y-%m-%d")
            end = datetime.strptime(request.date_range[1], "%Y-%m-%d")
            date_range = (start, end)

        report = commander.analyze_by_person(request.operator_id, date_range)

        formatter = ReportFormatter()
        return formatter.to_dict(report)

    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/analysis/batch")
def analyze_batch(request: BatchAnalysisRequest, db: Session = Depends(get_db)):
    """
    分析单个批次

    POST /api/analysis/batch
    {
        "batch_id": "BATCH_001",
        "include_risks": true,
        "include_recommendations": true
    }
    """
    try:
        commander = BlackBeltCommander(db)
        report = commander.analyze_by_batch(request.batch_id)

        formatter = ReportFormatter()
        return formatter.to_dict(report)

    except Exception as e:
        return {"error": str(e), "success": False}


@app.get("/api/analysis/batch/{batch_id}/actions")
def get_batch_actions(batch_id: str, max_actions: int = 5, db: Session = Depends(get_db)):
    """
    获取批次的优先级行动建议（快速端点）

    只返回最关键的行动建议，用于前端快速显示。

    GET /api/analysis/batch/BATCH_001/actions?max_actions=5
    """
    try:
        commander = BlackBeltCommander(db)
        actions = commander.get_recommended_actions(batch_id, max_actions)
        return {"actions": actions, "success": True}

    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/analysis/process")
def analyze_process(request: ProcessAnalysisRequest, db: Session = Depends(get_db)):
    """
    分析指定工序的稳定性

    POST /api/analysis/process
    {
        "node_code": "E04",
        "time_window": 7  # 最近7天
    }
    """
    try:
        commander = BlackBeltCommander(db)
        report = commander.analyze_by_process(request.node_code, request.time_window)

        formatter = ReportFormatter()
        return formatter.to_dict(report)

    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/analysis/workshop")
def analyze_workshop(request: WorkshopAnalysisRequest, db: Session = Depends(get_db)):
    """
    分析整个车间的整体表现

    POST /api/analysis/workshop
    {
        "block_id": "BLOCK_E",
        "date": "2025-01-03"
    }
    """
    try:
        commander = BlackBeltCommander(db)
        report = commander.analyze_by_workshop(request.block_id, request.date)

        formatter = ReportFormatter()
        return formatter.to_dict(report)

    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/analysis/time")
def analyze_time(request: TimeAnalysisRequest, db: Session = Depends(get_db)):
    """
    分析时间维度的趋势

    POST /api/analysis/time
    {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "granularity": "week"  # day/week/month
    }
    """
    try:
        commander = BlackBeltCommander(db)
        report = commander.analyze_by_time(
            request.start_date,
            request.end_date,
            request.granularity
        )

        formatter = ReportFormatter()
        return formatter.to_dict(report)

    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/analysis/daily")
def analyze_daily_production(request: DailyAnalysisRequest, db: Session = Depends(get_db)):
    """
    每日生产报告（核心入口）

    这个接口会组合多个维度：
    1. 按车间：查看每个车间的整体表现
    2. 按批次：分析问题批次
    3. 按工序：识别失控工序
    4. 按人员：标记需要培训的操作工

    POST /api/analysis/daily
    {
        "date": "2025-01-03"
    }
    """
    try:
        commander = BlackBeltCommander(db)
        formatter = ReportFormatter()

        # 多维度分析
        workshop_reports = []
        for block_id in ["BLOCK_E", "BLOCK_P", "BLOCK_C"]:
            try:
                report = commander.analyze_by_workshop(block_id, request.date)
                workshop_reports.append(report)
            except Exception as e:
                # 单个车间分析失败不影响其他车间
                continue

        # 汇总报告
        merged_report = formatter.merge_reports(workshop_reports)

        return merged_report

    except Exception as e:
        return {"error": str(e), "success": False}

# ============================================
# 指令管理 API 端点
# ============================================

@app.get("/api/instructions")
def get_instructions(
    role: str,
    status: Optional[str] = None,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取指令列表
    
    GET /api/instructions?role=Operator&status=Pending,Read
    """
    try:
        from analysis import IntelligentCommander
        from datetime import datetime
        
        commander = IntelligentCommander(db)
        
        # 默认查询今天
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        instructions = commander.get_instructions_by_role(
            role=role,
            target_date=target_date,
            status=status
        )
        
        return {
            "instructions": [
                {
                    "id": inst.id,
                    "role": inst.role,
                    "content": inst.content,
                    "priority": inst.priority,
                    "status": inst.status,
                    "evidence": inst.evidence,
                    "node_code": inst.node_code,
                    "batch_id": inst.batch_id,
                    "created_at": inst.instruction_date.isoformat() if inst.instruction_date else None
                }
                for inst in instructions
            ],
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/instructions/{instruction_id}/read")
def mark_instruction_read(instruction_id: int, db: Session = Depends(get_db)):
    """
    标记指令为已读（进行中）
    
    POST /api/instructions/123/read
    """
    try:
        from analysis import IntelligentCommander
        
        commander = IntelligentCommander(db)
        commander.mark_instruction_read(instruction_id)
        
        return {"success": True, "message": "指令已标记为进行中"}
    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/instructions/{instruction_id}/done")
def mark_instruction_done(
    instruction_id: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    标记指令为完成
    
    POST /api/instructions/123/done
    Body: { "feedback": "已完成调整" }
    """
    try:
        from analysis import IntelligentCommander
        
        commander = IntelligentCommander(db)
        commander.mark_instruction_done(instruction_id, feedback or "")
        
        return {"success": True, "message": "指令已完成"}
    except Exception as e:
        return {"error": str(e), "success": False}


# ============================================
# 监控数据 API 端点
# ============================================

@app.get("/api/monitor/node/{node_code}")
def get_node_monitoring(node_code: str, db: Session = Depends(get_db)):
    """
    获取节点监控数据（实时SCADA或历史数据）
    
    GET /api/monitor/node/E04
    """
    try:
        import models
        from sqlalchemy import desc
        
        # 查询该节点最近的温度测量数据
        measurements = db.query(models.Measurement).filter(
            models.Measurement.node_code == node_code,
            models.Measurement.param_code == "temp"  # 假设查温度
        ).order_by(desc(models.Measurement.timestamp)).limit(100).all()
        
        if not measurements:
            return {
                "trend": {"times": [], "values": [], "cpk_history": []},
                "statistics": None,
                "success": True
            }
        
        # 提取数据
        times = [m.timestamp.strftime("%H:%M") for m in measurements]
        values = [float(m.value) for m in measurements]
        
        # 简单计算统计数据（实际应调用SPC工具）
        import statistics
        current_value = values[0] if values else 0
        avg_value = statistics.mean(values) if len(values) > 1 else 0
        std_value = statistics.stdev(values) if len(values) > 1 else 0
        
        # 模拟Cpk历史（实际应从分析结果获取）
        cpk_history = [1.45, 1.33, 1.21, 1.15, 1.08]
        cpk = cpk_history[-1] if cpk_history else 1.0
        
        # 假设规格（实际应从ParameterDef获取）
        usl, lsl, target = 85.0, 79.0, 82.0
        
        # 计算偏离度（σ）
        deviation = (current_value - target) / std_value if std_value > 0 else 0
        
        return {
            "trend": {
                "times": times,
                "values": values,
                "cpk_history": cpk_history
            },
            "statistics": {
                "cpk": cpk,
                "current_value": current_value,
                "usl": usl,
                "lsl": lsl,
                "target": target,
                "deviation": deviation
            },
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@app.get("/api/monitor/latest")
def get_all_latest_status(db: Session = Depends(get_db)):
    """
    获取所有节点的最新状态（用于节点颜色更新）

    GET /api/monitor/latest
    """
    try:
        import models
        from sqlalchemy import desc, func

        # 获取所有Unit节点
        nodes = db.query(models.ProcessNode).filter(
            models.ProcessNode.node_type == "Unit"
        ).all()

        node_status = []
        for node in nodes:
            # 获取该节点最新测量值
            latest = db.query(models.Measurement).filter(
                models.Measurement.node_code == node.code,
                models.Measurement.param_code == "temp"
            ).order_by(desc(models.Measurement.timestamp)).first()

            if latest:
                # 简化版：根据温度判断Cpk（实际应调用SPC计算）
                temp = float(latest.value)
                if temp > 84.0:
                    status = "CRITICAL"
                    cpk = 0.6
                elif temp > 82.0:
                    status = "WARNING"
                    cpk = 1.0
                else:
                    status = "NORMAL"
                    cpk = 1.5

                node_status.append({
                    "node_code": node.code,
                    "current_value": temp,
                    "cpk": cpk,
                    "status": status
                })

        return {
            "nodes": node_status,
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/api/instructions/generate-today")
def generate_today_instructions(db: Session = Depends(get_db)):
    """
    生成今日工艺指令（演示用）

    POST /api/instructions/generate-today
    """
    try:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        # 检查是否已有今日指令
        existing = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today
        ).all()

        if existing:
            # 删除旧指令
            for inst in existing:
                db.delete(inst)
            db.commit()

        # 生成示例指令
        instructions_data = [
            {
                "target_date": today,
                "role": "Operator",
                "content": "检测到E04 醇提罐温度异常（当前85.5℃），建议将蒸汽阀开度从50%调至45%",
                "priority": "HIGH",
                "evidence": {"current_value": 85.5, "target_value": 82.0, "cpk": 0.85},
                "action_code": "ADJUST_TEMP",
                "batch_id": "BATCH-001",
                "node_code": "E04",
                "param_code": "temp",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "QA",
                "content": "E04 醇提罐温度Cpk=0.85低于临界值1.33，请对批次BATCH-001启动偏差调查流程",
                "priority": "HIGH",
                "evidence": {"cpk": 0.85, "threshold": 1.33},
                "action_code": "DEV_INVESTIGATION",
                "batch_id": "BATCH-001",
                "node_code": "E04",
                "param_code": "temp",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "Operator",
                "content": "C01 混合机液位偏低（当前35%），请检查进料阀是否正常",
                "priority": "MEDIUM",
                "evidence": {"current_value": 35, "threshold": 40},
                "action_code": "CHECK_LEVEL",
                "batch_id": "BATCH-002",
                "node_code": "C01",
                "param_code": "level",
                "status": "Pending"
            },
            {
                "target_date": today,
                "role": "TeamLeader",
                "content": "E03 投料站即将到清洁周期（已运行23小时），请安排清洁计划",
                "priority": "LOW",
                "evidence": {"run_hours": 23, "max_hours": 24},
                "action_code": "SCHEDULE_CLEAN",
                "batch_id": None,
                "node_code": "E03",
                "param_code": None,
                "status": "Pending"
            }
        ]

        # 保存到数据库
        for inst_data in instructions_data:
            record = models.DailyInstruction(**inst_data)
            db.add(record)

        db.commit()

        return {
            "success": True,
            "message": f"已生成 {len(instructions_data)} 条今日工艺指令",
            "count": len(instructions_data),
            "date": today
        }
    except Exception as e:
        return {"error": str(e), "success": False}


# ============================================
# LSS 工具箱 API 端点
# ============================================

from routers import lss_router
app.include_router(lss_router)


# ============================================
# Demo 演示数据管理端点
# ============================================

@app.delete("/api/demo/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    重置演示环境（回到初始状态）

    DELETE /api/demo/reset

    清空内容：
    - 工人填报的测量记录（保留初始演示数据）
    - 工人填报的批次记录（保留 BATCH-DEMO-001）
    - 生成的指令（保留初始示例指令）

    保留内容：
    - ProcessNode (流程节点)
    - ProcessEdge (流向)
    - ParameterDef (参数定义)
    - RiskNode/RiskEdge (风险图谱)
    - ActionDef (对策库)
    - 初始演示数据（700条历史测量 + 4条示例指令）
    """
    try:
        from initial_data.demo_init import init_demo_data
        import os

        # 清空工人新增的动态数据（但保留初始演示数据）
        # 删除非 BATCH-DEMO-001 的批次
        db.query(models.Batch).filter(
            models.Batch.id != "BATCH-DEMO-001"
        ).delete()

        # 删除 BATCH-DEMO-001 以外的测量记录（保留初始700条）
        db.query(models.Measurement).filter(
            models.Measurement.batch_id != "BATCH-DEMO-001"
        ).delete()

        # 删除今日以外的指令（保留初始示例指令）
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date != today
        ).delete()

        # 清空今日的指令（会由 init_demo_data 重新生成）
        db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today
        ).delete()

        db.commit()

        # 重新初始化演示数据（恢复到初始状态）
        db_path = os.path.join(os.path.dirname(__file__), "lss.db")
        init_demo_data(db_path)

        return {
            "success": True,
            "message": "✅ 演示环境已重置：已恢复到初始演示状态，工人填报数据已清空。"
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@app.post("/api/demo/init-actions")
def init_action_definitions(db: Session = Depends(get_db)):
    """
    初始化对策库数据（演示用）

    POST /api/demo/init-actions

    从 initial_data/actions.csv 加载对策定义到数据库。
    """
    try:
        import csv
        import os

        # 检查是否已有数据
        existing_count = db.query(models.ActionDef).count()
        if existing_count > 0:
            return {
                "success": True,
                "message": f"对策库已存在 {existing_count} 条记录，无需初始化。",
                "count": existing_count
            }

        # 读取 actions.csv
        actions_csv = os.path.join(
            os.path.dirname(__file__),
            "initial_data",
            "actions.csv"
        )

        if not os.path.exists(actions_csv):
            return {
                "success": False,
                "error": f"文件不存在: {actions_csv}"
            }

        with open(actions_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actions_data = list(reader)

        # 插入数据
        for row in actions_data:
            active_str = row.get('active', 'true')
            action = models.ActionDef(
                code=row['code'],
                name=row['name'],
                risk_code=row['risk_code'],
                target_role=row['target_role'],
                instruction_template=row['instruction_template'],
                priority=row['priority'],
                category=row['category'],
                estimated_impact=row.get('estimated_impact', ''),
                active=active_str.lower() == 'true' if active_str else True
            )
            db.add(action)

        db.commit()

        return {
            "success": True,
            "message": f"✅ 已初始化 {len(actions_data)} 条对策定义",
            "count": len(actions_data)
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@app.post("/api/demo/shift-report")
def submit_shift_report(data: dict, db: Session = Depends(get_db)):
    """
    下工填报单（工人填写生产数据）

    POST /api/demo/shift-report
    {
        "batch_id": "WX-20231026",
        "worker_id": "WORKER_007",
        "shift_end_time": "2023-10-26T17:00:00",
        "data": [
            {
                "node_code": "E04",
                "param_code": "temp",
                "value": 98.5,
                "unit": "℃"
            },
            {
                "node_code": "E04",
                "param_code": "pressure",
                "value": 2.5,
                "unit": "MPa"
            },
            {
                "node_code": "E04",
                "param_code": "motor_status",
                "value": "abnormal",
                "unit": "status"
            }
        ]
    }
    """
    try:
        from datetime import datetime

        batch_id_input = data.get("batch_id")

        # 创建或获取批次记录（注意：Batch模型的主键是id，不是batch_id）
        batch = db.query(models.Batch).filter(
            models.Batch.id == batch_id_input
        ).first()

        if not batch:
            batch = models.Batch(
                id=batch_id_input,  # 使用id字段
                product_name="稳心颗粒",
                start_time=datetime.now(),
                status="In Progress"
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

        # 插入测量数据
        measurements = []
        for item in data.get("data", []):
            param_code = item.get("param_code")
            node_code = item.get("node_code")
            raw_value = item["value"]

            # 转换参数代码为全大写P前缀格式: temp -> P_E04_TEMP
            if param_code != "motor_status":  # motor_status保持原样
                param_code = f"P_{node_code}_{param_code.upper()}"

            # 根据参数类型处理值
            # 注意：Measurement.value 字段是 Float 类型，不能存储字符串
            if param_code == "motor_status":
                # 将设备状态转换为数值代码：normal=1.0, abnormal=0.0
                if isinstance(raw_value, str):
                    processed_value = 1.0 if raw_value.lower() == "normal" else 0.0
                else:
                    processed_value = float(raw_value)
            else:
                # 数值型参数转换为float
                processed_value = float(raw_value) if isinstance(raw_value, (int, float, str)) else 0

            record = models.Measurement(
                batch_id=batch.id,  # 外键关联
                node_code=node_code,
                param_code=param_code,
                value=processed_value,
                source_type="SENSOR",  # 标记为传感器数据
                timestamp=datetime.now()
            )
            db.add(record)
            measurements.append(record)

        db.commit()

        # 触发智能分析（模拟夜间批处理）
        from analysis import IntelligentCommander
        commander = IntelligentCommander(db)

        # 生成指令
        print(f"🔍 开始分析 {len(measurements)} 条测量数据...")
        for meas in measurements:
            print(f"  - {meas.node_code}.{meas.param_code} = {meas.value}")

        instructions_generated = commander.generate_instructions_from_data(
            batch_id=batch.id,  # 使用batch.id
            measurements=measurements
        )

        print(f"✅ 分析完成，生成了 {len(instructions_generated)} 条指令")

        return {
            "success": True,
            "message": f"已提交 {len(measurements)} 条数据，生成 {len(instructions_generated)} 条指令",
            "batch_id": batch.id,
            "data_count": len(measurements),
            "instructions_count": len(instructions_generated)
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}


@app.post("/api/demo/login")
def worker_login(data: dict, db: Session = Depends(get_db)):
    """
    工人上工登录（刷卡）

    POST /api/demo/login
    {
        "worker_id": "WORKER_007"
    }
    """
    try:
        from datetime import datetime

        worker_id = data.get("worker_id")
        today = datetime.now().strftime("%Y-%m-%d")

        # 查询今日指派给该工人的指令
        instructions = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today,
            models.DailyInstruction.role.in_(["Operator", worker_id])
        ).order_by(
            models.DailyInstruction.priority.desc(),  # HIGH > MEDIUM > LOW
            models.DailyInstruction.id
        ).all()

        # 查询系统状态概览
        total_pending = db.query(models.DailyInstruction).filter(
            models.DailyInstruction.target_date == today,
            models.DailyInstruction.status == "Pending"
        ).count()

        return {
            "success": True,
            "worker_id": worker_id,
            "worker_name": f"操作工 {worker_id}",
            "login_time": datetime.now().isoformat(),
            "briefing": {
                "total_instructions": len(instructions),
                "pending_count": total_pending,
                "instructions": [
                    {
                        "id": inst.id,
                        "priority": inst.priority,
                        "content": inst.content,
                        "node_code": inst.node_code,
                        "batch_id": inst.batch_id,
                        "evidence": inst.evidence
                    }
                    for inst in instructions
                ]
            }
        }
    except Exception as e:
        return {"error": str(e), "success": False}


# ============================================
# Demo API 端点 (基于真实架构的轻量化实现)
# ============================================

from demo_api import router as demo_router
app.include_router(demo_router)
