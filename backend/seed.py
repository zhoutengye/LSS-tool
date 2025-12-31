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

    # 3. 遍历总图，逐个建立区块
    for _, row in df_master.iterrows():
        # A. 创建父节点 (Block)
        block = models.ProcessNode(
            code=row['block_code'],
            name=row['block_name'],
            node_type="Block"
        )
        db.add(block)
        db.commit() # 获取 block.id

        # B. 建立区块间的连线 (Block -> Block)
        if pd.notna(row['next_block_code']):
            edge = models.ProcessEdge(
                source_code=row['block_code'],
                target_code=row['next_block_code'],
                name="区块流转"
            )
            db.add(edge)

        # C. 钻入子文件夹，处理子流程
        sub_folder = os.path.join(base_path, str(row['folder_name']))
        if os.path.exists(sub_folder):
            print(f"  └── 正在加载子流程: {row['folder_name']}")
            seed_sub_folder(db, sub_folder, block.id)
        else:
            print(f"  ⚠️ 警告: 文件夹 {row['folder_name']} 不存在，跳过子流程")

    db.commit()
    print("✅ 所有图谱构建完成！")
    db.close()

# 辅助函数：处理单个子文件夹
def seed_sub_folder(db, folder_path, parent_id):
    # 1. 读取 Nodes
    f_nodes = os.path.join(folder_path, "nodes.csv")
    if os.path.exists(f_nodes):
        df_nodes = pd.read_csv(f_nodes)
        for _, n_row in df_nodes.iterrows():
            node = models.ProcessNode(
                code=n_row['code'],
                name=n_row['name'],
                node_type=n_row['type'],
                parent_id=parent_id # 挂在当前 Block 下
            )
            db.add(node)
        db.commit()

    # 2. 读取 Params
    f_params = os.path.join(folder_path, "params.csv")
    if os.path.exists(f_params):
        df_params = pd.read_csv(f_params)
        df_params = df_params.where(pd.notnull(df_params), None) # 处理空值

        for _, p_row in df_params.iterrows():
            # 找节点
            node = db.query(models.ProcessNode).filter_by(code=p_row['node']).first()
            if node:
                # 辅助函数：安全转换浮点数
                def safe_float(val):
                    """尝试转换为浮点数，失败返回 None"""
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

    # 3. 读取 Flows (内部连线)
    f_flows = os.path.join(folder_path, "flows.csv")
    if os.path.exists(f_flows):
        df_flows = pd.read_csv(f_flows)
        for _, f_row in df_flows.iterrows():
            # 只有当有连线时才添加
            if pd.notna(f_row['source']) and pd.notna(f_row['target']):
                edge = models.ProcessEdge(
                    source_code=f_row['source'],
                    target_code=f_row['target'],
                    name=f_row['name']
                )
                db.add(edge)

    db.commit()

if __name__ == "__main__":
    seed_hierarchical()
