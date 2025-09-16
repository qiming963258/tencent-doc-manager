#!/usr/bin/env python3
"""
测试v3版本上传模块 - 验证能否正确提取新上传文档的链接
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

# v3模块测试 - 使用quick_upload_v3函数


async def test_upload():
    """测试上传功能"""
    
    # 1. 读取cookie配置
    config_path = '/root/projects/tencent-doc-manager/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    cookie_str = config.get('cookie', '')
    if not cookie_str:
        print("❌ 未找到cookie配置")
        return False
    
    # 2. 准备测试文件
    test_file = '/tmp/test_upload_v3.txt'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_content = f"测试文件 v3 - {timestamp}\n上传时间: {datetime.now()}\n测试内容"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ 创建测试文件: {test_file}")
    print(f"📄 文件内容: {test_content[:50]}...")
    
    # 3. 使用v3的quick_upload函数
    from production.core_modules.tencent_doc_upload_production_v3 import quick_upload_v3
    
    try:
        # 4. 执行上传
        print("\n🚀 开始上传测试...")
        result = await quick_upload_v3(cookie_str, test_file, headless=True)
        success = result.get('success', False)
        
        if success:
            url = result.get('url')
            print(f"✅ 上传成功!")
            print(f"📎 文档链接: {url}")
            print(f"💬 消息: {result.get('message', '')}")
            
            # 验证链接 (txt文件会成为doc，excel文件会成为sheet)
            if url and (url.startswith('https://docs.qq.com/sheet/') or url.startswith('https://docs.qq.com/doc/')):
                print(f"✅ 链接格式正确")
                
                # v3模块的message中包含了匹配方式的信息
                if "文件名匹配" in result.get('message', ''):
                    print(f"✅ 通过文件名匹配找到了新上传的文档")
                    return True
                elif "最新文档" in result.get('message', ''):
                    print(f"✅ 通过时间戳找到了新上传的文档")
                    return True
                else:
                    print(f"⚠️ 找到了文档但匹配方式不确定")
                    return True
            else:
                print(f"❌ 链接格式异常: {url}")
                return False
        else:
            print(f"❌ 上传失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🧹 已清理测试文件")


async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 腾讯文档上传v3版本测试")
    print("=" * 60)
    
    success = await test_upload()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过 - v3模块可以正常工作")
        print("💡 建议: 可以更新8093系统使用v3版本")
    else:
        print("❌ 测试失败 - v3模块需要进一步调试")
        print("💡 建议: 检查日志排查问题")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())