#!/usr/bin/env python3
import json
import os
import sys
import glob
from pathlib import Path
import time

# 测试通过 auto_download_ui_system 下载
def test_download_with_ui_adapter():
    print("🧪 测试通过UI适配器下载...")
    
    # 加载Cookie
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    cookie = config.get('cookie', '')
    
    if not cookie:
        print("❌ Cookie为空，请先设置Cookie")
        return False
        
    print(f"✅ Cookie长度: {len(cookie)}")
    
    # 扫描下载前的文件
    csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions')
    before_files = set(csv_dir.glob('**/*.csv'))
    print(f"📁 下载前CSV文件数: {len(before_files)}")
    
    # 导入适配器
    from auto_download_ui_system import download_file_from_url
    
    # 测试URL
    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
    
    print(f"📥 开始下载: {test_url}")
    start_time = time.time()
    
    # 执行下载（Cookie从配置文件自动加载）
    result = download_file_from_url(test_url, 'csv')
    download_time = time.time() - start_time
    
    print(f"⏱️ 下载耗时: {download_time:.2f}秒")
    print(f"📊 下载结果: success={result.get('success')}")
    
    if result.get('success'):
        files = result.get('files', [])
        if files:
            print(f"✅ 成功下载 {len(files)} 个文件:")
            for f in files:
                print(f"   📄 {f}")
                # 检查文件是否存在
                if os.path.exists(f):
                    print(f"   ✓ 文件存在，大小: {os.path.getsize(f)} 字节")
                else:
                    print(f"   ✗ 文件不存在！")
            return files[0] if files else None
        else:
            print("⚠️ 下载成功但没有返回文件路径")
    else:
        print(f"❌ 下载失败: {result.get('error')}")
        
    # 如果没有返回路径，尝试扫描文件系统
    print("\n🔍 尝试扫描文件系统查找新文件...")
    time.sleep(2)
    after_files = set(csv_dir.glob('**/*.csv'))
    new_files = after_files - before_files
    
    if new_files:
        print(f"✅ 找到 {len(new_files)} 个新文件:")
        for f in sorted(new_files, key=lambda x: x.stat().st_mtime, reverse=True):
            print(f"   📄 {f}")
        return str(list(new_files)[0])
    else:
        print("❌ 没有找到新下载的文件")
        return None

if __name__ == "__main__":
    result = test_download_with_ui_adapter()
    if result:
        print(f"\n🎉 测试成功！文件路径: {result}")
    else:
        print("\n❌ 测试失败")