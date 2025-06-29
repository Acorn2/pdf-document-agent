#!/bin/bash

echo "🚀 启动PDF文献分析智能体系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🐍 创建Python虚拟环境..."
    python3 -m venv venv
fi

echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查虚拟环境是否激活成功
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo "📦 升级pip..."
pip install --upgrade pip

echo "📦 安装项目依赖..."
# 根据LLM类型选择依赖文件
if grep -q "LLM_TYPE=qwen" .env 2>/dev/null; then
    echo "使用通义千问依赖文件..."
    pip install -r requirements_qwen.txt
else
    echo "使用默认依赖文件..."
    pip install -r requirements.txt
fi

# 检查依赖安装是否成功
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败，请检查错误信息"
    exit 1
fi

# 创建必要目录
mkdir -p uploads vector_db logs

# 分别检查关键模块
echo "🔍 检查关键依赖..."

echo "  检查 fastapi..."
python -c "import fastapi; print('  ✅ fastapi 可用')" || echo "  ❌ fastapi 导入失败"

echo "  检查 celery..."
python -c "import celery; print('  ✅ celery 可用')" || echo "  ❌ celery 导入失败"

echo "  检查 chromadb..."
python -c "import chromadb; print('  ✅ chromadb 可用')" || echo "  ❌ chromadb 导入失败"

echo "  检查 dashscope..."
python -c "import dashscope; print('  ✅ dashscope 可用')" || echo "  ❌ dashscope 导入失败"

echo "  检查 langchain..."
python -c "import langchain; print('  ✅ langchain 可用')" || echo "  ❌ langchain 导入失败"

# 不要因为单个模块失败就退出，继续启动服务
echo "🚀 启动后端API服务..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待API服务启动
sleep 3

echo "🚀 启动Celery工作者..."
celery -A app.celery_app worker --loglevel=info &
WORKER_PID=$!

echo "🚀 启动Celery监控..."
celery -A app.celery_app flower --port=5555 &
FLOWER_PID=$!

echo "✅ 系统启动完成！"
echo ""
echo "🔗 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🌸 Celery监控: http://localhost:5555"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $API_PID $WORKER_PID $FLOWER_PID 2>/dev/null; exit" INT
wait