"""数据库配置模块

本模块配置 SQLAlchemy 数据库连接和会话管理。

数据库使用 SQLite 存储在 backend/lss_factory.db。

Example:
    >>> from database import SessionLocal
    >>> db = SessionLocal()
    >>> # 使用 db 进行查询...
    >>> db.close()
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库文件将生成在 backend 目录下
SQLALCHEMY_DATABASE_URL = "sqlite:///./lss_factory.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话的依赖注入函数

    用于 FastAPI 依赖注入，自动管理会话生命周期。

    Yields:
        SQLAlchemy 数据库会话

    Example:
        >>> @app.get("/api/data")
        >>> def get_data(db: Session = Depends(get_db)):
        ...     return db.query(models.ProcessNode).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
