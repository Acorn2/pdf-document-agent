import os
import dashscope
from typing import List, Dict, Any, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import Generation, LLMResult
import logging

logger = logging.getLogger(__name__)

class QwenLLM(LLM):
    """通义千问大模型适配器"""
    
    model_name: str = "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max
    temperature: float = 0.1
    max_tokens: int = 2000
    top_p: float = 0.8
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 设置API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量")
        
        dashscope.api_key = api_key
    
    @property
    def _llm_type(self) -> str:
        return "qwen"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """调用通义千问API"""
        try:
            response = dashscope.Generation.call(
                model=self.model_name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stop=stop,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.output.text
            else:
                logger.error(f"通义千问API调用失败: {response.message}")
                raise Exception(f"API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问调用异常: {str(e)}")
            raise e
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """异步调用通义千问API"""
        try:
            response = await dashscope.AGeneration.call(
                model=self.model_name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stop=stop,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.output.text
            else:
                logger.error(f"通义千问异步API调用失败: {response.message}")
                raise Exception(f"异步API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问异步调用异常: {str(e)}")
            raise e

class QwenChatModel:
    """通义千问对话模型（支持对话格式）"""
    
    def __init__(self, model_name: str = "qwen-plus", **kwargs):
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.1)
        self.max_tokens = kwargs.get("max_tokens", 2000)
        self.top_p = kwargs.get("top_p", 0.8)
        
        # 设置API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量")
        
        dashscope.api_key = api_key
    
    def predict(self, text: str) -> str:
        """预测方法，兼容LangChain接口"""
        return self._call_chat([{"role": "user", "content": text}])
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """调用方法，支持消息格式"""
        return self._call_chat(messages)
    
    def _call_chat(self, messages: List[Dict[str, str]]) -> str:
        """调用通义千问聊天API"""
        try:
            response = dashscope.Generation.call(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                logger.error(f"通义千问聊天API调用失败: {response.message}")
                raise Exception(f"聊天API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问聊天调用异常: {str(e)}")
            raise e 