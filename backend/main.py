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

# 跨域配置 (让前端能连上)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
