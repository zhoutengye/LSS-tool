"""监控数据API路由

提供实时监控数据和历史趋势查询接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
import models

router = APIRouter(prefix="/api/monitor", tags=["监控数据"])


@router.get("/node/{node_code}")
def get_node_monitoring(node_code: str, db: Session = Depends(get_db)):
    """
    获取节点监控数据（实时SCADA或历史数据）

    GET /api/monitor/node/E04
    """
    try:
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


@router.get("/latest")
def get_all_latest_status(db: Session = Depends(get_db)):
    """
    获取所有节点的最新状态（用于节点颜色更新）

    GET /api/monitor/latest
    """
    try:
        from sqlalchemy import func

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
