#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的上传功能
"""

import asyncio
import json
from pathlib import Path
from production.core_modules.tencent_doc_upload_production import quick_upload

async def test_upload():
    """测试修复后的上传功能"""
    
    print("=" * 60)
    print("测试修复后的上传功能")
    print("=" * 60)
    
    # 读取Cookie
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ 找不到config.json")
        return
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        cookie_string = config.get('cookie', '')
    
    if not cookie_string:
        print("❌ Cookie为空")
        return
    
    # 测试文件
    test_file = Path('/root/projects/tencent-doc-manager/excel_outputs/risk_analysis_report_20250819_024132.xlsx')
    if not test_file.exists():
        # 创建测试文件
        test_file = Path('/tmp/test_upload.txt')
        test_file.write_text("测试上传内容 - " + str(Path.cwd()))
    
    print(f"\n📁 测试文件: {test_file}")
    print(f"📏 文件大小: {test_file.stat().st_size} bytes")
    
    # 执行上传
    print("\n🚀 开始上传...")
    result = await quick_upload(
        cookie_string=cookie_string,
        file_path=str(test_file),
        headless=True
    )
    
    print("\n📊 上传结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  消息: {result.get('message')}")
    print(f"  URL: {result.get('url')}")
    print(f"  文档名: {result.get('doc_name')}")
    
    if result.get('success'):
        print("\n✅ 上传测试成功！")
        if result.get('url') and '/desktop/' not in result.get('url'):
            print(f"🔗 访问文档: {result.get('url')}")
        else:
            print("📝 文档已上传到文档列表，请手动查看")
    else:
        print(f"\n❌ 上传测试失败: {result.get('message')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_upload())