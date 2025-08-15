#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯文档下载功能
URL: https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs
"""

import requests
import time
from datetime import datetime

def test_tencent_doc_download():
    """测试腾讯文档下载"""
    url = "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs"
    
    print(f"开始测试腾讯文档下载...")
    print(f"目标URL: {url}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 设置请求头模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 发起请求
        print("\n发送HTTP请求...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"响应内容长度: {len(response.content)} 字节")
        
        # 检查响应内容前500字符
        content_preview = response.text[:500]
        print(f"\n响应内容预览:")
        print("-" * 50)
        print(content_preview)
        print("-" * 50)
        
        # 保存完整响应内容
        timestamp = int(time.time())
        filename = f"tencent_doc_download_test_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"\n完整响应已保存到: {filename}")
        
        # 分析响应内容
        if response.status_code == 200:
            if 'csv' in response.headers.get('Content-Type', '').lower():
                print("✅ 获得CSV格式内容")
            elif 'json' in response.headers.get('Content-Type', '').lower():
                print("✅ 获得JSON格式内容")
            elif 'html' in response.headers.get('Content-Type', '').lower():
                print("⚠️ 获得HTML页面，可能需要进一步处理")
                
                # 检查是否需要登录
                if '登录' in response.text or 'login' in response.text.lower():
                    print("❌ 页面要求登录")
                elif '权限' in response.text or 'permission' in response.text.lower():
                    print("❌ 页面提示权限不足")
                else:
                    print("ℹ️ 页面内容需要进一步分析")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
        
        return response
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return None
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_tencent_doc_download()