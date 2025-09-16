#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传 - Windows可视化调试工具
支持非headless模式，可以看到浏览器操作过程
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 导入上传模块
from tencent_upload_enhanced import TencentDocUploadEnhanced


class VisualDebugger:
    """可视化调试器"""
    
    def __init__(self):
        self.uploader = None
        self.config_file = 'config/cookies.json'
        
    async def start_visual_browser(self):
        """启动可视化浏览器"""
        logger.info("🚀 启动可视化浏览器（非headless模式）...")
        self.uploader = TencentDocUploadEnhanced()
        
        # 重要：设置headless=False以显示浏览器
        success = await self.uploader.start_browser(headless=False)
        
        if success:
            logger.info("✅ 浏览器启动成功，您可以看到操作过程")
        else:
            logger.error("❌ 浏览器启动失败")
            
        return success
    
    async def load_and_apply_cookies(self):
        """加载并应用Cookie"""
        try:
            # 读取Cookie配置
            if not os.path.exists(self.config_file):
                logger.warning(f"⚠️ Cookie文件不存在: {self.config_file}")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            cookie_string = cookie_data.get('cookie_string', '')
            if not cookie_string:
                logger.warning("⚠️ Cookie字符串为空")
                return False
            
            logger.info(f"📝 加载了 {len(cookie_data.get('cookies', []))} 个Cookie")
            
            # 应用Cookie
            success = await self.uploader.login_with_cookies(cookie_string)
            
            if success:
                logger.info("✅ Cookie应用成功")
            else:
                logger.warning("⚠️ Cookie应用可能失败，但继续尝试")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Cookie加载失败: {e}")
            return False
    
    async def test_upload(self, file_path: str):
        """测试上传文件"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ 文件不存在: {file_path}")
                return None
            
            logger.info(f"📤 开始上传文件: {file_path}")
            logger.info(f"   文件大小: {os.path.getsize(file_path)} 字节")
            
            # 执行上传
            result = await self.uploader.upload_file(file_path)
            
            if result.get('success'):
                logger.info("✅ 上传成功！")
                logger.info(f"📎 新文档URL: {result.get('url', '未获取到')}")
                logger.info(f"📄 文档名称: {result.get('filename', '未知')}")
            else:
                logger.error(f"❌ 上传失败: {result.get('message', '未知错误')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def interactive_mode(self):
        """交互式调试模式"""
        logger.info("\n" + "="*60)
        logger.info("🎮 进入交互式调试模式")
        logger.info("="*60)
        
        # 启动浏览器
        if not await self.start_visual_browser():
            return
        
        # 加载Cookie
        await self.load_and_apply_cookies()
        
        while True:
            print("\n" + "-"*40)
            print("请选择操作：")
            print("1. 上传测试文件")
            print("2. 上传自定义文件")
            print("3. 重新加载Cookie")
            print("4. 访问腾讯文档主页")
            print("5. 等待观察（30秒）")
            print("0. 退出")
            print("-"*40)
            
            choice = input("请输入选项: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                # 上传测试文件
                test_file = 'test_files/test_upload_20250909.xlsx'
                if os.path.exists(test_file):
                    await self.test_upload(test_file)
                else:
                    logger.warning(f"测试文件不存在: {test_file}")
            elif choice == '2':
                # 上传自定义文件
                file_path = input("请输入文件路径: ").strip()
                if file_path:
                    await self.test_upload(file_path)
            elif choice == '3':
                # 重新加载Cookie
                await self.load_and_apply_cookies()
            elif choice == '4':
                # 访问主页
                await self.uploader.page.goto('https://docs.qq.com')
                logger.info("已导航到腾讯文档主页")
            elif choice == '5':
                # 等待观察
                logger.info("等待30秒，您可以手动操作浏览器...")
                await asyncio.sleep(30)
            else:
                print("无效选项")
        
        # 清理
        if self.uploader:
            await self.uploader.cleanup()
            
    async def quick_test(self):
        """快速测试模式"""
        logger.info("\n" + "="*60)
        logger.info("⚡ 快速测试模式")
        logger.info("="*60)
        
        # 启动浏览器
        if not await self.start_visual_browser():
            return
        
        # 加载Cookie
        if not await self.load_and_apply_cookies():
            logger.warning("Cookie加载失败，但继续测试")
        
        # 等待用户观察
        logger.info("\n⏱️ 浏览器已打开，等待5秒让您观察...")
        await asyncio.sleep(5)
        
        # 上传测试文件
        test_file = 'test_files/test_upload_20250909.xlsx'
        if os.path.exists(test_file):
            await self.test_upload(test_file)
        else:
            logger.warning(f"测试文件不存在: {test_file}")
        
        # 等待观察结果
        logger.info("\n⏱️ 上传完成，等待30秒让您观察结果...")
        logger.info("💡 提示：您可以手动操作浏览器查看上传的文档")
        await asyncio.sleep(30)
        
        # 清理
        if self.uploader:
            await self.uploader.cleanup()


async def main():
    """主函数"""
    print("\n" + "="*30)
    print("\n腾讯文档上传 - Windows可视化调试工具")
    print("\n" + "="*30)
    
    debugger = VisualDebugger()
    
    # 选择模式
    print("\n请选择运行模式：")
    print("1. 交互式调试（推荐）")
    print("2. 快速测试")
    print("0. 退出")
    
    mode = input("\n请输入选项: ").strip()
    
    if mode == '1':
        await debugger.interactive_mode()
    elif mode == '2':
        await debugger.quick_test()
    else:
        print("退出程序")


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())