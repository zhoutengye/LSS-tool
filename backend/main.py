"""LSS 系统主程序

FastAPI 后端服务，提供 RESTful API 接口。

主要功能:
- 知识图谱查询 (工序节点、工艺流向)
- 批次数据管理
- 分析工具调用
- 前端可视化数据支持

API 端点:
- GET /: 系统状态检查
- GET /api/test: 测试连接
- POST /api/simulate: 简单仿真

所有业务逻辑已拆分到 routers/ 目录下的独立模块中。

Example:
    >>> import uvicorn
    >>> uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from pathlib import Path
import models

# 启动时自动建表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wexin LSS Engine")


# ============================================
# 启动事件：初始化演示数据
# ============================================

@app.on_event("startup")
async def startup_event():
    """应用启动时自动初始化演示数据"""
    from initial_data.demo_init import init_demo_data

    # 获取数据库路径（与 database.py 中的配置保持一致）
    db_path = str(Path(__file__).parent / "lss.db")

    print("\n" + "="*60)
    print("🚀 LSS 系统启动中...")
    print("="*60)

    # 初始化演示数据
    init_demo_data(db_path)

    print("="*60)
    print("✅ LSS 系统启动完成！")
    print("="*60 + "\n")

# 跨域配置 (让前端能连上)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 当使用 "*" 时必须设为 False
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)


# ============================================
# 基础端点 (保留在 main.py 中)
# ============================================

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


# ============================================
# 注册所有路由模块
# ============================================

from routers import lss_router
app.include_router(lss_router)  # LSS工具箱

# 注册新的业务router（注意：这些router已经包含了prefix）
from routers import graph, analysis, instructions, monitoring, demo
app.include_router(graph.router)
app.include_router(analysis.router)
app.include_router(instructions.router)
app.include_router(monitoring.router)
app.include_router(demo.router)
