#!/bin/bash

# PDF文献分析智能体部署脚本

set -e

echo "🚀 开始部署PDF文献分析智能体..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  .env文件不存在，从示例文件复制..."
    cp .env.example .env
    echo "📝 请编辑.env文件配置必要的环境变量"
    exit 1
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p uploads vector_db logs

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🌟 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🔍 检查服务状态..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ 服务启动成功！"
    echo "🌐 应用访问地址: http://localhost"
    echo "📊 Flower监控: http://localhost/flower"
    echo "🔧 API文档: http://localhost/api/docs"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
    exit 1
fi

echo "🎉 部署完成！" 