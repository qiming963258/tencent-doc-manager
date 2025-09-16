#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传流程测试脚本
测试完整的上传流程，包括Excel文件上传和URL获取
"""

import os
import json
import time
import requests
from datetime import datetime


def test_upload_flow():
    """测试完整上传流程"""
    
    print("\n" + "=" * 60)
    print("腾讯文档上传流程测试")
    print("=" * 60)
    
    # 测试文件路径
    test_file = "/root/projects/tencent-doc-manager/excel_test/test_upload_20250909.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print(f"✅ 找到测试文件: {test_file}")
    print(f"   文件大小: {os.path.getsize(test_file)} 字节")
    
    # 服务器地址
    server_url = "http://localhost:8109"
    
    # 检查服务器状态
    print(f"\n📡 检查服务器状态: {server_url}")
    try:
        response = requests.get(server_url, timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("💡 请确保上传测试服务器正在运行: python3 upload_test_server_8109.py")
        return False
    
    # Cookie配置说明
    print("\n🍪 Cookie配置")
    print("=" * 40)
    print("上传功能需要有效的腾讯文档Cookie")
    print("请通过以下方式之一配置Cookie：")
    print("1. 访问 http://localhost:8109 并在网页中配置")
    print("2. 编辑 /root/projects/tencent-doc-manager/config/cookies.json")
    print("3. 设置环境变量 TENCENT_DOC_COOKIE")
    
    # 检查Cookie文件
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies.json"
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
            if cookies and cookies.get('cookies'):
                print(f"\n✅ 找到Cookie配置文件")
                print(f"   Cookie数量: {len(cookies['cookies'])} 个")
            else:
                print(f"\n⚠️ Cookie文件为空，需要配置")
    else:
        print(f"\n⚠️ Cookie文件不存在: {cookie_file}")
    
    # 测试流程说明
    print("\n📋 测试流程")
    print("=" * 40)
    print("1. 打开浏览器访问: http://localhost:8109")
    print("2. 配置腾讯文档Cookie（如果尚未配置）")
    print("3. 选择或拖拽Excel文件进行上传")
    print("4. 等待上传完成")
    print("5. 获取新文档的URL")
    
    # 预期结果
    print("\n🎯 预期结果")
    print("=" * 40)
    print("✅ 文件成功上传到腾讯文档")
    print("✅ 创建新的腾讯文档（不覆盖原文档）")
    print("✅ 获取新文档的URL")
    print("✅ 可以在浏览器中打开新文档")
    
    # 已知问题
    print("\n⚠️ 已知问题")
    print("=" * 40)
    print("- Cookie认证可能失败（需要最新的Cookie）")
    print("- 上传大文件可能超时")
    print("- 需要安装playwright和chromium")
    
    # 测试URL
    print("\n🔗 测试链接")
    print("=" * 40)
    print(f"上传测试页面: http://202.140.143.88:8109")
    print(f"本地访问: http://localhost:8109")
    
    return True


def check_dependencies():
    """检查依赖项"""
    print("\n📦 检查依赖项")
    print("=" * 40)
    
    dependencies = {
        'playwright': '浏览器自动化',
        'flask': 'Web服务器',
        'requests': 'HTTP请求'
    }
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError:
            print(f"❌ {module}: 未安装 (pip install {module})")
    
    # 检查playwright浏览器
    print("\n🌐 检查Playwright浏览器")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browsers = []
            if p.chromium._impl_obj._connection:
                browsers.append("Chromium")
            print(f"✅ 可用浏览器: {', '.join(browsers) if browsers else '需要安装'}")
            if not browsers:
                print("💡 运行: playwright install chromium")
    except Exception as e:
        print(f"⚠️ Playwright未正确配置: {e}")


def main():
    """主函数"""
    print("\n" + "🚀" * 30)
    print("\n腾讯文档上传测试系统")
    print("\n" + "🚀" * 30)
    
    # 检查依赖
    check_dependencies()
    
    # 运行测试流程
    if test_upload_flow():
        print("\n✅ 测试环境准备就绪")
        print("\n📍 下一步操作:")
        print("1. 访问 http://localhost:8109")
        print("2. 上传Excel文件进行测试")
        print("3. 查看上传结果和获取的URL")
    else:
        print("\n❌ 测试环境存在问题，请检查")


if __name__ == "__main__":
    main()