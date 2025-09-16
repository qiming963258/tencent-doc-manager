#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实上传测试脚本
使用已配置的Cookie测试上传到腾讯文档
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from tencent_upload_enhanced import TencentDocUploadEnhanced


async def test_real_upload():
    """测试真实上传功能"""
    
    print("\n" + "="*60)
    print("🚀 腾讯文档真实上传测试")
    print("="*60)
    
    # 测试文件
    test_file = "/root/projects/tencent-doc-manager/excel_test/test_upload_20250909.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print(f"✅ 找到测试文件: {test_file}")
    print(f"   文件大小: {os.path.getsize(test_file)} 字节")
    
    # 读取Cookie配置
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies.json"
    
    if not os.path.exists(cookie_file):
        print(f"❌ Cookie文件不存在: {cookie_file}")
        return False
    
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_data = json.load(f)
    
    print(f"✅ 加载Cookie配置")
    print(f"   Cookie数量: {len(cookie_data.get('cookies', []))} 个")
    
    # 创建上传器
    uploader = TencentDocUploadEnhanced()
    
    try:
        print("\n📤 开始上传...")
        print("   1. 初始化浏览器...")
        await uploader.start_browser(headless=True)
        
        print("   2. 设置Cookie...")
        # 使用cookie_string格式
        if 'cookie_string' in cookie_data:
            await uploader.login_with_cookies(cookie_data['cookie_string'])
        else:
            # 将cookies列表转换为字符串
            cookie_pairs = []
            for cookie in cookie_data.get('cookies', []):
                cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
            cookie_string = '; '.join(cookie_pairs)
            await uploader.login_with_cookies(cookie_string)
        
        print("   3. 执行上传...")
        result = await uploader.upload_file(test_file)
        
        if result.get('success'):
            print("\n✅ 上传成功！")
            print(f"   新文档URL: {result.get('url', '未获取到')}")
            print(f"   文档名称: {result.get('filename', '未知')}")
            
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"/root/projects/tencent-doc-manager/upload_result_{timestamp}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 结果保存到: {result_file}")
            
            return True
        else:
            print(f"\n❌ 上传失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("\n🔚 清理资源...")
        await uploader.cleanup()


def main():
    """主函数"""
    print("\n" + "🎯"*30)
    print("\n腾讯文档上传功能真实测试")
    print("\n" + "🎯"*30)
    
    # 检查依赖
    try:
        from playwright.async_api import async_playwright
        print("\n✅ Playwright已安装")
    except ImportError:
        print("\n❌ 需要安装Playwright: pip install playwright")
        print("   然后运行: playwright install chromium")
        return
    
    # 运行测试
    success = asyncio.run(test_real_upload())
    
    if success:
        print("\n🎉 测试完成！上传功能正常工作")
        print("\n📋 下一步：")
        print("1. 检查上传的文档URL")
        print("2. 在浏览器中打开验证")
        print("3. 确认文件内容和格式正确")
    else:
        print("\n⚠️ 测试失败，请检查：")
        print("1. Cookie是否有效")
        print("2. 网络连接是否正常")
        print("3. 腾讯文档服务是否可用")


if __name__ == "__main__":
    main()