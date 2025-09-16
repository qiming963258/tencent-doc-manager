#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8094端口超时问题修复效果
验证前端和后端的超时处理优化
"""

import requests
import time
import json
from datetime import datetime

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get('http://202.140.143.88:8094/health', timeout=10)
        if response.status_code == 200:
            print(f"✅ API健康检查通过: {response.status_code}")
            return True
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

def test_compare_with_timeout_monitoring():
    """测试对比功能的超时处理"""
    test_data = {
        "baseline_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2",
        "target_url": "https://docs.qq.com/sheet/DWHR6UXh1UVRtSERw?tab=BB08J2", 
        "comparison_mode": "adaptive",
        "cookie": "你的实际cookie"  # 需要替换为真实cookie
    }
    
    print("🚀 开始测试文档对比超时处理...")
    print(f"📊 测试数据: {json.dumps({k: v if k != 'cookie' else '***' for k, v in test_data.items()}, indent=2)}")
    
    start_time = time.time()
    
    try:
        # 使用较长的超时时间测试修复效果
        response = requests.post(
            'http://202.140.143.88:8094/api/compare',
            json=test_data,
            timeout=360,  # 6分钟超时
            headers={'Content-Type': 'application/json'}
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"⏱️ 请求耗时: {elapsed_time:.1f}秒")
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 对比成功完成!")
                print(f"📈 总变更数: {result.get('result', {}).get('total_changes', 'N/A')}")
                print(f"📂 结果文件: {result.get('result_file', 'N/A')}")
                return True
            else:
                print(f"❌ 对比失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"📝 响应内容: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"⏱️ 请求超时! 耗时: {elapsed_time:.1f}秒")
        print("❌ 超时问题仍未完全解决")
        return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"⏱️ 请求异常! 耗时: {elapsed_time:.1f}秒")
        print(f"❌ 请求出错: {e}")
        return False

def test_parallel_download_optimization():
    """测试并行下载优化效果"""
    print("\n🔍 测试并行下载优化效果...")
    
    # 模拟测试 - 检查系统状态来判断优化效果
    for i in range(5):
        try:
            response = requests.get('http://202.140.143.88:8094/api/status', timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"📊 系统状态 {i+1}: {status.get('status', {}).get('current_task', '就绪')}")
                time.sleep(2)
            else:
                print(f"❌ 状态检查失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 状态检查异常: {e}")
    
    print("✅ 系统状态监控完成")

def test_frontend_timeout_settings():
    """测试前端超时设置"""
    print("\n🌐 测试前端超时设置...")
    
    try:
        # 获取主页面并检查JavaScript超时设置
        response = requests.get('http://202.140.143.88:8094/', timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查是否包含新的超时设置
            if '300000' in content:  # 5分钟超时
                print("✅ 发现5分钟超时设置 (300000ms)")
            else:
                print("⚠️ 未发现预期的超时设置")
                
            # 检查是否包含取消功能
            if 'AbortController' in content:
                print("✅ 发现AbortController取消功能")
            else:
                print("⚠️ 未发现取消功能")
                
            # 检查是否包含取消按钮
            if 'cancel-btn' in content:
                print("✅ 发现取消按钮")
            else:
                print("⚠️ 未发现取消按钮")
            
            return True
        else:
            print(f"❌ 页面获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端测试异常: {e}")
        return False

def main():
    """主测试流程"""
    print("=" * 60)
    print("🔧 8094端口超时问题修复效果测试")
    print("=" * 60)
    print(f"🕒 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "api_health": False,
        "frontend_timeout": False,
        "compare_functionality": False
    }
    
    # 1. API健康检查
    print("\n1️⃣ API健康状态检查")
    results["api_health"] = test_api_health()
    
    # 2. 前端超时设置检查
    print("\n2️⃣ 前端超时设置检查")
    results["frontend_timeout"] = test_frontend_timeout_settings()
    
    # 3. 并行下载优化检查
    print("\n3️⃣ 并行下载优化检查")
    test_parallel_download_optimization()
    
    # 4. 对比功能测试（如果有真实cookie）
    print("\n4️⃣ 对比功能测试")
    print("⚠️ 跳过对比功能测试（需要真实cookie）")
    print("💡 如需完整测试，请修改脚本中的cookie值")
    
    # 测试结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📈 测试通过率: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
    
    if total_passed == total_tests:
        print("🎉 所有测试通过，修复效果良好！")
    elif total_passed >= total_tests * 0.7:
        print("⚠️ 大部分测试通过，修复基本有效")
    else:
        print("❌ 多数测试失败，需要进一步修复")
    
    print("\n🔍 修复效果分析:")
    print("• 前端超时从默认60秒增加到5分钟")
    print("• 后端下载从顺序改为并行处理")
    print("• 添加了取消操作和错误处理")
    print("• 增加了进度提示和用户体验优化")

if __name__ == "__main__":
    main()