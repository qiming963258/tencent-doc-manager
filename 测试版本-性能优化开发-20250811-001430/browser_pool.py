#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器池管理器 - 性能优化核心组件
适配4H2G服务器配置的轻量化浏览器池
"""

import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import psutil
import os


@dataclass
class BrowserInstance:
    """浏览器实例信息"""
    browser: Browser
    context: BrowserContext
    page: Page
    in_use: bool = False
    created_at: float = 0
    last_used: float = 0
    task_count: int = 0


class OptimizedBrowserPool:
    """优化的浏览器池管理器"""
    
    def __init__(self, max_instances=3, max_memory_mb=1500):
        self.max_instances = max_instances  # 适配4H2G配置
        self.max_memory_mb = max_memory_mb  # 内存限制1.5GB
        self.instances: Dict[str, BrowserInstance] = {}
        self.playwright = None
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
    async def start(self):
        """启动浏览器池"""
        self.playwright = await async_playwright().start()
        
        # 预创建2个浏览器实例
        for i in range(2):
            await self._create_instance(f"pool_{i}")
        
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info(f"浏览器池启动，预创建{len(self.instances)}个实例")
    
    async def _create_instance(self, instance_id: str) -> BrowserInstance:
        """创建优化的浏览器实例"""
        # Ubuntu优化的启动参数
        launch_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',  # 减少内存使用
            '--disable-gpu',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # 不加载图片，加快速度
            '--disable-javascript',  # 部分页面可以禁用JS
            '--memory-pressure-off',
            '--max_old_space_size=512',  # 限制V8内存
        ]
        
        browser = await self.playwright.chromium.launch(
            headless=True,
            args=launch_args
        )
        
        # 创建轻量化上下文
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Linux x86_64) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        # 优化页面性能
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", 
                        lambda route: route.abort())  # 阻止静态资源
        
        instance = BrowserInstance(
            browser=browser,
            context=context,
            page=page,
            created_at=time.time()
        )
        
        self.instances[instance_id] = instance
        self.logger.info(f"创建浏览器实例: {instance_id}")
        return instance
    
    async def get_instance(self, preferred_id: Optional[str] = None) -> tuple[str, BrowserInstance]:
        """获取可用的浏览器实例"""
        async with self._lock:
            # 检查内存使用
            if self._check_memory_pressure():
                await self._cleanup_unused()
            
            # 优先使用指定实例
            if preferred_id and preferred_id in self.instances:
                instance = self.instances[preferred_id]
                if not instance.in_use:
                    instance.in_use = True
                    instance.last_used = time.time()
                    instance.task_count += 1
                    return preferred_id, instance
            
            # 查找空闲实例
            for instance_id, instance in self.instances.items():
                if not instance.in_use:
                    instance.in_use = True
                    instance.last_used = time.time()
                    instance.task_count += 1
                    return instance_id, instance
            
            # 如果没有空闲实例且未达到最大数量，创建新实例
            if len(self.instances) < self.max_instances:
                new_id = f"pool_{len(self.instances)}"
                instance = await self._create_instance(new_id)
                instance.in_use = True
                instance.last_used = time.time()
                instance.task_count += 1
                return new_id, instance
            
            # 等待实例释放
            self.logger.warning("所有浏览器实例都在使用中，等待释放...")
            while True:
                await asyncio.sleep(0.5)
                for instance_id, instance in self.instances.items():
                    if not instance.in_use:
                        instance.in_use = True
                        instance.last_used = time.time()
                        instance.task_count += 1
                        return instance_id, instance
    
    async def release_instance(self, instance_id: str):
        """释放浏览器实例"""
        async with self._lock:
            if instance_id in self.instances:
                self.instances[instance_id].in_use = False
                self.instances[instance_id].last_used = time.time()
                self.logger.debug(f"释放浏览器实例: {instance_id}")
    
    def _check_memory_pressure(self) -> bool:
        """检查内存压力"""
        try:
            memory_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            return memory_mb > self.max_memory_mb
        except:
            return False
    
    async def _cleanup_unused(self):
        """清理未使用的实例"""
        current_time = time.time()
        to_remove = []
        
        for instance_id, instance in self.instances.items():
            # 保留至少1个实例，清理5分钟未使用的实例
            if (len(self.instances) > 1 and 
                not instance.in_use and 
                current_time - instance.last_used > 300):
                to_remove.append(instance_id)
        
        for instance_id in to_remove:
            await self._remove_instance(instance_id)
    
    async def _remove_instance(self, instance_id: str):
        """移除浏览器实例"""
        if instance_id in self.instances:
            instance = self.instances[instance_id]
            try:
                await instance.page.close()
                await instance.context.close()
                await instance.browser.close()
            except:
                pass
            del self.instances[instance_id]
            self.logger.info(f"移除浏览器实例: {instance_id}")
    
    async def _cleanup_loop(self):
        """定期清理循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                async with self._lock:
                    await self._cleanup_unused()
                    
                    # 内存监控
                    memory_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                    self.logger.debug(f"当前内存使用: {memory_mb:.1f}MB")
                    
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")
    
    async def get_pool_stats(self) -> dict:
        """获取池状态统计"""
        total = len(self.instances)
        in_use = sum(1 for inst in self.instances.values() if inst.in_use)
        
        try:
            memory_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0
        
        return {
            "total_instances": total,
            "in_use": in_use,
            "available": total - in_use,
            "memory_mb": round(memory_mb, 1),
            "instances": {
                id: {
                    "in_use": inst.in_use,
                    "task_count": inst.task_count,
                    "age_seconds": int(time.time() - inst.created_at)
                }
                for id, inst in self.instances.items()
            }
        }
    
    async def cleanup(self):
        """清理所有资源"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        for instance_id in list(self.instances.keys()):
            await self._remove_instance(instance_id)
        
        if self.playwright:
            await self.playwright.stop()
        
        self.logger.info("浏览器池已清理")


# 全局浏览器池实例
_browser_pool: Optional[OptimizedBrowserPool] = None

async def get_browser_pool() -> OptimizedBrowserPool:
    """获取全局浏览器池"""
    global _browser_pool
    if _browser_pool is None:
        _browser_pool = OptimizedBrowserPool()
        await _browser_pool.start()
    return _browser_pool

async def cleanup_browser_pool():
    """清理全局浏览器池"""
    global _browser_pool
    if _browser_pool:
        await _browser_pool.cleanup()
        _browser_pool = None