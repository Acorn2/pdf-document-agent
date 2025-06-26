from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentUploadRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: TaskStatus
    upload_time: datetime
    message: str

class QueryRequest(BaseModel):
    document_id: str
    question: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=20)

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[dict]
    processing_time: float

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_size: int
    pages: int
    upload_time: datetime
    status: TaskStatus
    chunk_count: Optional[int] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    services: dict 