"""智能分析API路由

提供按人员、批次、工序、车间、时间等多维度的分析接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db

# 导入编排层
from analysis import BlackBeltCommander, ReportFormatter

router = APIRouter(prefix="/api/analysis", tags=["智能分析"])


# ==================== 请求模型 ====================

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


# ==================== 分析接口 ====================

@router.post("/person")
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


@router.post("/batch")
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


@router.get("/batch/{batch_id}/actions")
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


@router.post("/process")
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


@router.post("/workshop")
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


@router.post("/time")
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


@router.post("/daily")
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
