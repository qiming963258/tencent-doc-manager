#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版腾讯文档上传工具 - 使用浏览器池和智能等待优化
适配4H2G服务器配置，提升上传速度和并发能力
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
class UploadTask:
    """上传任务"""
    file_path: str
    cookies: str
    homepage_url: str
    task_id: str
    priority: int = 0


@dataclass
class UploadResult:
    """上传结果"""
    task_id: str
    file_path: str
    success: bool
    error: Optional[str] = None
    duration: float = 0


class OptimizedTencentUploader:
    """优化版腾讯文档上传器"""
    
    def __init__(self, max_concurrent=2):  # 上传比下载更消耗资源，减少并发数
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, UploadResult] = {}
        self.logger = logging.getLogger(__name__)
        self._task_queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
    async def add_upload_task(self, file_path: str, cookies: str, 
                             homepage_url: str = "https://docs.qq.com/desktop", 
                             priority: int = 0) -> str:
        """添加上传任务"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        task_id = f"upload_{int(time.time() * 1000)}"
        
        task = UploadTask(
            file_path=file_path,
            cookies=cookies,
            homepage_url=homepage_url,
            task_id=task_id,
            priority=priority
        )
        
        await self._task_queue.put(task)
        self.logger.info(f"添加上传任务: {task_id} - {file_path}")
        return task_id
    
    async def start_processing(self):
        """开始处理任务队列"""
        workers = []
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(f"upload_worker_{i}"))
            workers.append(worker)
        
        self.logger.info(f"启动{self.max_concurrent}个上传工作进程")
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
                    
                    result = await self._upload_single(task, browser_pool)
                    self.results[task.task_id] = result
                    
                    self.logger.info(f"{worker_id} 完成任务: {task.task_id}, 成功: {result.success}")
                
                self._task_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"{worker_id} 工作异常: {e}")
                await asyncio.sleep(1)
    
    async def _upload_single(self, task: UploadTask, browser_pool) -> UploadResult:
        """执行单个上传任务"""
        start_time = time.time()
        
        try:
            # 获取浏览器实例
            instance_id, browser_instance = await browser_pool.get_instance()
            
            try:
                # 设置Cookie
                await self._set_cookies(browser_instance, task.cookies)
                
                # 访问主页
                self.logger.debug(f"访问腾讯文档主页: {task.homepage_url}")
                await browser_instance.page.goto(task.homepage_url, 
                                                wait_until='domcontentloaded', 
                                                timeout=20000)
                
                # 智能等待页面就绪
                await self._wait_for_upload_page_ready(browser_instance.page)
                
                # 执行上传流程
                success = await self._perform_upload(browser_instance, task)
                
                duration = time.time() - start_time
                return UploadResult(
                    task_id=task.task_id,
                    file_path=task.file_path,
                    success=success,
                    duration=duration
                )
                
            finally:
                # 释放浏览器实例
                await browser_pool.release_instance(instance_id)
                
        except Exception as e:
            duration = time.time() - start_time
            return UploadResult(
                task_id=task.task_id,
                file_path=task.file_path,
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
    
    async def _wait_for_upload_page_ready(self, page):
        """智能等待上传页面就绪"""
        # 等待导入按钮出现
        try:
            await page.wait_for_selector('button.desktop-import-button-pc', timeout=15000)
            self.logger.debug("检测到导入按钮")
        except:
            raise Exception("导入按钮未找到，页面可能未正确加载")
        
        # 等待页面稳定
        await page.wait_for_timeout(2000)
    
    async def _perform_upload(self, browser_instance, task: UploadTask) -> bool:
        """执行上传操作 - 按照TECHNICAL_SPEC规范"""
        page = browser_instance.page
        
        try:
            # 记录初始文档数量
            initial_doc_count = await self._get_document_count(page)
            
            # 步骤1: 点击导入按钮
            import_btn = await page.wait_for_selector('button.desktop-import-button-pc', timeout=10000)
            if not import_btn:
                raise Exception("未找到导入按钮")
            
            # 设置文件选择器监听
            file_chooser_promise = page.wait_for_event('filechooser', timeout=10000)
            
            await import_btn.click()
            self.logger.debug("已点击导入按钮")
            
            # 步骤2: 处理文件选择
            try:
                file_chooser = await file_chooser_promise
                await file_chooser.set_files(task.file_path)
                self.logger.debug(f"文件已通过选择器设置: {task.file_path}")
                
            except asyncio.TimeoutError:
                self.logger.debug("文件选择器超时，查找input元素...")
                
                # 等待DOM更新
                await page.wait_for_timeout(1000)
                
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(task.file_path)
                    self.logger.debug(f"文件已通过input元素设置: {task.file_path}")
                else:
                    raise Exception("未找到文件输入元素")
            
            # 步骤3: 点击确定按钮
            await self._click_confirm_button(page)
            
            # 步骤4: 智能等待上传完成
            success = await self._wait_for_upload_completion(page, initial_doc_count)
            
            return success
            
        except Exception as e:
            self.logger.error(f"上传过程异常: {e}")
            return False
    
    async def _get_document_count(self, page) -> int:
        """获取当前文档数量"""
        try:
            count = await page.evaluate('''() => {
                return document.querySelectorAll('[class*="doc"], [class*="file"], .document-item').length;
            }''')
            return count
        except:
            return 0
    
    async def _click_confirm_button(self, page):
        """点击确定按钮"""
        # 等待确认对话框出现
        await page.wait_for_timeout(2000)
        
        # 按照SPEC规范的选择器
        confirm_selectors = [
            'div.dui-button-container:has-text("确定")',
            '.dui-button-container:has-text("确定")',
            'button:has-text("确定")',
            '.dui-button:has-text("确定")'
        ]
        
        for selector in confirm_selectors:
            try:
                confirm_btn = await page.query_selector(selector)
                if confirm_btn:
                    await confirm_btn.click()
                    self.logger.debug(f"已点击确定按钮: {selector}")
                    return
            except Exception as e:
                continue
        
        # 备用方案：键盘回车
        self.logger.debug("使用键盘回车确认")
        await page.keyboard.press('Enter')
    
    async def _wait_for_upload_completion(self, page, initial_doc_count: int, timeout: float = 60) -> bool:
        """智能等待上传完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查文档数量变化
                current_count = await self._get_document_count(page)
                if current_count > initial_doc_count:
                    self.logger.debug(f"文档数量增加: {initial_doc_count} -> {current_count}")
                    return True
                
                # 检查上传状态文字
                status = await page.evaluate('''() => {
                    const bodyText = document.body.textContent;
                    return {
                        complete: bodyText.includes('上传完成') || bodyText.includes('导入完成'),
                        error: bodyText.includes('上传失败') || bodyText.includes('导入失败'),
                        uploading: bodyText.includes('上传中') || bodyText.includes('正在上传')
                    };
                }''')
                
                if status['complete']:
                    self.logger.debug("检测到上传完成文字")
                    return True
                elif status['error']:
                    self.logger.warning("检测到上传错误")
                    return False
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.debug(f"上传监控异常: {e}")
                await asyncio.sleep(1)
        
        # 超时后再次检查文档数量
        final_count = await self._get_document_count(page)
        return final_count > initial_doc_count
    
    async def get_result(self, task_id: str, timeout: float = 60) -> Optional[UploadResult]:
        """获取上传结果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.results:
                return self.results[task_id]
            await asyncio.sleep(0.5)
        
        return None
    
    async def get_all_results(self) -> Dict[str, UploadResult]:
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


async def upload_multiple_files(files_and_cookies: List[tuple], homepage_url: str = None):
    """并发上传多个文件"""
    uploader = OptimizedTencentUploader()
    
    # 添加所有任务
    task_ids = []
    for i, (file_path, cookies) in enumerate(files_and_cookies):
        task_id = await uploader.add_upload_task(file_path, cookies, 
                                               homepage_url or "https://docs.qq.com/desktop", 
                                               priority=i)
        task_ids.append(task_id)
    
    # 启动处理
    workers = await uploader.start_processing()
    
    try:
        # 等待所有任务完成
        await uploader.wait_for_completion()
        
        # 获取结果
        results = await uploader.get_all_results()
        stats = await uploader.get_stats()
        
        print(f"上传统计: {stats}")
        
        return results, stats
        
    finally:
        # 清理工作进程
        for worker in workers:
            worker.cancel()
        
        # 清理浏览器池
        await cleanup_browser_pool()


async def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='优化版腾讯文档批量上传工具')
    parser.add_argument('files', nargs='+', help='要上传的文件列表')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--homepage', default='https://docs.qq.com/desktop', help='腾讯文档主页URL')
    parser.add_argument('--max-concurrent', type=int, default=2, help='最大并发数')
    parser.add_argument('--verbose', action='store_true', help='详细日志')
    
    args = parser.parse_args()
    
    # 配置日志
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 检查文件存在
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在 {file_path}")
            return
    
    # 准备上传任务
    files_and_cookies = [(file_path, args.cookies) for file_path in args.files]
    
    print(f"开始批量上传 {len(files_and_cookies)} 个文件...")
    start_time = time.time()
    
    # 执行上传
    results, stats = await upload_multiple_files(files_and_cookies, args.homepage)
    
    total_time = time.time() - start_time
    
    # 显示结果
    print("\n=== 上传结果 ===")
    for task_id, result in results.items():
        if result.success:
            print(f"✅ {task_id}: {result.file_path} ({result.duration:.2f}s)")
        else:
            print(f"❌ {task_id}: {result.file_path} - {result.error}")
    
    print(f"\n=== 总体统计 ===")
    print(f"总时间: {total_time:.2f}s")
    print(f"平均速度: {len(results)/total_time:.2f} 文件/秒")
    print(f"成功率: {stats['success_rate']}")


if __name__ == "__main__":
    asyncio.run(main())