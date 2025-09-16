#!/usr/bin/env python3
"""
DeepSeek API客户端
用于L2语义分析的AI服务
"""

import os
import json
import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端（使用硅基流动代理）"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置，请设置DEEPSEEK_API_KEY环境变量")
        
        # 使用硅基流动(SiliconFlow)的API端点
        # 硅基流动是DeepSeek的官方代理服务
        self.base_url = "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def call_api(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        调用DeepSeek API（通过硅基流动）
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            API响应文本
        """
        # 不允许任何降级，必须使用真实API
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",  # 硅基流动平台上的DeepSeek V3模型
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的文档变更分析助手，专门分析企业文档中的修改风险。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30  # 增加超时时间以适应DeepSeek-V2.5的响应速度
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek API错误: {response.status_code} - {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise Exception("API调用超时")
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {e}")
            raise
    
    
    def analyze_modification(self, modification: Dict) -> str:
        """
        分析单个修改
        
        Args:
            modification: 修改数据
            
        Returns:
            分析结果文本
        """
        prompt = f"""
        请分析以下文档修改的风险等级：
        
        列名：{modification.get('column_name')}
        原值：{modification.get('old_value', '')}
        新值：{modification.get('new_value', '')}
        
        请返回：
        1. 风险判断（SAFE/RISKY/UNSURE）
        2. 置信度（0-100）
        3. 简要原因
        
        格式：判断|置信度|原因
        """
        
        return self.call_api(prompt, max_tokens=100)
    
    def batch_analyze(self, modifications: list, batch_size: int = 5) -> list:
        """
        批量分析修改
        
        Args:
            modifications: 修改列表
            batch_size: 批次大小
            
        Returns:
            分析结果列表
        """
        results = []
        
        for i in range(0, len(modifications), batch_size):
            batch = modifications[i:i+batch_size]
            
            # 构建批量提示词
            prompt = "请分析以下多个文档修改，每个修改一行，格式：序号|判断|置信度|原因\n\n"
            
            for j, mod in enumerate(batch, 1):
                prompt += f"{j}. {mod.get('column_name')}: {mod.get('old_value', '')} → {mod.get('new_value', '')}\n"
            
            try:
                response = self.call_api(prompt, max_tokens=500)
                results.append(response)
            except Exception as e:
                logger.error(f"批次{i//batch_size + 1}分析失败: {e}")
                # 不降级，继续报错
                raise
        
        return results


# 单例模式
_client_instance = None

def get_deepseek_client() -> DeepSeekClient:
    """获取DeepSeek客户端单例"""
    global _client_instance
    if _client_instance is None:
        # 使用硅基流动的有效API密钥（同一套系统共享）
        # 此密钥来自: /deepseek_enhanced_server_complete.py 第34行
        # 硅基流动API端点: https://api.siliconflow.cn/v1
        # 模型: deepseek-ai/DeepSeek-V3 (最新版本)
        SHARED_API_KEY = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
        
        # 使用真实API，不允许任何降级
        _client_instance = DeepSeekClient(api_key=SHARED_API_KEY)
        logger.info("使用硅基流动DeepSeek V3 API客户端")
    return _client_instance