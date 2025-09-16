#!/usr/bin/env python3
"""
测试8089和8093服务连接的脚本
用于验证8089的监控设置能否正确调用8093的下载服务
"""

import requests
import json
import time

def test_connection():
    """测试8089到8093的连接"""
    
    print("="*60)
    print("🧪 开始测试8089和8093服务连接")
    print("="*60)
    
    # 第1步：测试8089服务是否运行
    print("\n[1] 测试8089服务状态...")
    try:
        response = requests.get('http://localhost:8089/')
        if response.status_code == 200:
            print("✅ 8089服务正常运行")
        else:
            print(f"⚠️ 8089服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 8089服务未运行: {e}")
        return
    
    # 第2步：测试8093服务是否运行
    print("\n[2] 测试8093服务状态...")
    try:
        response = requests.get('http://localhost:8093/')
        if response.status_code == 200:
            print("✅ 8093服务正常运行")
        else:
            print(f"⚠️ 8093服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 8093服务未运行: {e}")
        return
    
    # 第3步：保存测试下载链接到8089
    print("\n[3] 保存测试下载链接到8089...")
    test_links = [
        {
            "name": "测试文档1",
            "url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
            "enabled": True
        }
    ]
    
    try:
        response = requests.post(
            'http://localhost:8089/api/save-download-links',
            json={"links": test_links}
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 成功保存 {result.get('links_count', 0)} 个链接")
            else:
                print(f"❌ 保存失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ 保存链接失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 保存链接异常: {e}")
        return
    
    # 第4步：设置Cookie（必需）
    print("\n[4] 设置测试Cookie...")
    test_cookie = "test_cookie_value_123456"  # 这只是测试值
    
    try:
        response = requests.post(
            'http://localhost:8089/api/update-cookie',
            json={"cookie": test_cookie}
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Cookie设置成功")
            else:
                print(f"⚠️ Cookie设置响应: {result}")
        else:
            print(f"⚠️ Cookie设置返回: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Cookie设置异常（可能不影响测试）: {e}")
    
    # 第5步：触发下载（关键测试）
    print("\n[5] 测试8089调用8093下载服务...")
    print("触发start-download接口...")
    
    try:
        response = requests.post(
            'http://localhost:8089/api/start-download',
            json={"task_type": "test"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('success'):
                print("\n✅ 成功！8089可以调用8093服务")
                
                # 检查结果详情
                if 'results' in result:
                    for item in result['results']:
                        status = item.get('status', 'unknown')
                        name = item.get('name', 'unknown')
                        if status == 'started':
                            print(f"  ✅ {name}: 工作流已启动（通过8093）")
                        elif status == 'success':
                            print(f"  ✅ {name}: 下载成功（直接下载）")
                        else:
                            print(f"  ⚠️ {name}: {status}")
            else:
                error = result.get('error', '未知错误')
                print(f"❌ 调用失败: {error}")
                
                # 分析错误原因
                if "8093服务未运行" in error:
                    print("  📌 原因：8093服务未运行，已回退到直接下载")
                elif "Cookie" in error:
                    print("  📌 原因：需要有效的Cookie")
                elif "链接" in error:
                    print("  📌 原因：需要先导入下载链接")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == '__main__':
    test_connection()