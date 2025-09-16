#!/usr/bin/env python3
"""测试完整的处理流程"""

import requests
import json
import time
import sys

# API端点
BASE_URL = "http://localhost:8093"

def test_complete_flow():
    """测试完整流程"""
    
    print("=" * 60)
    print("腾讯文档处理系统完整流程测试")
    print("=" * 60)
    
    # 测试数据
    test_data = {
        "baseline_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",  # 副本-测试版本-出国销售计划表
        "target_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",     # 测试版本-小红书部门
        "cookie": "YOUR_COOKIE_HERE",  # 请替换为实际的Cookie
        "advanced_settings": {
            "force_download": True,  # 强制下载
            "enable_standardization": True,  # 启用列标准化
            "enable_ai_analysis": True,  # 启用AI分析
            "enable_excel_marking": True,  # 启用Excel标记
            "ai_threshold": 0.7,
            "verbose_logging": True
        }
    }
    
    # 从命令行参数获取Cookie（如果提供）
    if len(sys.argv) > 1:
        test_data["cookie"] = sys.argv[1]
        print(f"✅ 使用提供的Cookie")
    else:
        print("⚠️ 警告：未提供Cookie，请在命令行参数中提供")
        print("用法: python3 test_complete_flow.py 'YOUR_COOKIE_HERE'")
        return
    
    print("\n📊 测试配置:")
    print(f"  基线URL: {test_data['baseline_url']}")
    print(f"  目标URL: {test_data['target_url']}")
    print(f"  强制下载: {test_data['advanced_settings']['force_download']}")
    print(f"  列标准化: {test_data['advanced_settings']['enable_standardization']}")
    print(f"  AI分析: {test_data['advanced_settings']['enable_ai_analysis']}")
    print(f"  Excel标记: {test_data['advanced_settings']['enable_excel_marking']}")
    
    # 发送请求
    print("\n🚀 开始执行流程...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/start",
            json=test_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            return
        
        print("✅ 流程已启动")
        
        # 轮询状态
        print("\n📊 监控执行状态...")
        while True:
            time.sleep(2)
            
            status_response = requests.get(f"{BASE_URL}/api/status")
            if status_response.status_code != 200:
                print(f"❌ 无法获取状态")
                break
            
            status = status_response.json()
            
            # 显示进度
            progress = status.get("progress", 0)
            current_task = status.get("current_task", "")
            state = status.get("status", "unknown")
            
            print(f"\r进度: {progress}% | 状态: {state} | 当前任务: {current_task}", end="")
            
            # 检查是否完成
            if state == "completed":
                print("\n✅ 流程完成！")
                
                # 显示结果
                results = status.get("results", {})
                if results:
                    print("\n📊 执行结果:")
                    
                    # 统计信息
                    stats = results.get("statistics", {})
                    if stats:
                        print(f"  修改单元格: {stats.get('changed_cells', 0)}")
                        print(f"  风险评分: {stats.get('risk_score', 0)}")
                    
                    # 文件信息
                    if results.get("baseline_file"):
                        print(f"  基线文件: {results['baseline_file']}")
                    if results.get("target_file"):
                        print(f"  目标文件: {results['target_file']}")
                    if results.get("comparison_file"):
                        print(f"  对比文件: {results['comparison_file']}")
                    if results.get("excel_file"):
                        print(f"  Excel文件: {results['excel_file']}")
                    if results.get("upload_url"):
                        print(f"  上传URL: {results['upload_url']}")
                
                # 检查日志中的错误
                logs = status.get("logs", [])
                errors = [log for log in logs if log.get("level") == "error"]
                if errors:
                    print("\n⚠️ 发现错误:")
                    for error in errors[-5:]:  # 显示最后5个错误
                        print(f"  [{error['time']}] {error['message']}")
                
                break
            
            elif state == "error":
                print("\n❌ 流程出错")
                
                # 显示错误日志
                logs = status.get("logs", [])
                errors = [log for log in logs if log.get("level") == "error"]
                for error in errors[-5:]:
                    print(f"  [{error['time']}] {error['message']}")
                
                break
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_complete_flow()