import fitz  # PyMuPDF
import os
import hashlib
from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """PDF文档处理器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[str, any]:
        """从PDF文件中提取文本和元数据"""
        try:
            doc = fitz.open(file_path)
            
            # 提取基本信息
            metadata = {
                "pages": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", "")
            }
            
            # 提取文本内容
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": page_text
                })
                full_text += f"\n\n--- 第{page_num + 1}页 ---\n\n{page_text}"
            
            doc.close()
            
            return {
                "metadata": metadata,
                "full_text": full_text,
                "page_texts": page_texts,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            return {
                "metadata": {},
                "full_text": "",
                "page_texts": [],
                "success": False,
                "error": str(e)
            }
    
    def split_text_into_chunks(self, text: str) -> List[Dict[str, any]]:
        """将文本分割成块"""
        try:
            chunks = self.text_splitter.split_text(text)
            
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # 生成块的唯一ID
                chunk_id = hashlib.md5(f"{chunk}_{i}".encode()).hexdigest()
                
                processed_chunks.append({
                    "chunk_id": chunk_id,
                    "content": chunk,
                    "chunk_index": i,
                    "chunk_length": len(chunk)
                })
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"文本分块失败: {str(e)}")
            return []
    
    def process_document(self, file_path: str) -> Dict[str, any]:
        """处理文档的完整流程"""
        # 提取文本
        extraction_result = self.extract_text_from_pdf(file_path)
        
        if not extraction_result["success"]:
            return extraction_result
        
        # 分割文本
        chunks = self.split_text_into_chunks(extraction_result["full_text"])
        
        return {
            "metadata": extraction_result["metadata"],
            "full_text": extraction_result["full_text"],
            "page_texts": extraction_result["page_texts"],
            "chunks": chunks,
            "chunk_count": len(chunks),
            "success": True,
            "error": None
        } 