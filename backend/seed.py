import pandas as pd
import os
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

def seed_hierarchical():
    db = SessionLocal()
    base_path = "initial_data"

    # 1. 清理
    print("🧹 清理旧数据...")
    db.query(models.RiskEdge).delete()
    db.query(models.RiskNode).delete()
    db.query(models.ProcessEdge).delete()
    db.query(models.ParameterDef).delete()
    db.query(models.ProcessNode).delete()
    db.commit()

    # 2. 读取总图 (Master Flow)
    master_file = os.path.join(base_path, "master_flow.csv")
    if not os.path.exists(master_file):
        print("❌ 错误：找不到总图 master_flow.csv")
        return

    df_master = pd.read_csv(master_file)
    print(f"📖 读取总图：发现 {len(df_master)} 个区块...")

    # ==========================================
    # 第一阶段：构建所有节点 (Blocks + Units)
    # ==========================================
    print("\n🏗️ Phase 1: 构建所有节点...")
    for _, row in df_master.iterrows():
        # A. 创建父节点 (Block)
        block = models.ProcessNode(
            code=row['block_code'],
            name=row['block_name'],
            node_type="Block"
        )
        db.add(block)
        db.commit() # 获取 block.id

        # B. 钻入子文件夹，创建 Unit/Resource 节点
        sub_folder = os.path.join(base_path, str(row['folder_name']))
        if os.path.exists(sub_folder):
            print(f"  └── 创建节点: {row['folder_name']}")
            seed_nodes(db, sub_folder, block.id)
        else:
            print(f"  ⚠️ 警告: 文件夹 {row['folder_name']} 不存在")

    # ==========================================
    # 第二阶段：填充细节 (Params, Risks, Flows)
    # ==========================================
    print("\n🔗 Phase 2: 连接管路与填充参数...")

    # 2.1 Block-to-Block 连线
    for _, row in df_master.iterrows():
        if pd.notna(row['next_block_code']):
            edge = models.ProcessEdge(
                source_code=row['block_code'],
                target_code=row['next_block_code'],
                name="区块流转"
            )
            db.add(edge)
    db.commit()

    # 2.2 遍历子文件夹，填充参数和管路
    for _, row in df_master.iterrows():
        sub_folder = os.path.join(base_path, str(row['folder_name']))
        if os.path.exists(sub_folder):
            print(f"  └── 处理细节: {row['folder_name']}")
            seed_params(db, sub_folder)
            seed_flows(db, sub_folder)
            seed_risks(db, sub_folder)

    db.commit()
    print("\n✅ 全厂贯通完成！")
    db.close()

# 辅助函数：只创建节点
def seed_nodes(db, folder_path, parent_id):
    f_nodes = os.path.join(folder_path, "nodes.csv")
    if os.path.exists(f_nodes):
        df_nodes = pd.read_csv(f_nodes)
        for _, n_row in df_nodes.iterrows():
            node = models.ProcessNode(
                code=n_row['code'],
                name=n_row['name'],
                node_type=n_row['type'],
                parent_id=parent_id
            )
            db.add(node)
        db.commit()

# 辅助函数：填充参数
def seed_params(db, folder_path):
    f_params = os.path.join(folder_path, "params.csv")
    if os.path.exists(f_params):
        df_params = pd.read_csv(f_params)
        df_params = df_params.where(pd.notnull(df_params), None)

        for _, p_row in df_params.iterrows():
            # 找节点
            node = db.query(models.ProcessNode).filter_by(code=p_row['node']).first()
            if node:
                def safe_float(val):
                    """安全转换浮点数"""
                    if val is None or pd.isna(val):
                        return None
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return None

                param = models.ParameterDef(
                    node_id=node.id,
                    code=p_row['param'],
                    name=p_row['name'],
                    role=p_row['role'],
                    unit=p_row.get('unit'),
                    usl=safe_float(p_row.get('usl')),
                    lsl=safe_float(p_row.get('lsl')),
                    target=safe_float(p_row.get('target')),
                    is_material=bool(p_row.get('is_material', False)),
                    data_type=p_row.get('data_type', 'Scalar')
                )
                db.add(param)
        db.commit()

# 辅助函数：连接管路 (包括跨车间)
def seed_flows(db, folder_path):
    f_flows = os.path.join(folder_path, "flows.csv")
    if os.path.exists(f_flows):
        df_flows = pd.read_csv(f_flows)
        for _, f_row in df_flows.iterrows():
            if pd.notna(f_row['source']) and pd.notna(f_row['target']):
                # 现在所有节点都已创建，跨车间连线能找到了
                src = db.query(models.ProcessNode).filter_by(code=f_row['source']).first()
                tgt = db.query(models.ProcessNode).filter_by(code=f_row['target']).first()

                if src and tgt:
                    edge = models.ProcessEdge(
                        source_code=f_row['source'],
                        target_code=f_row['target'],
                        name=f_row['name']
                    )
                    db.add(edge)
                else:
                    print(f"    ⚠️ 警告: 连线失败 {f_row['source']} -> {f_row['target']} (节点未找到)")
        db.commit()

# 辅助函数：填充风险节点和连线
def seed_risks(db, folder_path):
    # 1. 读取风险节点
    f_risks = os.path.join(folder_path, "risks.csv")
    if os.path.exists(f_risks):
        df_risks = pd.read_csv(f_risks)
        df_risks = df_risks.where(pd.notnull(df_risks), None)

        for _, row in df_risks.iterrows():
            existing = db.query(models.RiskNode).filter_by(code=row['code']).first()
            if not existing:
                risk = models.RiskNode(
                    code=row['code'],
                    name=row['name'],
                    category=row['category'],
                    base_probability=float(row['prob']) if row['prob'] else 0.01
                )
                db.add(risk)
        db.commit()

    # 2. 读取风险连线
    f_r_edges = os.path.join(folder_path, "risk_edges.csv")
    if os.path.exists(f_r_edges):
        df_r_edges = pd.read_csv(f_r_edges)
        for _, row in df_r_edges.iterrows():
            existing = db.query(models.RiskEdge).filter_by(
                source_code=row['source'],
                target_code=row['target']
            ).first()
            if not existing:
                edge = models.RiskEdge(
                    source_code=row['source'],
                    target_code=row['target']
                )
                db.add(edge)
        db.commit()

if __name__ == "__main__":
    seed_hierarchical()
