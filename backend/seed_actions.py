"""导入对策库（ActionDef）种子数据

从 CSV 文件导入标准化应对措施到数据库。
"""

import csv
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models


def import_actions_from_csv(csv_path: str):
    """
    从 CSV 文件导入对策库

    CSV 格式：
        code,name,risk_code,target_role,instruction_template,priority,category,estimated_impact,active

    Args:
        csv_path: CSV 文件路径
    """
    db = SessionLocal()

    try:
        # 清空现有数据（可选）
        # db.query(models.ActionDef).delete()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            count = 0
            for row in reader:
                # 检查是否已存在
                existing = db.query(models.ActionDef).filter(
                    models.ActionDef.code == row['code']
                ).first()

                if existing:
                    print(f"⚠️  对策 {row['code']} 已存在，跳过")
                    continue

                # 创建新对策
                action = models.ActionDef(
                    code=row['code'],
                    name=row['name'],
                    risk_code=row['risk_code'],
                    target_role=row['target_role'],
                    instruction_template=row['instruction_template'],
                    priority=row['priority'],
                    category=row['category'],
                    estimated_impact=row['estimated_impact'],
                    active=row['active'].lower() == 'true'
                )

                db.add(action)
                count += 1
                print(f"✅ 导入对策: {row['code']} - {row['name']}")

            db.commit()
            print(f"\n🎉 成功导入 {count} 条对策！")

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    csv_path = "initial_data/actions.csv"

    if not Path(csv_path).exists():
        print(f"❌ 文件不存在: {csv_path}")
        sys.exit(1)

    print("📦 开始导入对策库...")
    import_actions_from_csv(csv_path)
