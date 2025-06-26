# PDF文献分析智能体

基于AI技术的PDF文档智能分析和问答系统，支持OpenAI和通义千问模型。

## 🏗️ 项目架构

```
pdf-document-agent/
├── backend/                    # 后端服务 (FastAPI + Celery)
│   ├── Dockerfile             # API服务容器
│   ├── Dockerfile.worker      # Worker服务容器
│   ├── app/                   # 应用代码
│   │   ├── main.py           # FastAPI主应用
│   │   ├── core/             # 核心功能模块
│   │   ├── llm/              # LLM集成模块
│   │   └── celery_app.py     # Celery配置
│   ├── requirements.txt       # Python依赖
│   ├── requirements_qwen.txt  # 通义千问特殊依赖
│   ├── .env                   # 环境配置
│   ├── .env.example          # 环境配置示例
│   ├── .env.qwen             # 通义千问配置
│   └── start.sh              # 启动脚本
├── frontend/                   # 前端服务 (Vue.js + Element Plus)
│   ├── Dockerfile             # 前端容器
│   ├── nginx.conf             # 前端nginx配置
│   ├── src/                   # 源代码
│   │   ├── components/       # Vue组件
│   │   ├── stores/           # Pinia状态管理
│   │   ├── api/              # API客户端
│   │   └── styles/           # 样式文件
│   ├── package.json           # Node.js依赖
│   └── vite.config.ts        # Vite配置
├── nginx/                      # 统一网关
│   ├── Dockerfile             # Nginx容器
│   └── nginx.conf             # 路由配置
├── uploads/                    # 文件上传存储
├── vector_db/                  # 向量数据库存储
├── logs/                       # 应用日志
├── docker-compose.yml          # 容器编排配置
├── deploy.sh                   # 一键部署脚本
├── .gitignore                 # Git忽略规则
└── README.md                   # 项目文档
```

## 🚀 功能特性

### 核心功能
- 📄 **PDF文档上传与解析** - 支持多种PDF格式的智能解析
- 🤖 **智能问答系统** - 基于文档内容的精准问答
- 🔍 **语义搜索** - 高效的文档内容检索
- 📊 **内容分析** - 文档摘要和关键信息提取
- 📈 **处理进度监控** - 实时处理状态跟踪

### 技术特性
- 🔥 **多模型支持** - OpenAI GPT / 通义千问
- ⚡ **异步处理** - Celery任务队列
- 📦 **容器化部署** - Docker + Docker Compose
- 🔒 **安全可靠** - 环境变量配置，安全认证
- 📱 **响应式UI** - 现代化前端界面
- 🌐 **API优先** - RESTful API设计

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **异步任务**: Celery 5.3+
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **AI模型**: OpenAI GPT-4 / 通义千问
- **向量数据库**: Chroma/FAISS
- **文档处理**: PyPDF2, pdfplumber

### 前端
- **框架**: Vue.js 3+
- **UI库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **类型支持**: TypeScript

### 部署
- **容器**: Docker
- **编排**: Docker Compose
- **反向代理**: Nginx
- **监控**: Flower (Celery)

## 🚀 快速开始

### 环境要求
- Docker 20.0+
- Docker Compose 2.0+
- 至少 4GB RAM
- 10GB 可用磁盘空间

### 1. 克隆项目
```bash
git clone <repository-url>
cd pdf-document-agent
```

### 2. 配置环境变量
```bash
# 复制环境配置文件
cp backend/.env.example .env

# 编辑配置文件，设置必要的API密钥
nano .env
```

**必需配置项**:
```env
# AI服务配置 (二选一)
OPENAI_API_KEY=your_openai_api_key
QWEN_API_KEY=your_qwen_api_key

# 选择使用的模型
LLM_TYPE=openai          # 或 qwen
EMBEDDING_TYPE=openai    # 或 qwen

# 数据库配置
POSTGRES_PASSWORD=your_secure_password
```

### 3. 一键部署
```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. 访问应用
部署完成后，可以通过以下地址访问：

- 🌐 **前端应用**: http://localhost
- 📚 **API文档**: http://localhost/api/docs
- 📊 **任务监控**: http://localhost/flower
- 🔧 **健康检查**: http://localhost/health

## 💻 开发模式

### 后端开发
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker
celery -A app.celery_app worker --loglevel=info
```

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 数据库迁移
```bash
# 进入API容器
docker-compose exec api bash

# 运行数据库迁移
python -m app.core.database
```

## 📊 服务架构详情

