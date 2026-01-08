"""工艺图谱API路由

提供工艺流程图和风险图谱的查询接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/api/graph", tags=["工艺图谱"])


@router.get("/structure")
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


@router.get("/risks/tree")
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


@router.get("/nodes/{node_code}/risks")
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
