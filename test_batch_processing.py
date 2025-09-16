#!/usr/bin/env python3
"""测试8094批量处理功能"""
import requests
import json
import time

def test_batch_processing():
    """测试批量处理API"""
    print("🧪 测试8094批量处理功能")
    print("-" * 50)
    
    # 测试数据 - 使用真实的腾讯文档URL
    test_batch_input = """# 批量处理测试
# 格式：基线URL 目标URL
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr
https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R
"""
    
    # 发送批量处理请求
    url = "http://localhost:8094/api/batch-process"
    data = {
        "batch_input": test_batch_input
    }
    
    print("📤 发送批量处理请求...")
    print(f"   任务数量: 2")
    
    try:
        response = requests.post(url, json=data, timeout=300)
        result = response.json()
        
        if result.get('success'):
            print("✅ 批量处理请求成功!")
            summary = result.get('summary', {})
            print(f"\n📊 处理结果汇总:")
            print(f"   总任务数: {summary.get('total_tasks', 0)}")
            print(f"   成功数量: {summary.get('success_count', 0)}")
            print(f"   失败数量: {summary.get('failed_count', 0)}")
            print(f"   结果文件: {result.get('result_file', 'N/A')}")
            
            # 显示详细结果
            if summary.get('results'):
                print(f"\n📝 详细结果:")
                for i, task_result in enumerate(summary['results'], 1):
                    print(f"\n   任务 {i}:")
                    print(f"   - 基线: {task_result.get('baseline_url', 'N/A')[:50]}...")
                    print(f"   - 目标: {task_result.get('target_url', 'N/A')[:50]}...")
                    print(f"   - 状态: {'✅ 成功' if task_result.get('success') else '❌ 失败'}")
                    if not task_result.get('success'):
                        error = task_result.get('result', {}).get('error', 'Unknown error')
                        print(f"   - 错误: {error}")
        else:
            print(f"❌ 批量处理请求失败: {result.get('error', 'Unknown error')}")
            
    except requests.exceptions.Timeout:
        print("⏱️ 请求超时（5分钟）")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("-" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_batch_processing()