| 服务名 | 端口 | 描述 | 健康检查 |
|--------|------|------|----------|
| nginx | 80/443 | 统一网关和负载均衡 | http://localhost/health |
| api | 8000 | FastAPI后端服务 | http://localhost:8000/ |
| frontend | 80 | Vue.js前端应用 | 内置nginx |
| postgres | 5432 | PostgreSQL数据库 | pg_isready |
| redis | 6379 | Redis缓存/消息队列 | redis-cli ping |
| worker | - | Celery异步任务处理 | - |
| flower | 5555 | Celery任务监控 | http://localhost:5555 |

## 📝 API文档

### 主要端点

#### 文档管理
- `POST /api/v1/documents/upload` - 上传PDF文档
- `GET /api/v1/documents/` - 获取文档列表
- `GET /api/v1/documents/{id}` - 获取文档详情
- `DELETE /api/v1/documents/{id}` - 删除文档

#### 智能问答
- `POST /api/v1/documents/{id}/query` - 文档问答
- `GET /api/v1/documents/{id}/history` - 查询历史

#### 任务管理
- `GET /api/v1/tasks/{task_id}` - 获取任务状态
- `POST /api/v1/tasks/{task_id}/cancel` - 取消任务

完整API文档: http://localhost/api/docs

## 🔧 配置说明

### 环境变量配置

#### 基础配置
```env
# 应用配置
LOG_LEVEL=INFO
ENVIRONMENT=production

# 数据库配置
POSTGRES_DB=document_analysis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis配置
REDIS_URL=redis://redis:6379/0

# 文件存储
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=pdf
```

#### AI模型配置
```env
# OpenAI配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# 通义千问配置
QWEN_API_KEY=xxx
QWEN_MODEL=qwen-turbo
QWEN_EMBEDDING_MODEL=text-embedding-v1

# 模型选择
LLM_TYPE=openai  # openai 或 qwen
EMBEDDING_TYPE=openai  # openai 或 qwen
```

### 性能调优

#### Celery配置
```env
CELERY_WORKER_CONCURRENCY=2
CELERY_TASK_TIME_LIMIT=600
CELERY_RESULT_EXPIRES=3600
```

#### 向量数据库配置
```env
VECTOR_DB_TYPE=chroma
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## 🔒 安全配置

### 基础安全
- 环境变量隔离
- API密钥安全存储
- 文件上传类型限制
- 文件大小限制

### 生产环境安全加固
```nginx
# 在nginx配置中添加安全头
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

## 📊 监控和日志

### 日志配置
- **应用日志**: `logs/app.log`
- **访问日志**: `logs/access.log`
- **错误日志**: `logs/error.log`
- **Celery日志**: `logs/celery.log`

### 监控端点
- **应用健康**: http://localhost/health
- **API健康**: http://localhost/api/health
- **Celery监控**: http://localhost/flower
- **数据库监控**: 通过Docker健康检查

## 🐛 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 查看服务日志
docker-compose logs api
docker-compose logs worker
docker-compose logs frontend
```

#### 2. API密钥配置问题
```bash
# 检查环境变量
docker-compose exec api env | grep API_KEY
```

#### 3. 数据库连接问题
```bash
# 测试数据库连接
docker-compose exec postgres psql -U postgres -d document_analysis -c "SELECT 1;"
```

#### 4. 文件上传问题
```bash
# 检查上传目录权限
ls -la uploads/
chmod 755 uploads/
```

### 性能问题

#### 1. 处理速度慢
- 检查Celery worker数量
- 优化chunk大小配置
- 考虑增加Redis内存

#### 2. 内存使用过高
- 调整worker并发数
- 优化向量数据库配置
- 定期清理临时文件

## 🔄 更新和维护

### 更新应用
```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据备份
```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres document_analysis > backup.sql

# 备份上传文件
tar -czf uploads_backup.tar.gz uploads/

# 备份向量数据库
tar -czf vector_db_backup.tar.gz vector_db/
```

### 日志清理
```bash
# 清理应用日志
truncate -s 0 logs/*.log

# 清理Docker日志
docker system prune -f
```

## 📞 支持和贡献

### 获取帮助
- 📋 提交Issue: [GitHub Issues](repository-url/issues)
- 📧 邮箱支持: support@example.com
- 📖 文档wiki: [Project Wiki](repository-url/wiki)

### 贡献代码
1. Fork 项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

### 开发规范
- 遵循PEP 8 Python代码规范
- 使用ESLint和Prettier格式化前端代码
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目:
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3组件库
- [Celery](https://docs.celeryq.dev/) - 分布式任务队列
- [OpenAI](https://openai.com/) - AI模型服务
- [通义千问](https://tongyi.aliyun.com/) - 阿里云AI模型

---

🎉 **Happy Coding!** 如有问题，欢迎提交Issue或联系我们！