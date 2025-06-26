import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器 - 支持Redis和内存缓存"""
    
    def __init__(self, redis_url: str = None, use_redis: bool = True):
        self.use_redis = use_redis
        self.memory_cache = {}
        self.memory_cache_maxsize = 1000
        
        if use_redis and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # 测试连接
                self.redis_client.ping()
                logger.info("Redis缓存连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存缓存: {e}")
                self.use_redis = False
                self.redis_client = None
        else:
            self.use_redis = False
            self.redis_client = None
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """生成缓存键"""
        hash_value = hashlib.md5(data.encode('utf-8')).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
        return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存值"""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.setex(
                    key, expire, json.dumps(value, ensure_ascii=False)
                )
            else:
                # 内存缓存简单LRU实现
                if len(self.memory_cache) >= self.memory_cache_maxsize:
                    # 删除最旧的项
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                
                self.memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
        return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
        return False
    
    def search_cache_key(self, document_id: str, query: str, k: int) -> str:
        """生成搜索缓存键"""
        cache_data = f"{document_id}:{query}:{k}"
        return self._generate_key("search", cache_data)
    
    def summary_cache_key(self, document_id: str) -> str:
        """生成摘要缓存键"""
        return self._generate_key("summary", document_id)

# 全局缓存实例
cache_manager = CacheManager(
    redis_url=os.getenv("REDIS_URL"),
    use_redis=os.getenv("USE_REDIS", "true").lower() == "true"
) 