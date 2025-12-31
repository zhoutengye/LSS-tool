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
from database import engine, get_db
import models

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

    # 分离区块和单元
    blocks = [n for n in nodes if n.node_type == "Block"]
    units = [n for n in nodes if n.node_type == "Unit"]

    flow_nodes = []
    flow_edges = []

    # 先放置区块（水平排列，间距大）
    block_spacing = 500
    for idx, block in enumerate(blocks):
        flow_nodes.append({
            "id": str(block.id),
            "data": {
                "label": block.name,
                "code": block.code,
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
                    "label": unit.name,
                    "code": unit.code,
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
