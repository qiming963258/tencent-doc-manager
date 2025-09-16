#!/usr/bin/env python3
"""测试硅基流动API模型列表"""

import requests
import json

def list_models():
    """列出硅基流动可用模型"""
    
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    base_url = "https://api.siliconflow.cn/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 尝试获取模型列表
    try:
        response = requests.get(
            f"{base_url}/models",
            headers=headers,
            timeout=5
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("\n可用模型列表:")
                for model in data['data']:
                    if 'id' in model:
                        print(f"  - {model['id']}")
                        if 'deepseek' in model['id'].lower():
                            print(f"    ^ 这是DeepSeek模型!")
        
    except Exception as e:
        print(f"错误: {e}")

def test_deepseek_v3():
    """测试DeepSeek V3模型"""
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    base_url = "https://api.siliconflow.cn/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试DeepSeek V3模型
    models_to_test = [
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-V3.1",
        "deepseek-ai/deepseek-v3",  # 小写版本
        "DeepSeek-V3"  # 简短版本
    ]
    
    for model in models_to_test:
        print(f"\n测试模型: {model}")
        print("-" * 40)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "回复OK"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ 成功！模型 {model} 可用")
                result = response.json()
                print(f"  响应: {result['choices'][0]['message']['content']}")
                return model
            else:
                print(f"✗ 失败 ({response.status_code}): {response.text[:100]}")
        except Exception as e:
            print(f"✗ 异常: {e}")
    
    return None

if __name__ == "__main__":
    print("="*60)
    print("硅基流动模型列表")
    print("="*60)
    list_models()
    
    print("\n" + "="*60)
    print("测试DeepSeek V3模型")
    print("="*60)
    working_model = test_deepseek_v3()
    if working_model:
        print(f"\n✅ 找到可用的DeepSeek V3模型: {working_model}")