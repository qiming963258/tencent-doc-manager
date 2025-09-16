#!/usr/bin/env python3
"""使用修复后的登录方式测试文件上传"""

import asyncio
import os
from tencent_upload_enhanced import TencentDocUploadEnhanced

async def test_upload():
    """测试文件上传功能"""
    uploader = TencentDocUploadEnhanced()
    
    try:
        print("="*50)
        print("腾讯文档上传测试 - 使用改进的登录方法")
        print("="*50)
        
        # 1. 启动浏览器（可见模式）
        print("\n1. 启动浏览器...")
        success = await uploader.start_browser(headless=False)
        if not success:
            print("浏览器启动失败")
            return
        print("浏览器启动成功")
        
        # 2. 从配置文件加载Cookie
        print("\n2. 加载Cookie配置...")
        import json
        config_file = 'config/cookies.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cookie_string = config.get('cookie_string', '')
        else:
            print("未找到Cookie配置文件")
            return
        
        # 3. 使用Cookie登录（现在使用改进的方法）
        print("\n3. 使用改进的Cookie登录方法...")
        login_success = await uploader.login_with_cookies(cookie_string)
        
        if login_success:
            print("登录成功！")
        else:
            print("登录可能失败，但继续尝试上传...")
        
        # 4. 等待页面稳定
        print("\n4. 等待页面稳定...")
        await asyncio.sleep(3)
        
        # 5. 选择测试文件
        test_files = [
            "副本-副本-测试版本-出国销售计划表.xlsx",
            "test_files/test_upload_20250909.xlsx"
        ]
        
        test_file = None
        for file in test_files:
            if os.path.exists(file):
                test_file = file
                break
        
        if not test_file:
            print("未找到测试文件")
            return
        
        print(f"\n5. 准备上传文件: {test_file}")
        file_size = os.path.getsize(test_file)
        print(f"文件大小: {file_size:,} 字节")
        
        # 6. 执行上传
        print("\n6. 开始上传...")
        result = await uploader.upload_file(test_file)
        
        # 7. 显示结果
        print("\n7. 上传结果:")
        print(f"成功: {result.get('success', False)}")
        if result.get('url'):
            print(f"文档URL: {result['url']}")
        if result.get('message'):
            print(f"消息: {result['message']}")
        
        # 8. 等待观察
        print("\n等待30秒供观察结果...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        await uploader.cleanup()
        print("\n测试完成")

if __name__ == "__main__":
    asyncio.run(test_upload())