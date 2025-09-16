#!/usr/bin/env python3
import asyncio
import json
import sys
sys.path.insert(0, '/root/projects/tencent-doc-manager')
from production.core_modules.tencent_export_automation import TencentDocAutoExporter
import glob
from pathlib import Path
import time

async def test_download_with_scan():
    print("🧪 测试文件系统扫描修复...")
    
    # 加载Cookie
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    cookie = config.get('cookie', '')
    
    if not cookie:
        print("❌ Cookie为空，请先设置Cookie")
        return False
        
    print(f"✅ Cookie长度: {len(cookie)}")
    
    # 创建导出器
    exporter = TencentDocAutoExporter()
    
    # 测试URL
    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
    
    # 扫描下载前的文件
    csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions')
    before_files = set(csv_dir.glob('**/*.csv'))
    print(f"📁 下载前CSV文件数: {len(before_files)}")
    
    # 执行下载
    print(f"📥 开始下载: {test_url}")
    start_time = time.time()
    
    try:
        result = await exporter.export_document(test_url, 'csv', cookie)
        download_time = time.time() - start_time
        
        print(f"⏱️ 下载耗时: {download_time:.2f}秒")
        
        if result:
            print(f"✅ 导出器返回路径: {result}")
        else:
            print("⚠️ 导出器返回空路径")
            
            # 扫描下载后的文件
            time.sleep(2)  # 等待文件写入完成
            after_files = set(csv_dir.glob('**/*.csv'))
            new_files = after_files - before_files
            
            if new_files:
                print(f"🔍 通过文件系统扫描找到 {len(new_files)} 个新文件:")
                for f in sorted(new_files, key=lambda x: x.stat().st_mtime, reverse=True):
                    print(f"   📄 {f}")
                    # 返回最新的文件
                    result = str(f)
                    print(f"✅ 使用最新文件: {result}")
            else:
                print("❌ 没有找到新下载的文件")
                return False
                
        return result
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭浏览器
        if hasattr(exporter, 'browser') and exporter.browser:
            try:
                await exporter.browser.close()
            except:
                pass

# 运行测试
if __name__ == "__main__":
    result = asyncio.run(test_download_with_scan())
    if result:
        print(f"\n🎉 测试成功！文件路径: {result}")
    else:
        print("\n❌ 测试失败")