#!/bin/bash

echo "🚀 PDF文献分析智能体 - 项目初始化脚本"
echo "================================================"

# 检查Docker环境
echo "🔍 检查运行环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 创建目录结构
echo "📁 创建项目目录结构..."
mkdir -p uploads vector_db logs

# 设置目录权限
chmod 755 uploads vector_db logs

echo "✅ 目录创建完成"

# 检查环境配置
if [ ! -f .env ]; then
    if [ -f backend/.env.example ]; then
        echo "📝 创建环境配置文件..."
        cp backend/.env.example .env
        echo "⚠️  请编辑 .env 文件，配置必要的API密钥"
    else
        echo "❌ 找不到环境配置模板文件"
        exit 1
    fi
else
    echo "✅ 环境配置文件已存在"
fi

# 验证必要文件
echo "🔍 验证项目文件..."
required_files=(
    "backend/Dockerfile"
    "backend/Dockerfile.worker"
    "frontend/Dockerfile"
    "nginx/Dockerfile"
    "docker-compose.yml"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ 缺少以下文件:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "请先创建这些文件"
    exit 1
fi

echo "✅ 所有必要文件已存在"

# 检查API密钥配置
echo "🔑 检查API密钥配置..."
if ! grep -q "OPENAI_API_KEY=" .env && ! grep -q "QWEN_API_KEY=" .env; then
    echo "⚠️  请在 .env 文件中配置 OPENAI_API_KEY 或 QWEN_API_KEY"
    echo "   编辑命令: nano .env"
    exit 1
fi

echo "✅ 项目初始化完成！"
echo ""
echo "🎉 下一步操作:"
echo "   1. 检查 .env 文件配置: nano .env"
echo "   2. 启动服务: ./deploy.sh"
echo "   3. 访问应用: http://localhost"
echo ""
echo "�� 更多信息请查看 README.md" 