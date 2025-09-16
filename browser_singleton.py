#!/usr/bin/env python3
"""
浏览器单例管理器 - 复用浏览器实例，避免重复创建
"""

import asyncio
import os
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import time

class BrowserSingleton:
    """浏览器单例模式实现"""
    
    _instance = None
    _browser: Optional[Browser] = None
    _playwright = None
    _context: Optional[BrowserContext] = None
    _last_used = 0
    _max_idle_time = 300  # 5分钟空闲后自动关闭
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_browser(self) -> Browser:
        """获取浏览器实例（复用或创建新的）"""
        current_time = time.time()
        
        # 检查是否需要重新创建（超时或未初始化）
        if (self._browser is None or 
            not self._browser.is_connected() or
            (current_time - self._last_used > self._max_idle_time)):
            
            # 先清理旧实例
            await self.cleanup()
            
            print("🚀 创建新的浏览器实例（单例模式）...")
            
            # 创建playwright
            self._playwright = await async_playwright().start()
            
            # 启动浏览器（内存优化配置）
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',  # 关键：使用/tmp而不是/dev/shm
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-images',  # 不加载图片，节省内存
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-features=site-per-process',
                    '--renderer-process-limit=1',  # 限制渲染进程数
                    '--memory-model=low',  # 低内存模式
                    '--max_old_space_size=512',  # 限制V8堆大小
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--mute-audio'
                ]
            )
            
            print("✅ 浏览器实例创建成功（单例）")
        else:
            print("♻️ 复用现有浏览器实例")
        
        self._last_used = current_time
        return self._browser
    
    async def get_context(self, **kwargs) -> BrowserContext:
        """获取浏览器上下文（复用或创建新的）"""
        browser = await self.get_browser()
        
        # 如果没有context或需要新的，创建一个
        if self._context is None or not kwargs.get('reuse_context', True):
            # 关闭旧的context
            if self._context:
                try:
                    await self._context.close()
                except:
                    pass
            
            # 创建新context
            self._context = await browser.new_context(
                accept_downloads=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 720},
                **kwargs
            )
            print("✅ 创建新的浏览器上下文")
        else:
            print("♻️ 复用现有浏览器上下文")
        
        return self._context
    
    async def get_page(self, new_page=False) -> Page:
        """获取页面实例"""
        context = await self.get_context()
        
        # 获取现有页面或创建新页面
        pages = context.pages
        if pages and not new_page:
            print("♻️ 复用现有页面")
            return pages[0]
        else:
            print("📄 创建新页面")
            return await context.new_page()
    
    async def cleanup(self):
        """清理资源"""
        print("🧹 清理浏览器资源...")
        
        # 关闭所有页面
        if self._context:
            try:
                await self._context.close()
            except:
                pass
            self._context = None
        
        # 关闭浏览器
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass
            self._browser = None
        
        # 停止playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except:
                pass
            self._playwright = None
        
        self._last_used = 0
        print("✅ 浏览器资源已清理")
    
    async def refresh_if_needed(self):
        """检查并刷新浏览器（如果需要）"""
        if self._browser and not self._browser.is_connected():
            print("⚠️ 浏览器连接已断开，重新创建...")
            await self.cleanup()
            await self.get_browser()
    
    def get_memory_info(self) -> dict:
        """获取内存使用信息"""
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        return {
            'memory_mb': memory_mb,
            'browser_active': self._browser is not None and self._browser.is_connected(),
            'idle_seconds': time.time() - self._last_used if self._last_used > 0 else 0
        }


# 全局单例实例
browser_singleton = BrowserSingleton()


async def test_singleton():
    """测试单例模式"""
    print("="*60)
    print("浏览器单例模式测试")
    print("="*60)
    
    # 第一次获取
    print("\n第一次获取浏览器:")
    browser1 = await browser_singleton.get_browser()
    page1 = await browser_singleton.get_page()
    
    # 显示内存信息
    info = browser_singleton.get_memory_info()
    print(f"📊 内存使用: {info['memory_mb']:.2f}MB")
    
    # 第二次获取（应该复用）
    print("\n第二次获取浏览器:")
    browser2 = await browser_singleton.get_browser()
    page2 = await browser_singleton.get_page()
    
    # 验证是同一个实例
    print(f"✅ 是否同一浏览器: {browser1 == browser2}")
    print(f"✅ 是否同一页面: {page1 == page2}")
    
    # 清理
    await browser_singleton.cleanup()
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_singleton())