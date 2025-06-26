from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from datetime import datetime
import logging
import time

from .database import get_db, create_tables, Document, QueryHistory
from .schemas import *
from .core.document_processor import DocumentProcessor
from .core.vector_store import VectorStoreManager
from .core.agent_core import DocumentAnalysisAgent
from .core.model_factory import ModelFactory
from .celery_app import process_document_task, generate_summary_task
from .logging_config import setup_logging, RequestLoggingMiddleware
from .core.enhanced_vector_store import EnhancedVectorStore
from .core.cache_manager import cache_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="PDF文献分析智能体",
    description="基于LangChain的PDF文档问答系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保必要目录存在
os.makedirs("uploads", exist_ok=True)
os.makedirs("vector_db", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 在应用初始化时检查可用模型
available_models = ModelFactory.get_available_models()
logger.info(f"可用模型: {available_models}")

# 初始化核心组件 - 支持多模型
processor = DocumentProcessor()

# 根据环境变量选择模型类型
llm_type = os.getenv("LLM_TYPE", "openai")
embedding_type = os.getenv("EMBEDDING_TYPE", "openai")

logger.info(f"使用语言模型: {llm_type}")
logger.info(f"使用嵌入模型: {embedding_type}")

# 在应用初始化时添加
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir="./logs"
)

# 添加中间件
app.add_middleware(RequestLoggingMiddleware)

# 使用增强的向量存储
vector_store = EnhancedVectorStore(
    embedding_type=embedding_type,
    embedding_config={
        "model": os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v1")
    }
)

agent = DocumentAnalysisAgent(
    vector_store_manager=vector_store,
    llm_type=llm_type,
    model_config={
        "model": os.getenv("QWEN_MODEL", "qwen-plus"),
        "temperature": 0.1
    }
)

# 创建数据库表
create_tables()

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("PDF文献分析智能体服务启动")
    logger.info("正在初始化数据库...")
    create_tables()

@app.get("/", response_model=HealthCheck)
async def root():
    """健康检查接口"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        services={
            "database": "connected",
            "vector_store": "ready",
            "llm": "ready"
        }
    )

@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传PDF文档 - 使用Celery异步处理"""
    
    # 验证文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    # 验证文件大小（50MB限制）
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    try:
        # 生成唯一文档ID
        document_id = str(uuid.uuid4())
        
        # 保存文件
        file_path = f"uploads/{document_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 创建数据库记录
        db_document = Document(
            id=document_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            status="pending"
        )
        db.add(db_document)
        db.commit()
        
        # 提交Celery任务
        task = process_document_task.delay(document_id, file_path)
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status=TaskStatus.PENDING,
            upload_time=datetime.now(),
            message="文档上传成功，正在处理中...",
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
        "progress": task_result.info if task_result.status == "PROCESSING" else None
    }

@app.post("/api/v1/documents/{document_id}/hybrid-query")
async def hybrid_query_document(
    document_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """混合检索查询文档内容"""
    
    # 检查文档状态
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail=f"文档状态: {document.status}，无法查询")
    
    try:
        start_time = time.time()
        
        # 使用混合检索
        search_results = vector_store.hybrid_search(
            document_id=document_id,
            query=request.question,
            k=request.max_results,
            alpha=0.7  # 向量搜索权重
        )
        
        if not search_results:
            return QueryResponse(
                answer="抱歉，在该文档中未找到与您问题相关的内容。",
                confidence=0.0,
                sources=[],
                processing_time=time.time() - start_time
            )
        
        # 使用智能体生成回答
        response = agent.answer_question(
            document_id=document_id,
            question=request.question,
            max_results=request.max_results
        )
        
        # 记录查询历史
        query_history = QueryHistory(
            document_id=document_id,
            question=request.question,
            answer=response["answer"],
            confidence=response["confidence"],
            processing_time=response["processing_time"]
        )
        db.add(query_history)
        db.commit()
        
        return QueryResponse(**response)
        
    except Exception as e:
        logger.error(f"混合查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/v1/documents/{document_id}/query", response_model=QueryResponse)
async def query_document(
    document_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """查询文档内容"""
    
    # 检查文档是否存在且已处理完成
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail=f"文档状态: {document.status}，无法查询")
    
    try:
        # 执行查询
        result = agent.answer_question(
            document_id=document_id,
            question=request.question,
            max_results=request.max_results
        )
        
        if result["success"]:
            # 保存查询历史
            query_record = QueryHistory(
                document_id=document_id,
                question=request.question,
                answer=result["answer"],
                confidence=result["confidence"],
                processing_time=result["processing_time"]
            )
            db.add(query_record)
            db.commit()
            
            return QueryResponse(
                answer=result["answer"],
                confidence=result["confidence"],
                sources=result["sources"],
                processing_time=result["processing_time"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")

@app.get("/api/v1/documents/{document_id}", response_model=DocumentInfo)
async def get_document_info(document_id: str, db: Session = Depends(get_db)):
    """获取文档信息"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DocumentInfo(
        document_id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        pages=document.pages,
        upload_time=document.upload_time,
        status=TaskStatus(document.status),
        chunk_count=document.chunk_count
    )

@app.get("/api/v1/documents", response_model=List[DocumentInfo])
async def list_documents(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取文档列表"""
    
    documents = db.query(Document).offset(skip).limit(limit).all()
    
    return [
        DocumentInfo(
            document_id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            pages=doc.pages,
            upload_time=doc.upload_time,
            status=TaskStatus(doc.status),
            chunk_count=doc.chunk_count
        )
        for doc in documents
    ]

@app.post("/api/v1/documents/{document_id}/summary")
async def generate_document_summary(document_id: str, db: Session = Depends(get_db)):
    """生成文档摘要"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail=f"文档状态: {document.status}，无法生成摘要")
    
    try:
        result = agent.generate_summary(document_id)
        
        if result["success"]:
            return {"summary": result["summary"]}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"摘要生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """删除文档"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 删除文件
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # 删除向量存储
        vector_store.delete_document_collection(document_id)
        
        # 删除数据库记录
        db.delete(document)
        
        # 删除查询历史
        db.query(QueryHistory).filter(QueryHistory.document_id == document_id).delete()
        
        db.commit()
        
        return {"message": "文档删除成功"}
        
    except Exception as e:
        logger.error(f"文档删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")

# 添加模型信息接口
@app.get("/api/v1/models/info")
async def get_model_info():
    """获取当前使用的模型信息"""
    return {
        "llm_type": llm_type,
        "embedding_type": embedding_type,
        "available_models": available_models,
        "current_config": {
            "llm_model": os.getenv("QWEN_MODEL", "qwen-plus") if llm_type == "qwen" else os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "embedding_model": os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v1") if embedding_type == "qwen" else "text-embedding-ada-002"
        }
    }

# 添加缓存管理接口
@app.delete("/api/v1/cache/{document_id}")
async def clear_document_cache(document_id: str):
    """清除文档相关缓存"""
    try:
        # 这里可以实现更精确的缓存清理逻辑
        cache_manager.delete(f"search:*{document_id}*")
        cache_manager.delete(cache_manager.summary_cache_key(document_id))
        
        return {"message": "缓存清理完成"}
    except Exception as e:
        logger.error(f"缓存清理失败: {str(e)}")
        raise HTTPException(status_code=500, detail="缓存清理失败")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 