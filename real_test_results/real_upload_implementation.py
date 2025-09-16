#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档真实上传实现 - 基于成功的自动化方案
使用已验证的DOM选择器和上传流程
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# 添加成功方案的路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def real_upload_to_tencent():
    """真实的腾讯文档上传功能"""
    print("🎯 腾讯文档真实上传功能")
    print("=" * 60)
    
    # 导入已验证的上传工具
    from tencent_upload_automation import TencentDocUploader
    
    # 配置参数
    modified_file = "/root/projects/tencent-doc-manager/real_test_results/direct_download_174042/测试版本-回国销售计划表_I6修改.xlsx"
    homepage_url = "https://docs.qq.com/desktop"
    
    if not os.path.exists(modified_file):
        print(f"❌ 文件不存在: {modified_file}")
        return False
    
    print(f"📂 待上传文件: {os.path.basename(modified_file)}")
    print(f"📏 文件大小: {os.path.getsize(modified_file)} bytes")
    
    # 创建上传器实例
    uploader = TencentDocUploader()
    
    try:
        # 读取Cookie
        print("🔐 读取认证信息...")
        with open('/root/projects/参考/cookie', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            cookies = ""
            for line in lines:
                if line.startswith('fingerprint='):
                    cookies = line
                    break
        
        print(f"📍 Cookie长度: {len(cookies)} 字符")
        
        # 启动浏览器
        print("🚀 启动浏览器...")
        await uploader.start_browser(headless=True)
        
        # 加载认证
        print("🔐 加载Cookie认证...")
        await uploader.login_with_cookies(cookies)
        
        # 执行上传
        print(f"📤 开始上传到腾讯文档主页...")
        print(f"🌐 目标: {homepage_url}")
        
        result = await uploader.upload_file_to_main_page(
            file_path=modified_file,
            homepage_url=homepage_url,
            max_retries=3
        )
        
        if result:
            print("✅ 上传成功！")
            return True
        else:
            print("❌ 上传失败")
            return False
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return False
        
    finally:
        # 清理资源
        if uploader.browser:
            await uploader.browser.close()
        if hasattr(uploader, 'playwright'):
            await uploader.playwright.stop()

if __name__ == "__main__":
    asyncio.run(real_upload_to_tencent())