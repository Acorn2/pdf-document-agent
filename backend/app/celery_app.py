from celery import Celery
import os
from dotenv import load_dotenv
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .database import Document, DATABASE_URL
from .core.document_processor import DocumentProcessor
from .core.vector_store import VectorStoreManager
from .core.model_factory import ModelFactory

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Celery应用
celery_app = Celery(
    "document_analysis",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=['app.celery_app']
)

# 配置Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_routes={
        'app.celery_app.process_document_task': {'queue': 'document_processing'},
        'app.celery_app.cleanup_task': {'queue': 'maintenance'},
    }
)

# 数据库连接
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

# 初始化组件
def get_components():
    """获取处理组件"""
    embedding_type = os.getenv("EMBEDDING_TYPE", "openai")
    
    processor = DocumentProcessor()
    vector_store = VectorStoreManager(
        embedding_type=embedding_type,
        embedding_config={
            "model": os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v1")
        }
    )
    
    return processor, vector_store

@celery_app.task(bind=True, name='app.celery_app.process_document_task')
def process_document_task(self, document_id: str, file_path: str):
    """异步处理文档任务"""
    db = get_db_session()
    
    try:
        # 更新任务状态
        self.update_state(
            state="PROCESSING", 
            meta={"step": "初始化", "progress": 0}
        )
        
        # 获取处理组件
        processor, vector_store = get_components()
        
        # 更新数据库状态
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "processing"
            db.commit()
        
        # 更新任务状态
        self.update_state(
            state="PROCESSING", 
            meta={"step": "提取文本", "progress": 20}
        )
        
        # 处理文档
        result = processor.process_document(file_path)
        
        if not result["success"]:
            # 处理失败
            if document:
                document.status = "failed"
                db.commit()
            
            self.update_state(
                state="FAILURE", 
                meta={"error": result["error"]}
            )
            return {"status": "failed", "error": result["error"]}
        
        # 更新任务状态
        self.update_state(
            state="PROCESSING", 
            meta={"step": "创建向量存储", "progress": 60}
        )
        
        # 创建向量存储
        vector_store.create_document_collection(document_id)
        vector_store.add_document_chunks(document_id, result["chunks"])
        
        # 更新任务状态
        self.update_state(
            state="PROCESSING", 
            meta={"step": "更新数据库", "progress": 90}
        )
        
        # 更新数据库
        if document:
            document.pages = result["metadata"]["pages"]
            document.chunk_count = result["chunk_count"]
            document.status = "completed"
            db.commit()
        
        # 完成
        self.update_state(
            state="SUCCESS", 
            meta={"step": "完成", "progress": 100}
        )
        
        logger.info(f"文档 {document_id} 处理完成")
        
        return {
            "status": "completed",
            "chunk_count": result["chunk_count"],
            "pages": result["metadata"]["pages"],
            "message": "文档处理完成"
        }
        
    except Exception as e:
        logger.error(f"处理文档 {document_id} 时发生错误: {str(e)}")
        
        # 更新数据库状态
        if document:
            document.status = "failed"
            db.commit()
        
        self.update_state(
            state="FAILURE", 
            meta={"error": str(e)}
        )
        
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()

@celery_app.task(name='app.celery_app.cleanup_task')
def cleanup_task():
    """清理任务：删除过期文件和数据"""
    db = get_db_session()
    
    try:
        from datetime import datetime, timedelta
        import os
        
        # 删除7天前失败的文档记录和文件
        cutoff_date = datetime.now() - timedelta(days=7)
        failed_docs = db.query(Document).filter(
            Document.status == "failed",
            Document.upload_time < cutoff_date
        ).all()
        
        cleaned_count = 0
        for doc in failed_docs:
            # 删除文件
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            
            # 删除数据库记录
            db.delete(doc)
            cleaned_count += 1
        
        db.commit()
        logger.info(f"清理了 {cleaned_count} 个过期的失败文档")
        
        return {"cleaned_count": cleaned_count}
        
    except Exception as e:
        logger.error(f"清理任务失败: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()

@celery_app.task(name='app.celery_app.generate_summary_task')
def generate_summary_task(document_id: str):
    """异步生成文档摘要"""
    db = get_db_session()
    
    try:
        # 检查文档是否存在
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document or document.status != "completed":
            return {"error": "文档不存在或未完成处理"}
        
        # 获取组件
        _, vector_store = get_components()
        
        # 初始化智能体
        llm_type = os.getenv("LLM_TYPE", "openai")
        from .core.agent_core import DocumentAnalysisAgent
        
        agent = DocumentAnalysisAgent(
            vector_store_manager=vector_store,
            llm_type=llm_type,
            model_config={
                "model": os.getenv("QWEN_MODEL", "qwen-plus"),
                "temperature": 0.1
            }
        )
        
        # 生成摘要
        result = agent.generate_summary(document_id)
        
        if result["success"]:
            logger.info(f"文档 {document_id} 摘要生成完成")
        else:
            logger.error(f"文档 {document_id} 摘要生成失败: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"生成摘要任务失败: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()

# 定期任务配置
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-failed-documents': {
        'task': 'app.celery_app.cleanup_task',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
} 