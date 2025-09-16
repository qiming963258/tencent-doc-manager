#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek V3 API客户端
使用硅基流动(SiliconFlow)平台的DeepSeek-V3模型
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """DeepSeek V3 API客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "deepseek-ai/DeepSeek-V3"
        
        # 配置
        self.default_temperature = 0.1  # 低温度确保一致性
        self.max_tokens = 4000
        self.timeout = 60
        
        logger.info(f"DeepSeek客户端初始化完成，使用模型: {self.model}")
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = None) -> Dict[str, Any]:
        """
        调用DeepSeek V3聊天完成API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            temperature: 温度参数，控制输出的随机性
            
        Returns:
            API响应字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "content": result["choices"][0]["message"]["content"],
                            "usage": result.get("usage", {}),
                            "model": result.get("model")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"API错误: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API错误: {response.status}",
                            "details": error_text
                        }
                        
        except asyncio.TimeoutError:
            logger.error("API调用超时")
            return {"success": False, "error": "API调用超时"}
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_columns(self, actual_columns: List[str], standard_columns: List[str]) -> Dict[str, Any]:
        """
        使用DeepSeek V3分析列名映射
        
        Args:
            actual_columns: 实际的列名列表
            standard_columns: 标准列名列表（19个）
            
        Returns:
            映射结果字典
        """
        prompt = self._build_column_analysis_prompt(actual_columns, standard_columns)
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的数据分析专家，精通CSV列名标准化和映射。你总是返回有效的JSON格式响应。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        result = await self.chat_completion(messages, temperature=0.1)
        
        if result["success"]:
            try:
                # 尝试解析JSON响应
                content = result["content"]
                
                # 提取JSON部分（如果被包含在其他文本中）
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > 0:
                    json_str = content[json_start:json_end]
                    parsed = json.loads(json_str)
                    return {
                        "success": True,
                        "result": parsed,
                        "raw_response": content
                    }
                else:
                    return {
                        "success": False,
                        "error": "响应中未找到JSON格式",
                        "raw_response": content
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return {
                    "success": False,
                    "error": f"JSON解析失败: {e}",
                    "raw_response": result["content"]
                }
        else:
            return result
    
    def call_api(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        同步调用DeepSeek API - 兼容L2语义分析器
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            API响应文本
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
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
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
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
    
    def _build_column_analysis_prompt(self, actual_columns: List[str], standard_columns: List[str]) -> str:
        """构建列名分析提示词"""
        return f"""分析CSV列名并生成标准化映射。

## 任务
将实际列名映射到19个标准列名，处理缺失和多余的情况。

## 19个标准列名（必须全部包含）
{json.dumps(standard_columns, ensure_ascii=False, indent=2)}

## 实际列名（共{len(actual_columns)}个）
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 要求
1. 每个实际列名映射到最匹配的标准列名
2. 识别缺失的标准列（标记为null）
3. 识别无法映射的多余列（放入discarded_columns）
4. 必须返回JSON格式

## 输出格式
{{
    "success": true,
    "standard_columns_status": {{
        "序号": "映射的实际列名或null",
        "项目类型": "映射的实际列名或null",
        // ... 全部19个标准列
    }},
    "mapping": {{
        "实际列名": "标准列名"
        // ... 所有成功的映射
    }},
    "confidence_scores": {{
        "实际列名": 0.0-1.0
        // ... 每个映射的置信度
    }},
    "missing_standard_columns": ["缺失的标准列名"],
    "discarded_columns": ["无法映射的实际列名"],
    "statistics": {{
        "mapped_count": 数字,
        "missing_count": 数字,
        "discarded_count": 数字
    }}
}}

请直接返回JSON，不要包含其他解释文字。"""
    
    def sync_analyze_columns(self, actual_columns: List[str], standard_columns: List[str]) -> Dict[str, Any]:
        """同步版本的列名分析（供Flask使用）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.analyze_columns(actual_columns, standard_columns))
        finally:
            loop.close()


# 测试代码
if __name__ == "__main__":
    import os
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试客户端
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    client = DeepSeekClient(api_key)
    
    # 测试列名
    test_columns = ["ID", "产品名称", "价格", "库存", "状态"]
    standard_columns = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
        "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
    ]
    
    # 异步测试
    async def test():
        result = await client.analyze_columns(test_columns, standard_columns)
        print("分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 运行测试
    asyncio.run(test())