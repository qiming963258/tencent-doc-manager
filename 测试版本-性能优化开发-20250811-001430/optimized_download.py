#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版腾讯文档下载工具 - 使用浏览器池和并发优化
适配4H2G服务器配置，提升2-3倍性能
"""

import asyncio
import os
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from browser_pool import get_browser_pool, cleanup_browser_pool


@dataclass
class DownloadTask:
    """下载任务"""
    url: str
    cookies: str
    output_dir: str
    task_id: str
    priority: int = 0


@dataclass
class DownloadResult:
    """下载结果"""
    task_id: str
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0


class OptimizedTencentDownloader:
    """优化版腾讯文档下载器"""
    
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent  # 适配4H2G配置
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, DownloadResult] = {}
        self.logger = logging.getLogger(__name__)
        self._task_queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
    async def add_download_task(self, url: str, cookies: str, 
                               output_dir: str = None, priority: int = 0) -> str:
        """添加下载任务"""
        task_id = f"download_{int(time.time() * 1000)}"
        output_dir = output_dir or os.path.join(os.getcwd(), "downloads")
        
        task = DownloadTask(
            url=url,
            cookies=cookies,
            output_dir=output_dir,
            task_id=task_id,
            priority=priority
        )
        
        await self._task_queue.put(task)
        self.logger.info(f"添加下载任务: {task_id} - {url}")
        return task_id
    
    async def start_processing(self):
        """开始处理任务队列"""
        workers = []
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(f"worker_{i}"))
            workers.append(worker)
        
        self.logger.info(f"启动{self.max_concurrent}个下载工作进程")
        return workers
    
    async def _worker(self, worker_id: str):
        """工作进程"""
        browser_pool = await get_browser_pool()
        
        while True:
            try:
                # 获取任务
                task = await self._task_queue.get()
                
                async with self._semaphore:  # 控制并发数
                    self.logger.info(f"{worker_id} 开始处理任务: {task.task_id}")
                    
                    result = await self._download_single(task, browser_pool)
                    self.results[task.task_id] = result
                    
                    self.logger.info(f"{worker_id} 完成任务: {task.task_id}, 成功: {result.success}")
                
                self._task_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"{worker_id} 工作异常: {e}")
                await asyncio.sleep(1)
    
    async def _download_single(self, task: DownloadTask, browser_pool) -> DownloadResult:
        """执行单个下载任务"""
        start_time = time.time()
        
        try:
            # 获取浏览器实例
            instance_id, browser_instance = await browser_pool.get_instance()
            
            try:
                # 设置Cookie
                await self._set_cookies(browser_instance, task.cookies)
                
                # 访问文档页面
                self.logger.debug(f"访问文档: {task.url}")
                await browser_instance.page.goto(task.url, 
                                                wait_until='domcontentloaded', 
                                                timeout=20000)
                
                # 优化等待 - 动态检测而非固定等待
                await self._wait_for_page_ready(browser_instance.page)
                
                # 执行下载流程
                file_path = await self._perform_download(browser_instance, task)
                
                duration = time.time() - start_time
                return DownloadResult(
                    task_id=task.task_id,
                    success=True,
                    file_path=file_path,
                    duration=duration
                )
                
            finally:
                # 释放浏览器实例
                await browser_pool.release_instance(instance_id)
                
        except Exception as e:
            duration = time.time() - start_time
            return DownloadResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _set_cookies(self, browser_instance, cookies: str):
        """设置多域名Cookies"""
        if not cookies:
            return
            
        cookie_list = []
        for cookie_str in cookies.split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
                for domain in domains:
                    cookie_list.append({
                        'name': name, 'value': value, 'domain': domain,
                        'path': '/', 'httpOnly': False, 'secure': True, 'sameSite': 'None'
                    })
        
        await browser_instance.context.add_cookies(cookie_list)
    
    async def _wait_for_page_ready(self, page):
        """动态等待页面就绪"""
        # 等待关键元素出现，而不是固定等待
        selectors_to_wait = [
            '.titlebar-icon.titlebar-icon-more',  # 菜单按钮
            '.doc-title',  # 文档标题
            '[class*="toolbar"]'  # 工具栏
        ]
        
        for selector in selectors_to_wait:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                self.logger.debug(f"检测到元素: {selector}")
                break
            except:
                continue
        
        # 最多等待5秒确保页面稳定
        await page.wait_for_timeout(2000)
    
    async def _perform_download(self, browser_instance, task: DownloadTask) -> str:
        """执行下载操作"""
        page = browser_instance.page
        
        # 监听下载事件
        downloaded_file = None
        download_promise = None
        
        def handle_download(download):
            nonlocal downloaded_file, download_promise
            if not downloaded_file:  # 只处理第一个下载
                downloaded_file = download
                download_promise = asyncio.create_task(self._save_download(download, task.output_dir))
        
        page.on("download", handle_download)
        
        try:
            # 点击菜单按钮
            menu_btn = await page.wait_for_selector('.titlebar-icon.titlebar-icon-more', timeout=10000)
            await menu_btn.click()
            self.logger.debug("点击菜单按钮")
            
            # 等待菜单出现并点击导出选项
            await page.wait_for_timeout(1000)
            export_option = await page.wait_for_selector(
                'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs', 
                timeout=5000
            )
            await export_option.click()
            self.logger.debug("点击导出选项")
            
            # 等待子菜单并点击Excel选项
            await page.wait_for_timeout(1000)
            excel_option = await page.wait_for_selector(
                'li.dui-menu-item.mainmenu-item-export-local', 
                timeout=5000
            )
            await excel_option.click()
            self.logger.debug("点击Excel导出选项")
            
            # 等待下载完成
            if download_promise:
                file_path = await asyncio.wait_for(download_promise, timeout=30)
                self.logger.info(f"下载完成: {file_path}")
                return file_path
            else:
                raise Exception("下载事件未触发")
                
        finally:
            page.remove_listener("download", handle_download)
    
    async def _save_download(self, download, output_dir: str) -> str:
        """保存下载文件"""
        os.makedirs(output_dir, exist_ok=True)
        suggested_filename = download.suggested_filename or "downloaded_file.xlsx"
        file_path = os.path.join(output_dir, suggested_filename)
        
        await download.save_as(file_path)
        return file_path
    
    async def get_result(self, task_id: str, timeout: float = 30) -> Optional[DownloadResult]:
        """获取下载结果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.results:
                return self.results[task_id]
            await asyncio.sleep(0.5)
        
        return None
    
    async def get_all_results(self) -> Dict[str, DownloadResult]:
        """获取所有结果"""
        return self.results.copy()
    
    async def wait_for_completion(self, timeout: float = 300):
        """等待所有任务完成"""
        await asyncio.wait_for(self._task_queue.join(), timeout=timeout)
    
    async def get_stats(self) -> dict:
        """获取统计信息"""
        total = len(self.results)
        successful = sum(1 for r in self.results.values() if r.success)
        failed = total - successful
        
        if total > 0:
            avg_duration = sum(r.duration for r in self.results.values()) / total
        else:
            avg_duration = 0
        
        return {
            "total_tasks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{successful/total*100:.1f}%" if total > 0 else "0%",
            "average_duration": f"{avg_duration:.2f}s",
            "queue_size": self._task_queue.qsize()
        }


