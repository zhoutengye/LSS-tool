LSS - 药品制造工艺仿真系统 文档
=====================================

欢迎来到 LSS 系统的官方文档。本系统是一个基于知识图谱的药品制造工艺仿真与优化平台。

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   architecture
   backend
   frontend
   api
   todo

系统概览
--------

LSS 系统通过 IDEF0 层级建模方法，将药品制造过程分解为：
- **Block (区块)**: 四大车间（前处理、提取纯化、制剂成型、内包外包）
- **Unit (单元)**: 每个车间内的具体设备
- **Parameter (参数)**: 每个设备的工艺参数（控制、输出、输入）

核心功能
--------

* 知识图谱可视化（React Flow）
* 动态参数配置与仿真
* 实时数据监控
* LSS 超级工具箱（SPC、风险分析、优化）
* 批次管理与数据采集

技术栈
------

**后端**:
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- SQLite/PostgreSQL (数据库)

**前端**:
- React + Vite
- React Flow (图谱可视化)
- Ant Design (UI 组件)

快速开始
----------

后端启动：

.. code-block:: bash

   cd backend
   conda activate med
   uvicorn main:app --reload --host 127.0.0.1 --port 8000

前端启动：

.. code-block:: bash

   cd frontend
   npm install
   npm run dev

索引与表格
==========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
