# 配置清单
## 1. 前置要求 (Prerequisites)
*   **Python**: 建议 3.9+ (推荐使用 Conda 管理)
*   **Node.js**: 必须 v20+ (推荐使用 `nvm` 管理)

## 2. 后端配置 (Python/FastAPI)
```bash
# 1. 创建/激活环境 (Conda 版)
conda create -n lss_env python=3.9
conda activate lss_env

# 2. 安装核心依赖
pip install fastapi uvicorn pandas numpy scipy networkx

# 3. 启动服务 (在 backend 目录下)
uvicorn main:app --reload
# 服务地址: http://127.0.0.1:8000
```

## 3. 前端配置 (React/Vite)
```bash
# 1. 解决 Node 版本问题 (必须 v20+)
nvm use 20
# 或者永久设置: nvm alias default 20

# 2. 初始化项目 (在根目录下)
npm create vite@latest frontend -- --template react

# 3. 安装依赖 (在 frontend 目录下)
npm install
npm install axios antd reactflow @ant-design/icons

# 4. 启动前端
npm run dev
# 访问地址: http://localhost:5173
```
# LSS-tool