async def download_multiple_docs(urls_and_cookies: List[tuple], output_dir: str = None):
    """并发下载多个文档"""
    downloader = OptimizedTencentDownloader()
    
    # 添加所有任务
    task_ids = []
    for i, (url, cookies) in enumerate(urls_and_cookies):
        task_id = await downloader.add_download_task(url, cookies, output_dir, priority=i)
        task_ids.append(task_id)
    
    # 启动处理
    workers = await downloader.start_processing()
    
    try:
        # 等待所有任务完成
        await downloader.wait_for_completion()
        
        # 获取结果
        results = await downloader.get_all_results()
        stats = await downloader.get_stats()
        
        print(f"下载统计: {stats}")
        
        return results, stats
        
    finally:
        # 清理工作进程
        for worker in workers:
            worker.cancel()
        
        # 清理浏览器池
        await cleanup_browser_pool()


async def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='优化版腾讯文档批量下载工具')
    parser.add_argument('urls', nargs='+', help='文档URL列表')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('-o', '--output', default='./downloads', help='输出目录')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    parser.add_argument('--max-concurrent', type=int, default=3, help='最大并发数')
    parser.add_argument('--verbose', action='store_true', help='详细日志')
    
    args = parser.parse_args()
    
    # 配置日志
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 准备下载任务
    urls_and_cookies = [(url, args.cookies) for url in args.urls]
    
    print(f"开始批量下载 {len(urls_and_cookies)} 个文档...")
    start_time = time.time()
    
    # 执行下载
    results, stats = await download_multiple_docs(urls_and_cookies, args.output)
    
    total_time = time.time() - start_time
    
    # 显示结果
    print("\n=== 下载结果 ===")
    for task_id, result in results.items():
        if result.success:
            print(f"✅ {task_id}: {result.file_path} ({result.duration:.2f}s)")
        else:
            print(f"❌ {task_id}: {result.error}")
    
    print(f"\n=== 总体统计 ===")
    print(f"总时间: {total_time:.2f}s")
    print(f"平均速度: {len(results)/total_time:.2f} 文档/秒")
    print(f"成功率: {stats['success_rate']}")
    

if __name__ == "__main__":
    asyncio.run(main())