#!/usr/bin/env python3
"""测试硅基流动API直接调用"""

import requests
import json

def test_siliconflow():
    """测试硅基流动API"""
    
    # 硅基流动配置
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    base_url = "https://api.siliconflow.cn/v1"
    
    # 尝试不同的模型名称
    models = [
        "deepseek-v2-chat",
        "deepseek-v2-chat-0628", 
        "deepseek-v2.5",
        "deepseek-chat",
        "deepseek/deepseek-v2-chat",
        "deepseek/deepseek-v2.5"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for model in models:
        print(f"\n测试模型: {model}")
        print("-" * 40)
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个测试助手。"
                },
                {
                    "role": "user",
                    "content": "请回复OK"
                }
            ],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✓ 成功！模型 {model} 可用")
                result = response.json()
                print(f"  响应: {result['choices'][0]['message']['content']}")
                # 找到第一个可用的模型就返回
                return model
            else:
                print(f"✗ 失败 ({response.status_code}): {response.text[:100]}")
                
        except Exception as e:
            print(f"✗ 异常: {e}")
    
    return None

if __name__ == "__main__":
    print("="*60)
    print("硅基流动API测试")
    print("="*60)
    
    working_model = test_siliconflow()
    
    if working_model:
        print(f"\n✅ 找到可用模型: {working_model}")
        print(f"请在代码中使用: model = \"{working_model}\"")
    else:
        print("\n❌ 没有找到可用的模型")