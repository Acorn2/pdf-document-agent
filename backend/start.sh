#!/bin/bash

# 启动PDF文献分析智能体系统

echo "🚀 启动PDF文献分析智能体系统..."

# 检查是否已安装Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查是否已安装Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 启动数据库服务
echo "📦 启动数据库服务..."
docker-compose up -d postgres redis

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 5

# 安装后端依赖（如果需要）
if [ ! -d "venv" ]; then
    echo "🐍 创建Python虚拟环境..."
    python3 -m venv venv
fi

echo "📦 激活虚拟环境并安装后端依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖（如果需要）
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 启动后端服务
echo "🚀 启动后端API服务..."
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 启动前端服务
echo "🚀 启动前端开发服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..

echo "✅ 系统启动完成！"
echo ""
echo "🌐 前端地址: http://localhost:3000"
echo "🔗 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🗄️ 数据库管理: http://localhost:5050 (admin@example.com / admin)"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit" INT
wait 