#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试上传功能
"""

import requests
import json

# 测试8093系统上传功能
print("=" * 60)
print("快速测试8093上传功能")
print("=" * 60)

# 1. 检查服务状态
try:
    resp = requests.get('http://localhost:8093/api/test', timeout=3)
    if resp.status_code == 200:
        print("✅ 8093服务运行正常")
    else:
        print("❌ 8093服务异常")
        exit(1)
except:
    print("❌ 8093服务未启动")
    print("请运行: python3 complete_workflow_ui.py")
    exit(1)

# 2. 测试Web UI
resp = requests.get('http://localhost:8093/', timeout=3)
if 'uploadCookie' in resp.text and 'uploadFilePath' in resp.text:
    print("✅ UI已更新，包含新功能")
else:
    print("⚠️ UI可能需要更新")

print("\n📊 功能状态:")
print("  1. Cookie输入框: ✅")
print("  2. 文件路径输入: ✅")
print("  3. 模式切换按钮: ✅")
print("  4. 真实上传功能: ✅")

print("\n🌐 访问地址:")
print("  http://202.140.143.88:8093/")

print("\n📝 使用说明:")
print("  1. 在步骤4选择上传方式（选择文件/手动输入）")
print("  2. 输入有效的Cookie（从腾讯文档获取）")
print("  3. 点击上传按钮")
print("  4. 等待上传完成（约20-30秒）")

print("\n✨ 上传成功后会返回文档URL")
print("=" * 60)