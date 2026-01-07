LSS - 药品制造工艺仿真系统 文档
=====================================

欢迎来到 LSS 系统的官方文档。本系统是一个基于知识图谱的药品制造工艺仿真与优化平台。

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   architecture
   backend
   frontend
   toolbox
   ai_expert
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

**三大功能页面**:

* **工艺监控** - 知识图谱可视化（React Flow）、实时数据监控、批次管理
* **LSS工具箱** - 4个精益六西格玛分析工具（帕累托图、直方图、箱线图、SPC控制图）
* **AI黑带专家** - 自动工具链分析、智能诊断报告、DMAIC改进路径生成

**技术亮点**:

* 知识图谱可视化（React Flow）
* 实时/仿真双模式监控
* 工艺指令系统（支持多状态过滤）
* LSS 分析工具箱（4个工具已实现）
* AI驱动的智能综合分析（自动串联多个工具，生成专家级诊断报告）

技术栈
------

**后端**:
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- SQLite/PostgreSQL (数据库)

**前端**:
- React 19.2.0 + Vite 7.2.4
- React Flow (图谱可视化)
- Ant Design 6.1.3 (UI 组件)
- ECharts 6.0.0 (数据可视化)

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
   source ~/.nvm/nvm.sh  # 如果使用 nvm
   nvm use 20           # Vite 7.2.4 需要 Node 20.19+
   npm install
   npm run dev

**注意事项**:
- 前端需要 Node.js 20.19+ 版本
- 如果遇到版本问题，使用 ``nvm use 20`` 切换到正确版本
- 前端默认运行在 ``http://localhost:5173``

索引与表格
==========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
