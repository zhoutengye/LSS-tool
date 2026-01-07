"""LSS工具API路由

提供所有LSS分析工具的RESTful API接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
import models
from core.registry import registry, register_all_tools

router = APIRouter(prefix="/api/lss", tags=["LSS工具"])

# 注册所有工具
register_all_tools()

# ==================== 请求模型 ====================

class ToolRunRequest(BaseModel):
    """工具运行请求"""
    data: List[float] | List[Dict] | Dict[str, List[float]]  # 支持多种数据格式
    config: Optional[Dict[str, Any]] = {}


class SPCRequest(BaseModel):
    """SPC分析请求"""
    param_code: str  # 参数代码
    node_code: Optional[str] = None  # 节点代码（可选，用于筛选）
    batch_id: Optional[str] = None  # 批次ID（可选）
    limit: Optional[int] = 50  # 数据量限制
    usl: Optional[float] = None  # 规格上限
    lsl: Optional[float] = None  # 规格下限
    target: Optional[float] = None  # 目标值


class ParetoRequest(BaseModel):
    """帕累托图请求"""
    categories: List[Dict[str, Any]]  # [{"category": "温度异常", "count": 15}, ...]
    threshold: Optional[float] = 0.8  # 累计占比阈值


class HistogramRequest(BaseModel):
    """直方图请求"""
    param_code: str  # 参数代码
    node_code: Optional[str] = None
    batch_id: Optional[str] = None
    limit: Optional[int] = 100
    bins: Optional[int] = 10
    usl: Optional[float] = None
    lsl: Optional[float] = None


class BoxplotRequest(BaseModel):
    """箱线图请求"""
    param_codes: List[str]  # 多个参数代码，用于对比
    node_codes: Optional[List[str]] = None  # 节点代码列表
    batch_id: Optional[str] = None
    limit_per_series: Optional[int] = 50


# ==================== 通用工具接口 ====================

@router.get("/tools")
def list_tools():
    """列出所有已注册的LSS工具

    Returns:
        工具列表及其元数据
    """
    tools = registry.list_tools()

    return {
        "success": True,
        "tools": [
            {
                "key": key,
                "name": tool["name"],
                "category": tool["category"],
                "description": tool["description"]
            }
            for key, tool in tools.items()
        ]
    }


@router.post("/tools/{tool_name}/run")
def run_tool(tool_name: str, request: ToolRunRequest):
    """运行指定工具

    Args:
        tool_name: 工具名称 (spc, pareto, histogram, boxplot)
        request: 包含数据和配置的请求体

    Returns:
        工具分析结果
    """
    try:
        # 获取工具
        tool = registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 未找到")

        # 运行工具
        result = tool.run(request.data, request.config or {})

        return result

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }


# ==================== SPC分析接口 ====================

@router.post("/spc/analyze")
def analyze_spc(request: SPCRequest, db: Session = Depends(get_db)):
    """SPC过程能力分析

    根据参数代码查询数据库中的测量数据，进行SPC分析。

    POST /api/lss/spc/analyze
    {
        "param_code": "P_E01_TEMP",
        "node_code": "E01",
        "limit": 50,
        "usl": 90.0,
        "lsl": 80.0,
        "target": 85.0
    }
    """
    try:
        # 构建查询
        query = db.query(models.Measurement).filter(
            models.Measurement.param_code == request.param_code
        )

        if request.node_code:
            query = query.filter(models.Measurement.node_code == request.node_code)

        if request.batch_id:
            query = query.filter(models.Measurement.batch_id == request.batch_id)

        # 获取数据
        measurements = query.order_by(models.Measurement.timestamp).limit(request.limit).all()

        if not measurements:
            return {
                "success": False,
                "errors": [f"未找到参数 {request.param_code} 的测量数据"]
            }

        data = [float(m.value) for m in measurements]

        # 获取参数定义（规格限）
        param_def = db.query(models.ParameterDef).filter(
            models.ParameterDef.code == request.param_code
        ).first()

        config = {
            "usl": request.usl or param_def.usl if param_def else None,
            "lsl": request.lsl or param_def.lsl if param_def else None,
            "target": request.target or param_def.target if param_def else None
        }

        # 运行SPC分析
        spc_tool = registry.get_tool("spc")
        result = spc_tool.run(data, config)

        # 添加元数据
        result["metadata"] = {
            "param_code": request.param_code,
            "node_code": request.node_code,
            "batch_id": request.batch_id,
            "data_points": len(data),
            "time_range": {
                "start": measurements[0].timestamp.isoformat(),
                "end": measurements[-1].timestamp.isoformat()
            }
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }


# ==================== 帕累托图接口 ====================

@router.post("/pareto/analyze")
def analyze_pareto(request: ParetoRequest):
    """帕累托图分析

    POST /api/lss/pareto/analyze
    {
        "categories": [
            {"category": "温度异常", "count": 45},
            {"category": "压力异常", "count": 28},
            ...
        ],
        "threshold": 0.8
    }
    """
    try:
        pareto_tool = registry.get_tool("pareto")

        config = {
            "threshold": request.threshold
        }

        result = pareto_tool.run(request.categories, config)
        return result

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }


@router.get("/pareto/demo")
def get_pareto_demo_data():
    """获取帕累托图演示数据

    Returns:
        预设的故障类别数据，用于Demo演示
    """
    demo_data = [
        {"category": "温度异常", "count": 45},
        {"category": "压力异常", "count": 28},
        {"category": "液位异常", "count": 22},
        {"category": "流量异常", "count": 18},
        {"category": "pH值异常", "count": 15},
        {"category": "真空度异常", "count": 12},
        {"category": "密度异常", "count": 10},
        {"category": "设备故障", "count": 8},
        {"category": "人为误差", "count": 6},
        {"category": "其他原因", "count": 5},
    ]

    return {
        "success": True,
        "data": demo_data
    }


# ==================== 直方图接口 ====================

@router.post("/histogram/analyze")
def analyze_histogram(request: HistogramRequest, db: Session = Depends(get_db)):
    """直方图分析

    POST /api/lss/histogram/analyze
    {
        "param_code": "P_C01_TEMP",
        "node_code": "C01",
        "limit": 100,
        "bins": 10,
        "usl": 70.0,
        "lsl": 60.0
    }
    """
    try:
        # 构建查询
        query = db.query(models.Measurement).filter(
            models.Measurement.param_code == request.param_code
        )

        if request.node_code:
            query = query.filter(models.Measurement.node_code == request.node_code)

        if request.batch_id:
            query = query.filter(models.Measurement.batch_id == request.batch_id)

        # 获取数据
        measurements = query.order_by(models.Measurement.timestamp).limit(request.limit).all()

        if not measurements:
            return {
                "success": False,
                "errors": [f"未找到参数 {request.param_code} 的测量数据"]
            }

        data = [float(m.value) for m in measurements]

        # 获取参数定义
        param_def = db.query(models.ParameterDef).filter(
            models.ParameterDef.code == request.param_code
        ).first()

        config = {
            "bins": request.bins,
            "usl": request.usl or param_def.usl if param_def else None,
            "lsl": request.lsl or param_def.lsl if param_def else None
        }

        # 运行直方图分析
        hist_tool = registry.get_tool("histogram")
        result = hist_tool.run(data, config)

        # 添加元数据
        result["metadata"] = {
            "param_code": request.param_code,
            "node_code": request.node_code,
            "data_points": len(data)
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }


# ==================== 箱线图接口 ====================

@router.post("/boxplot/analyze")
def analyze_boxplot(request: BoxplotRequest, db: Session = Depends(get_db)):
    """箱线图分析（多组对比）

    POST /api/lss/boxplot/analyze
    {
        "param_codes": ["P_E01_TEMP", "P_E02_TEMP", "P_E03_TEMP", "P_E04_TEMP"],
        "limit_per_series": 50
    }
    """
    try:
        multi_series_data = {}

        # 查询每个参数的数据
        for param_code in request.param_codes:
            query = db.query(models.Measurement).filter(
                models.Measurement.param_code == param_code
            )

            if request.batch_id:
                query = query.filter(models.Measurement.batch_id == request.batch_id)

            measurements = query.order_by(models.Measurement.timestamp).limit(request.limit_per_series).all()

            if measurements:
                # 使用参数名称作为系列名
                series_name = param_code
                multi_series_data[series_name] = [float(m.value) for m in measurements]

        if not multi_series_data:
            return {
                "success": False,
                "errors": ["未找到任何测量数据"]
            }

        # 运行箱线图分析
        boxplot_tool = registry.get_tool("boxplot")
        result = boxplot_tool.run(multi_series_data, {})

        # 添加元数据
        result["metadata"] = {
            "series_count": len(multi_series_data),
            "param_codes": request.param_codes
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }


@router.get("/boxplot/demo")
def get_boxplot_demo_data():
    """获取箱线图演示数据配置

    Returns:
        预设的多车间对比配置
    """
    demo_config = {
        "param_codes": [
            "P_E01_TEMP",
            "P_E02_TEMP",
            "P_E03_TEMP",
            "P_E04_TEMP"
        ],
        "description": "对比4个提取罐的温度波动",
        "limit_per_series": 50
    }

    return {
        "success": True,
        "config": demo_config
    }


# ==================== 综合演示接口 ====================

@router.get("/demo/scenarios")
def list_demo_scenarios():
    """列出所有演示场景

    Returns:
        演示场景列表
    """
    scenarios = [
        {
            "id": "qa_meeting",
            "name": "QA质量分析会",
            "description": "展示故障类别分布，识别关键问题",
            "tool": "pareto",
            "endpoint": "/api/lss/pareto/demo",
            "action": "运行帕累托分析"
        },
        {
            "id": "process_optimization",
            "name": "工艺参数调优",
            "description": "查看参数分布形态，计算过程能力",
            "tool": "histogram",
            "endpoint": "/api/lss/histogram/analyze",
            "action": "分析C01浓缩温度分布"
        },
        {
            "id": "workshop_comparison",
            "name": "车间对比会",
            "description": "对比多个车间的过程波动，识别最佳实践",
            "tool": "boxplot",
            "endpoint": "/api/lss/boxplot/demo",
            "action": "对比4个提取罐的温度"
        },
        {
            "id": "daily_monitoring",
            "name": "日常监控",
            "description": "实时监控过程参数，预警异常",
            "tool": "spc",
            "endpoint": "/api/lss/spc/analyze",
            "action": "分析E01温度过程能力"
        }
    ]

    return {
        "success": True,
        "scenarios": scenarios
    }


@router.get("/demo/summary")
def get_demo_summary(db: Session = Depends(get_db)):
    """获取演示环境摘要信息

    Returns:
        演示数据的统计信息
    """
    try:
        # 统计测量数据
        total_measurements = db.query(models.Measurement).count()

        # 统计批次数
        total_batches = db.query(models.Batch).count()

        # 统计节点数
        total_nodes = db.query(models.ProcessNode).filter(
            models.ProcessNode.node_type == "Unit"
        ).count()

        # 统计参数数量
        total_params = db.query(models.ParameterDef).count()

        # 获取最近的测量时间
        latest_measurement = db.query(models.Measurement).order_by(
            models.Measurement.timestamp.desc()
        ).first()

        return {
            "success": True,
            "summary": {
                "total_measurements": total_measurements,
                "total_batches": total_batches,
                "total_nodes": total_nodes,
                "total_params": total_params,
                "latest_measurement": latest_measurement.timestamp.isoformat() if latest_measurement else None
            },
            "tools_available": ["SPC", "Pareto", "Histogram", "Boxplot"],
            "demo_scenarios": 4
        }

    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }
