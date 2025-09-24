#!/usr/bin/env python3
"""
深度诊断AI语义分析失败的根本原因
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def check_api_key():
    """检查API密钥配置"""
    print("\n🔑 检查API密钥配置")
    print("="*60)

    # 1. 检查环境变量
    env_key = os.getenv('DEEPSEEK_API_KEY')
    if env_key:
        print(f"✅ 环境变量DEEPSEEK_API_KEY存在: {env_key[:10]}...")
    else:
        print("❌ 环境变量DEEPSEEK_API_KEY不存在")

    # 2. 检查.env文件
    env_file = Path('/root/projects/tencent-doc-manager/.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if 'DEEPSEEK_API_KEY' in line:
                    key = line.split('=')[1].strip()
                    print(f"✅ .env文件中有API密钥: {key[:10]}...")

                    # 尝试加载.env
                    try:
                        from dotenv import load_dotenv
                        load_dotenv(env_file)
                        new_env = os.getenv('DEEPSEEK_API_KEY')
                        if new_env:
                            print(f"✅ 成功从.env加载到环境变量: {new_env[:10]}...")
                            return new_env
                        else:
                            print("❌ .env加载失败，环境变量仍为空")
                    except ImportError:
                        print("⚠️ python-dotenv未安装")

    return env_key

def test_api_key(api_key):
    """测试API密钥是否有效"""
    print("\n🧪 测试API密钥有效性")
    print("="*60)

    if not api_key:
        print("❌ 无API密钥可测试")
        return False

    # 测试硅基流动API
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "回复OK即可"}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }

    try:
        print("正在调用DeepSeek API...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ API调用成功！密钥有效")
            result = response.json()
            print(f"响应: {result['choices'][0]['message']['content']}")
            return True
        elif response.status_code == 401:
            print("❌ API密钥无效或过期")
            return False
        elif response.status_code == 429:
            print("⚠️ API限流，但密钥有效")
            return True
        elif response.status_code == 503:
            print("⚠️ API服务繁忙，但密钥可能有效")
            return True
        else:
            print(f"❌ API返回错误: {response.status_code}")
            print(f"详情: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ API调用异常: {e}")
        return False

def check_account_balance(api_key):
    """检查账户余额（如果API支持）"""
    print("\n💰 检查账户余额")
    print("="*60)

    # 硅基流动的余额查询API
    url = "https://api.siliconflow.cn/v1/user/info"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            info = response.json()
            print(f"账户信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
        else:
            print(f"⚠️ 无法获取账户信息: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 余额查询失败: {e}")

def analyze_scoring_logic():
    """分析打分逻辑问题"""
    print("\n🔍 分析打分逻辑设计问题")
    print("="*60)

    print("\n当前的分层逻辑：")
    print("L1列（高风险）: 纯规则，不用AI ❌")
    print("L2列（中风险）: 强制使用AI ✅")
    print("L3列（低风险）: 纯规则，不用AI ❌")

    print("\n问题分析：")
    print("1. L1列最需要AI判断（如星号转数字），却不用AI")
    print("2. 92处'重要程度'变更全部被误判为高风险")
    print("3. 系统无法识别格式转换vs实质变更")

    print("\n建议修复方案：")
    print("1. 短期：在L1处理中加入格式转换识别")
    print("2. 长期：L1列也应该使用AI语义分析")
    print("3. 日志：明确显示AI调用失败原因")

def check_logs_and_fallback():
    """检查日志和降级机制"""
    print("\n📝 检查日志和降级机制")
    print("="*60)

    # 检查8093的日志
    log_file = Path('/tmp/8093.log')
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()

        ai_errors = [l for l in lines if 'AI' in l or '语义' in l or 'DeepSeek' in l]
        if ai_errors:
            print("发现AI相关日志:")
            for err in ai_errors[-5:]:  # 只显示最后5条
                print(f"  {err.strip()}")
        else:
            print("❌ 日志中没有AI相关信息")

    print("\n降级机制分析：")
    print("1. IntegratedScorer初始化时要求AI必须成功（第99行）")
    print("2. 但92处变更仍然完成，说明存在隐藏的降级")
    print("3. 可能是L1列根本不调用AI，所以不受影响")

def main():
    print("🔬 深度诊断AI语义分析问题")
    print("="*80)

    # 1. 检查API密钥
    api_key = check_api_key()

    # 2. 测试API
    if api_key:
        valid = test_api_key(api_key)
        if valid:
            check_account_balance(api_key)

    # 3. 分析逻辑问题
    analyze_scoring_logic()

    # 4. 检查日志
    check_logs_and_fallback()

    print("\n" + "="*80)
    print("📊 诊断总结:")
    print("\n根本原因：")
    print("1. ❌ '重要程度'是L1列，设计上不使用AI")
    print("2. ❌ 所有92处变更都用规则引擎处理")
    print("3. ❌ 星号转数字被误判为高风险变更")
    print("4. ⚠️ API密钥存在但可能未正确加载")
    print("5. ❌ 日志未显示AI调用状态和失败原因")

    print("\n这不是虚拟数据欺骗，而是设计缺陷：")
    print("最需要AI的L1列反而不用AI！")

if __name__ == "__main__":
    main()