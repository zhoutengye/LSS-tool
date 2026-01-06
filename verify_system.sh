#!/bin/bash

# LSS 智能工艺指挥系统 - 系统验证脚本
# 用于快速检查前后端环境是否就绪

echo "========================================="
echo "🧪 LSS 智能工艺指挥系统 - 环境检查"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
FAIL=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ========================================
# 1. Python 环境检查
# ========================================
echo "📦 检查 Python 环境..."

# 检查 conda
if command -v conda &> /dev/null; then
    check_pass "Conda 已安装"

    # 检查 med 环境
    if conda env list | grep -q "^med "; then
        check_pass "Conda 环境 'med' 存在"
    else
        check_fail "Conda 环境 'med' 不存在，请先创建: conda create -n med python=3.9"
    fi
else
    check_fail "Conda 未安装"
fi

# 检查 Python
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    check_pass "Python 版本: $PYTHON_VERSION"
else
    check_fail "Python 未安装或不在 PATH 中"
fi

echo ""

# ========================================
# 2. 后端依赖检查
# ========================================
echo "📦 检查后端依赖..."

cd backend 2>/dev/null || { check_fail "无法进入 backend 目录"; exit 1; }

# 关键依赖清单
BACKEND_DEPS=("fastapi" "uvicorn" "sqlalchemy" "pydantic" "axios")

for dep in "${BACKEND_DEPS[@]}"; do
    if python -c "import ${dep}" 2>/dev/null; then
        check_pass "${dep}"
    else
        check_fail "${dep} 未安装"
    fi
done

cd ..
echo ""

# ========================================
# 3. 数据库文件检查
# ========================================
echo "🗄️  检查数据库..."

if [ -f "backend/lss_database.db" ]; then
    check_pass "数据库文件存在"

    # 检查数据库表
    TABLES=$(sqlite3 backend/lss_database.db ".tables" 2>/dev/null)
    if [ -n "$TABLES" ]; then
        check_pass "数据库已初始化 ($(echo $TABLES | wc -w) 个表)"

        # 检查关键表
        if echo "$TABLES" | grep -q "meta_actions"; then
            check_pass "对策库表 (meta_actions) 存在"
        else
            check_warn "对策库表不存在，可能需要运行 seed.py"
        fi

        if echo "$TABLES" | grep -q "data_instructions"; then
            check_pass "指令表 (data_instructions) 存在"
        else
            check_warn "指令表不存在，可能需要运行 seed.py"
        fi
    else
        check_fail "数据库表为空"
    fi
else
    check_warn "数据库文件不存在，首次运行会自动创建"
fi

echo ""

# ========================================
# 4. Node.js 环境检查
# ========================================
echo "📦 检查 Node.js 环境..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js 版本: $NODE_VERSION"

    # 检查版本是否 >= 18
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        check_pass "Node.js 版本满足要求 (>= 18)"
    else
        check_warn "Node.js 版本较低，建议升级到 18.x"
    fi
else
    check_fail "Node.js 未安装"
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    check_pass "npm 版本: $NPM_VERSION"
else
    check_fail "npm 未安装"
fi

echo ""

# ========================================
# 5. 前端依赖检查
# ========================================
echo "📦 检查前端依赖..."

cd frontend 2>/dev/null || { check_fail "无法进入 frontend 目录"; exit 1; }

if [ -f "package.json" ]; then
    check_pass "package.json 存在"

    if [ -d "node_modules" ]; then
        check_pass "node_modules 目录存在"

        # 检查关键依赖
        FRONTEND_DEPS=("react" "antd" "axios" "reactflow" "echarts" "echarts-for-react")

        for dep in "${FRONTEND_DEPS[@]}"; do
            if [ -d "node_modules/${dep}" ]; then
                check_pass "${dep}"
            else
                check_fail "${dep} 未安装，请运行: npm install"
            fi
        done
    else
        check_fail "node_modules 不存在，请运行: npm install"
    fi
else
    check_fail "package.json 不存在"
fi

cd ..
echo ""

# ========================================
# 6. 配置文件检查
# ========================================
echo "📋 检查配置文件..."

CONFIG_FILES=(
    "backend/models.py"
    "backend/main.py"
    "backend/analysis/commander.py"
    "frontend/src/App.jsx"
    "frontend/src/components/ProcessFlow.jsx"
    "frontend/src/components/ActionList.jsx"
    "frontend/src/components/MonitorPanel.jsx"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file"
    else
        check_fail "$file 缺失"
    fi
done

echo ""

# ========================================
# 总结
# ========================================
echo "========================================="
echo "📊 检查结果汇总"
echo "========================================="
echo -e "${GREEN}✅ 通过: $PASS 项${NC}"
echo -e "${RED}❌ 失败: $FAIL 项${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 环境检查全部通过！系统可以启动！${NC}"
    echo ""
    echo "🚀 启动命令："
    echo ""
    echo "  后端："
    echo "    cd backend"
    echo "    conda activate med"
    echo "    python main.py"
    echo ""
    echo "  前端（新终端）："
    echo "    cd frontend"
    echo "    npm run dev"
    echo ""
    echo "  访问地址："
    echo "    http://localhost:5173"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  发现 $FAIL 个问题，请先解决后再启动系统${NC}"
    echo ""
    echo "📚 常见问题解决方案："
    echo ""
    echo "  1. Python 依赖缺失："
    echo "     conda activate med"
    echo "     pip install fastapi uvicorn sqlalchemy"
    echo ""
    echo "  2. 前端依赖缺失："
    echo "     cd frontend"
    echo "     npm install"
    echo ""
    echo "  3. 数据库未初始化："
    echo "     cd backend"
    echo "     python seed.py"
    echo ""
    exit 1
fi
