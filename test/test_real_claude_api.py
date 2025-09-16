#!/usr/bin/env python3
"""
真实测试Claude API连接
测试代理服务是否能正常工作
"""

import os
import requests
import json
from datetime import datetime

def test_direct_api():
    """直接测试API连接，不通过8081端口"""
    
    # 配置信息（基于config.py中的设置）
    base_url = "https://code2.ppchat.vip"
    
    # 注意：这里需要实际的API密钥
    # 如果您有可用的API密钥，请设置环境变量：
    # export ANTHROPIC_API_KEY="your-actual-api-key"
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        print("❌ 错误：未找到API密钥")
        print("请设置环境变量 ANTHROPIC_API_KEY")
        print("例如：export ANTHROPIC_API_KEY='sk-ant-...'")
        return False
    
    print(f"🔍 测试API连接...")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:20]}..." if len(api_key) > 20 else f"   API Key: {api_key}")
    
    # 构建请求
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    # 简单的测试消息
    data = {
        "model": "claude-3-5-haiku-20241022",  # 使用配置中的备用模型
        "messages": [
            {
                "role": "user",
                "content": "请回答：1+1等于几？只需要回答数字。"
            }
        ],
        "max_tokens": 10
    }
    
    try:
        print("\n📡 发送测试请求...")
        response = requests.post(
            f"{base_url}/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API连接成功！")
            print(f"   模型: {result.get('model', 'unknown')}")
            print(f"   响应: {result.get('content', [{}])[0].get('text', 'No response')}")
            print(f"   Token使用: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ API请求失败")
            print(f"   状态码: {response.status_code}")
            print(f"   错误信息: {response.text[:500]}")
            
            if response.status_code == 401:
                print("\n⚠️ 401错误通常表示API密钥无效或未授权")
            elif response.status_code == 404:
                print("\n⚠️ 404错误可能表示端点URL不正确")
            elif response.status_code == 429:
                print("\n⚠️ 429错误表示请求过于频繁，请稍后重试")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时（30秒）")
        print("   可能是网络问题或代理服务器不可达")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print("   请检查网络连接和代理URL")
        return False
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False

def test_with_mock_key():
    """使用模拟密钥测试（用于验证网络连通性）"""
    print("\n" + "="*60)
    print("使用模拟密钥测试网络连通性")
    print("="*60)
    
    # 使用一个假的密钥来测试网络是否能连接到代理
    os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-mock-key-for-connectivity-check'
    
    result = test_direct_api()
    
    if not result:
        print("\n💡 提示：如果收到401错误，说明网络连接正常，只是需要有效的API密钥")
        print("   如果收到其他错误，可能是网络或代理配置问题")
    
    return result

def main():
    """主测试函数"""
    print("="*60)
    print("Claude API 真实连接测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 首先检查是否有环境变量中的API密钥
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n✅ 检测到环境变量中的API密钥")
        test_direct_api()
    else:
        print("\n⚠️ 未检测到API密钥环境变量")
        print("将使用模拟密钥测试网络连通性...")
        test_with_mock_key()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()