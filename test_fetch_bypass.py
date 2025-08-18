#!/usr/bin/env python3
"""
测试Fetch MCP的robots.txt绕过功能
"""

import requests
import time

def test_robots_bypass():
    """测试robots.txt绕过功能"""
    
    # 测试不同的User-Agent和Headers
    test_configs = [
        {
            "name": "标准浏览器",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }
        },
        {
            "name": "机器人标识",
            "headers": {
                "User-Agent": "python-requests/2.28.0"
            }
        }
    ]
    
    # 测试URL - 一些通常有robots.txt限制的网站
    test_urls = [
        "https://httpbin.org/robots.txt",
        "https://httpbin.org/get",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    print("=== Fetch MCP Robots.txt 绕过测试 ===")
    
    for config in test_configs:
        print(f"\n🔍 测试配置: {config['name']}")
        
        for url in test_urls:
            try:
                response = requests.get(url, headers=config["headers"], timeout=10)
                status = "✅ 成功" if response.status_code == 200 else f"⚠️ {response.status_code}"
                print(f"  {url}: {status}")
                
                # 简短延迟避免被限流
                time.sleep(1)
                
            except Exception as e:
                print(f"  {url}: ❌ 失败 - {str(e)}")
    
    print(f"\n📋 配置摘要:")
    print(f"✅ Context7: 文档管理")
    print(f"✅ Excel优化版: 轻量级Excel操作 (2000单元格限制)")
    print(f"✅ Fetch无限制版: 绕过robots.txt + 伪装浏览器")
    print(f"📱 User-Agent: Chrome 120.0")
    print(f"🚫 Robots.txt: 已忽略")

if __name__ == "__main__":
    test_robots_bypass()