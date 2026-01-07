"""Demo API 路由

专门用于Demo演示的API接口
基于真实架构的轻量化实现
"""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.graph_importer import GraphImporter
from core.notification_center import NotificationCenter
from core.rag_engine import RAGEngine
from ingestion import DataIngestor
from database import SessionLocal
import models

router = APIRouter(prefix="/api/demo", tags=["demo"])


# ==================== 数据模型 ====================

class InitFactoryRequest(BaseModel):
    """初始化工厂请求"""
    reset: bool = True  # 是否重置现有数据


class DataInputRequest(BaseModel):
    """数据填报请求"""
    role: str  # worker | manager
    node_code: str
    measurements: Dict[str, float]


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    use_llm: bool = False  # 是否使用LLM


class RoleReportRequest(BaseModel):
    """角色报告请求"""
    role: str  # worker | manager | qa | teamleader
    time_window: int = 7


# ==================== 功能1: 知识图谱导入 ====================

@router.post("/setup/init")
async def init_factory(request: InitFactoryRequest):
    """初始化工厂 - 从Excel导入知识图谱

    Demo场景: 展示"无中生有"的能力
    """
    try:
        importer = GraphImporter()

        # 如果需要重置
        if request.reset:
            importer.clear_existing_graph()

        # Demo: 直接运行 seed.py (真实场景会解析上传的文件)
        import subprocess
        result = subprocess.run(
            ["python", "seed.py"],
            capture_output=True,
            text=True,
            cwd="/Users/zhoutengye/med/LSS/backend"
        )

        if result.returncode == 0:
            # 查询统计数据
            db = SessionLocal()
            node_count = db.query(models.ProcessNode).count()
            param_count = db.query(models.ParameterDef).count()
            risk_count = db.query(models.RiskNode).count()
            db.close()

            return {
                "success": True,
                "message": "工厂模型构建完成",
                "stats": {
                    "nodes_count": node_count,
                    "parameters_count": param_count,
                    "risks_count": risk_count
                }
            }
        else:
            return {
                "success": False,
                "message": f"初始化失败: {result.stderr}"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"错误: {str(e)}"
        }


@router.post("/setup/upload")
async def upload_graph_file(file: UploadFile = File(...)):
    """上传图谱文件 (Excel/CSV)

    真实能力: 解析上传的文件并构建图谱
    Demo能力: 接收文件并返回模拟进度
    """
    try:
        # TODO: 真实实现
        # 1. 保存上传文件
        # 2. 调用 GraphImporter.import_from_excel()
        # 3. 返回构建结果

        return {
            "success": True,
            "message": "文件上传成功，正在解析...",
            "progress": 100,
            "filename": file.filename
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"上传失败: {str(e)}"
        }


# ==================== 功能2: 数据填报 ====================

@router.post("/input/submit")
async def submit_data(request: DataInputRequest):
    """提交测量数据

    Demo场景: 模拟车间主任/操作工填报数据
    """
    try:
        db = SessionLocal()
        ingestor = DataIngestor(db)

        # 根据角色选择不同的处理方式
        if request.role == "worker":
            # 操作工: 直接录入测量数据
            batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d')}"

            for param_code, value in request.measurements.items():
                ingestor.ingest_single_point(
                    batch_id=batch_id,
                    node_code=request.node_code,
                    param_code=param_code,
                    value=value,
                    source="MANUAL"
                )

            db.close()

            return {
                "success": True,
                "message": f"已成功录入 {len(request.measurements)} 个参数数据",
                "batch_id": batch_id
            }

        elif request.role == "manager":
            # 车间主任: 录入检查项 (TODO: 扩展数据模型)
            return {
                "success": True,
                "message": "检查项已记录"
            }

        db.close()
        return {
            "success": False,
            "message": "未知角色"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"提交失败: {str(e)}"
        }


@router.get("/input/form/{node_code}")
async def get_input_form(node_code: str):
    """获取数据填报表单配置

    根据节点返回需要填写的参数列表
    """
    try:
        db = SessionLocal()

        # 查询该节点的所有参数定义
        params = db.query(models.ParameterDef).filter(
            models.ParameterDef.node_code == node_code
        ).all()

        form_config = {
            "node_code": node_code,
            "parameters": [
                {
                    "code": p.code,
                    "name": p.name,
                    "type": p.param_type,  # Input/Control/Output
                    "unit": p.unit,
                    "usl": p.usl,
                    "lsl": p.lsl,
                    "target": p.target
                }
                for p in params
            ]
        }

        db.close()

        return {
            "success": True,
            "form": form_config
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"获取表单失败: {str(e)}"
        }


# ==================== 功能3: 角色分析报告 ====================

@router.post("/report")
async def get_role_report(request: RoleReportRequest):
    """获取角色报告

    Demo场景: 展示"千人千面"的报告能力
    """
    try:
        center = NotificationCenter()

        if request.role == "worker":
            # 操作工: 获取待执行指令
            notifications = center.get_worker_notifications()

            return {
                "success": True,
                "type": "instruction",
                "role": "worker",
                "data": {
                    "title": "今日行动指令",
                    "items": notifications
                }
            }

        elif request.role == "manager":
            # 经理: 获取洞察报告
            report = center.get_manager_report(request.time_window)

            return {
                "success": True,
                "type": "insight",
                "role": "manager",
                "data": report
            }

        elif request.role == "qa":
            # QA: 获取质量相关通知
            notifications = center.get_qa_notifications()

            return {
                "success": True,
                "type": "instruction",
                "role": "qa",
                "data": {
                    "title": "质量检查任务",
                    "items": notifications
                }
            }

        elif request.role == "teamleader":
            # 班长: 获取班组任务
            notifications = center.get_teamleader_notifications()

            return {
                "success": True,
                "type": "instruction",
                "role": "teamleader",
                "data": {
                    "title": "班组任务",
                    "items": notifications
                }
            }

        return {
            "success": False,
            "message": "未知角色"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"获取报告失败: {str(e)}"
        }


# ==================== 功能4: AI知识问答 ====================

@router.post("/chat")
async def chat(request: ChatRequest):
    """AI知识问答

    Demo场景: 展示RAG知识库能力
    """
    try:
        engine = RAGEngine()

        # Demo: 预加载一些知识
        if len(engine.document_store) == 0:
            engine.load_text_chunks([
                {
                    "text": "提取温度的标准范围是80-90℃，目标值为85℃。温度过高会导致皂苷分解，过低则提取效率下降。",
                    "source": "SOP-提取工艺"
                },
                {
                    "text": "Cpk (过程能力指数) ≥ 1.33 表示过程能力充足，Cpk < 1.0 表示过程能力不足。计算公式: Cpk = min((USL-μ)/3σ, (μ-LSL)/3σ)",
                    "source": "LSS手册-统计过程控制"
                },
                {
                    "text": "当前最大的风险是'设备清洁不彻底'，历史数据显示其导致质量问题的概率为5%。建议加强清洁验证。",
                    "source": "风险分析报告"
                }
            ])

        # 搜索并回答
        result = engine.ask(request.question, use_llm=request.use_llm)

        return {
            "success": True,
            "question": request.question,
            "answer": result["answer"],
            "sources": result.get("sources", [])
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"问答失败: {str(e)}"
        }


@router.get("/chat/knowledge")
async def get_knowledge_base():
    """获取知识库状态

    Demo场景: 展示知识库中有多少文档
    """
    try:
        engine = RAGEngine()

        return {
            "success": True,
            "stats": {
                "document_count": len(engine.document_store),
                "last_updated": datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"获取知识库状态失败: {str(e)}"
        }
