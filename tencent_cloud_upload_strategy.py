# -*- coding: utf-8 -*-
"""
腾讯文档云端集成上传策略
替换本地存储，实现直接上传到腾讯文档的完整解决方案
"""

import asyncio
import aiohttp
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import tempfile
import uuid
import hashlib
from playwright.async_api import async_playwright, Browser, Page
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class UploadTask:
    """上传任务数据结构"""
    task_id: str
    file_path: str
    target_folder: str
    file_name: str
    upload_priority: int = 1  # 1=高优先级, 2=中等, 3=低优先级
    metadata: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UploadResult:
    """上传结果数据结构"""
    task_id: str
    success: bool
    tencent_doc_url: str = ""
    tencent_doc_id: str = ""
    upload_time: str = ""
    file_size_bytes: int = 0
    error_message: str = ""
    retry_count: int = 0
    upload_duration_seconds: float = 0.0


class TencentDocCloudUploadManager:
    """腾讯文档云端上传管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 上传配置
        self.max_concurrent_uploads = self.config.get("max_concurrent_uploads", 3)
        self.upload_timeout_seconds = self.config.get("upload_timeout_seconds", 300)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.retry_delay_seconds = self.config.get("retry_delay_seconds", 5)
        
        # 浏览器配置
        self.headless_mode = self.config.get("headless_mode", True)
        self.browser_pool_size = self.config.get("browser_pool_size", 2)
        
        # 文件管理配置
        self.cleanup_temp_files = self.config.get("cleanup_temp_files", True)
        self.max_file_size_mb = self.config.get("max_file_size_mb", 100)
        
        # 上传状态跟踪
        self.upload_history_db = self.config.get("upload_history_db", "upload_history.db")
        self._init_upload_history_db()
        
        # 浏览器池
        self.browser_pool = []
        self.browser_lock = asyncio.Lock()
        
        # 统计信息
        self.upload_stats = {
            "total_uploads": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_upload_time": 0.0,
            "average_upload_time": 0.0,
            "total_bytes_uploaded": 0
        }
    
    def _init_upload_history_db(self):
        """初始化上传历史数据库"""
        try:
            conn = sqlite3.connect(self.upload_history_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    target_folder TEXT NOT NULL,
                    tencent_doc_url TEXT,
                    tencent_doc_id TEXT,
                    upload_status TEXT NOT NULL,
                    upload_time TIMESTAMP,
                    file_size_bytes INTEGER,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    upload_duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_upload_status 
                ON upload_history(upload_status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_upload_time 
                ON upload_history(upload_time)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("上传历史数据库初始化完成")
            
        except Exception as e:
            logger.error(f"上传历史数据库初始化失败: {e}")
    
    async def initialize_browser_pool(self):
        """初始化浏览器池"""
        logger.info(f"初始化浏览器池，大小: {self.browser_pool_size}")
        
        playwright = await async_playwright().start()
        
        for i in range(self.browser_pool_size):
            try:
                browser = await playwright.chromium.launch(
                    headless=self.headless_mode,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',  # 提高性能
                        '--disable-javascript',  # 部分场景可以禁用
                    ]
                )
                
                self.browser_pool.append(browser)
                logger.info(f"浏览器实例 {i+1} 初始化成功")
                
            except Exception as e:
                logger.error(f"浏览器实例 {i+1} 初始化失败: {e}")
    
    async def upload_files_batch(self, upload_tasks: List[UploadTask], 
                               user_cookies: str) -> Dict[str, Any]:
        """
        批量上传文件到腾讯文档
        
        Args:
            upload_tasks: 上传任务列表
            user_cookies: 用户认证cookies
            
        Returns:
            批量上传结果汇总
        """
        logger.info(f"开始批量上传，任务数量: {len(upload_tasks)}")
        
        start_time = time.time()
        
        # 初始化浏览器池（如果未初始化）
        if not self.browser_pool:
            await self.initialize_browser_pool()
        
        # 按优先级排序
        sorted_tasks = sorted(upload_tasks, key=lambda t: t.upload_priority)
        
        # 分批并发处理
        results = []
        batch_size = min(self.max_concurrent_uploads, len(self.browser_pool))
        
        for i in range(0, len(sorted_tasks), batch_size):
            batch = sorted_tasks[i:i + batch_size]
            batch_results = await self._process_upload_batch(batch, user_cookies)
            results.extend(batch_results)
            
            # 批次间延迟，避免过度负载
            if i + batch_size < len(sorted_tasks):
                await asyncio.sleep(2)
        
        # 生成汇总结果
        summary = self._generate_upload_summary(results, time.time() - start_time)
        
        # 更新统计信息
        self._update_upload_statistics(results)
        
        return summary
    
    async def _process_upload_batch(self, batch: List[UploadTask], 
                                  user_cookies: str) -> List[UploadResult]:
        """处理单个批次的上传任务"""
        batch_results = []
        
        # 创建并发任务
        semaphore = asyncio.Semaphore(len(batch))
        tasks = []
        
        for task in batch:
            upload_task = self._create_upload_coroutine(task, user_cookies, semaphore)
            tasks.append(upload_task)
        
        # 等待所有任务完成
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                # 处理异常情况
                error_result = UploadResult(
                    task_id=batch[i].task_id,
                    success=False,
                    error_message=str(result),
                    upload_time=datetime.now().isoformat()
                )
                batch_results.append(error_result)
            else:
                batch_results.append(result)
        
        return batch_results
    
    async def _create_upload_coroutine(self, task: UploadTask, 
                                     user_cookies: str,
                                     semaphore: asyncio.Semaphore) -> UploadResult:
        """创建单个上传协程"""
        async with semaphore:
            return await self._upload_single_file(task, user_cookies)
    
    async def _upload_single_file(self, task: UploadTask, 
                                user_cookies: str) -> UploadResult:
        """上传单个文件"""
        start_time = time.time()
        browser = None
        
        try:
            logger.info(f"开始上传文件: {task.file_name} (任务ID: {task.task_id})")
            
            # 验证文件
            validation_result = self._validate_upload_file(task)
            if not validation_result["valid"]:
                return UploadResult(
                    task_id=task.task_id,
                    success=False,
                    error_message=validation_result["error"],
                    upload_time=datetime.now().isoformat()
                )
            
            # 获取浏览器实例
            browser = await self._get_browser_from_pool()
            if not browser:
                raise Exception("无法获取可用的浏览器实例")
            
            # 执行上传
            upload_result = await self._perform_upload_with_browser(
                browser, task, user_cookies
            )
            
            # 记录上传历史
            self._record_upload_history(task, upload_result)
            
            upload_result.upload_duration_seconds = time.time() - start_time
            
            logger.info(f"文件上传完成: {task.file_name}, 成功: {upload_result.success}")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"文件上传失败 {task.file_name}: {e}")
            
            error_result = UploadResult(
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                upload_time=datetime.now().isoformat(),
                upload_duration_seconds=time.time() - start_time
            )
            
            # 记录失败历史
            self._record_upload_history(task, error_result)
            
            return error_result
            
        finally:
            # 归还浏览器到池中
            if browser:
                await self._return_browser_to_pool(browser)
    
    async def _get_browser_from_pool(self) -> Optional[Browser]:
        """从浏览器池获取实例"""
        async with self.browser_lock:
            if self.browser_pool:
                return self.browser_pool.pop(0)
            return None
    
    async def _return_browser_to_pool(self, browser: Browser):
        """归还浏览器实例到池中"""
        async with self.browser_lock:
            if browser and not browser.is_connected():
                # 浏览器已断开，重新创建
                try:
                    playwright = await async_playwright().start()
                    new_browser = await playwright.chromium.launch(headless=self.headless_mode)
                    self.browser_pool.append(new_browser)
                except Exception as e:
                    logger.error(f"重新创建浏览器实例失败: {e}")
            else:
                self.browser_pool.append(browser)
    
    def _validate_upload_file(self, task: UploadTask) -> Dict[str, Any]:
        """验证上传文件"""
        file_path = Path(task.file_path)
        
        if not file_path.exists():
            return {"valid": False, "error": f"文件不存在: {task.file_path}"}
        
        if not file_path.is_file():
            return {"valid": False, "error": f"路径不是文件: {task.file_path}"}
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return {"valid": False, "error": f"文件大小超限: {file_size_mb:.2f}MB > {self.max_file_size_mb}MB"}
        
        # 检查文件扩展名
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.docx', '.doc', '.pptx', '.ppt']
        if file_path.suffix.lower() not in allowed_extensions:
            return {"valid": False, "error": f"不支持的文件类型: {file_path.suffix}"}
        
        return {"valid": True, "file_size_bytes": file_path.stat().st_size}
    
    async def _perform_upload_with_browser(self, browser: Browser, 
                                         task: UploadTask,
                                         user_cookies: str) -> UploadResult:
        """使用浏览器执行上传操作"""
        page = None
        
        try:
            # 创建新页面
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # 设置cookies
            await self._set_page_cookies(page, user_cookies)
            
            # 导航到腾讯文档主页
            await page.goto('https://docs.qq.com/', wait_until='networkidle')
            
            # 检查登录状态
            login_check = await self._check_login_status(page)
            if not login_check:
                raise Exception("用户未登录或cookies已过期")
            
            # 导航到目标文件夹
            if task.target_folder and task.target_folder != "根目录":
                await self._navigate_to_folder(page, task.target_folder)
            
            # 执行文件上传
            upload_result = await self._execute_file_upload(page, task)
            
            await context.close()
            
            return upload_result
            
        except Exception as e:
            if page:
                await page.context.close()
            raise e
    
    async def _set_page_cookies(self, page: Page, cookies: str):
        """设置页面cookies"""
        if not cookies:
            return
        
        cookie_list = []
        for cookie_str in cookies.split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                
                # 为腾讯文档相关域名设置cookies
                domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
                for domain in domains:
                    cookie_list.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': '/'
                    })
        
        if cookie_list:
            await page.context.add_cookies(cookie_list)
    
    async def _check_login_status(self, page: Page) -> bool:
        """检查登录状态"""
        try:
            # 等待页面加载完成
            await page.wait_for_timeout(3000)
            
            # 检查是否存在登录相关元素
            login_indicators = [
                'text=登录',
                'text=立即登录',
                '[data-test-id="login-btn"]',
                '.login-btn'
            ]
            
            for indicator in login_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        return False  # 发现登录按钮，说明未登录
                except:
                    continue
            
            # 检查是否存在用户信息（表示已登录）
            user_indicators = [
                '[data-test-id="user-avatar"]',
                '.user-avatar',
                'text=我的文档',
                '[data-test-id="upload-btn"]'
            ]
            
            for indicator in user_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        return True  # 发现用户相关元素，说明已登录
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    async def _navigate_to_folder(self, page: Page, folder_name: str):
        """导航到指定文件夹"""
        try:
            # 点击文件夹或创建新文件夹
            # 这里需要根据腾讯文档的实际界面结构来实现
            logger.info(f"导航到文件夹: {folder_name}")
            
            # 等待文件列表加载
            await page.wait_for_selector('[data-test-id="doc-list"]', timeout=10000)
            
            # 查找目标文件夹
            folder_selector = f'text={folder_name}'
            folder_element = await page.query_selector(folder_selector)
            
            if folder_element:
                # 文件夹存在，点击进入
                await folder_element.click()
                await page.wait_for_load_state('networkidle')
            else:
                # 文件夹不存在，创建新文件夹
                logger.info(f"文件夹 {folder_name} 不存在，将创建新文件夹")
                await self._create_new_folder(page, folder_name)
            
        except Exception as e:
            logger.warning(f"导航到文件夹失败，将使用根目录: {e}")
    
    async def _create_new_folder(self, page: Page, folder_name: str):
        """创建新文件夹"""
        try:
            # 查找创建文件夹按钮
            create_folder_selectors = [
                '[data-test-id="create-folder-btn"]',
                'text=新建文件夹',
                '.create-folder'
            ]
            
            for selector in create_folder_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=3000)
                    if button:
                        await button.click()
                        break
                except:
                    continue
            
            # 输入文件夹名称
            name_input = await page.wait_for_selector('input[placeholder*="文件夹名称"]', timeout=5000)
            if name_input:
                await name_input.fill(folder_name)
                
                # 点击确认按钮
                confirm_button = await page.wait_for_selector('text=确定', timeout=3000)
                if confirm_button:
                    await confirm_button.click()
                    await page.wait_for_load_state('networkidle')
            
        except Exception as e:
            logger.error(f"创建文件夹失败: {e}")
    
    async def _execute_file_upload(self, page: Page, task: UploadTask) -> UploadResult:
        """执行文件上传"""
        try:
            # 查找上传按钮
            upload_selectors = [
                '[data-test-id="upload-btn"]',
                'text=上传',
                '.upload-btn',
                'input[type="file"]'
            ]
            
            upload_element = None
            for selector in upload_selectors:
                try:
                    upload_element = await page.wait_for_selector(selector, timeout=5000)
                    if upload_element:
                        break
                except:
                    continue
            
            if not upload_element:
                raise Exception("找不到上传按钮")
            
            # 设置文件上传
            await upload_element.set_input_files(task.file_path)
            
            # 等待上传完成
            await self._wait_for_upload_completion(page, task.file_name)
            
            # 获取上传后的文档URL和ID
            doc_url, doc_id = await self._get_uploaded_document_info(page, task.file_name)
            
            return UploadResult(
                task_id=task.task_id,
                success=True,
                tencent_doc_url=doc_url,
                tencent_doc_id=doc_id,
                upload_time=datetime.now().isoformat(),
                file_size_bytes=Path(task.file_path).stat().st_size
            )
            
        except Exception as e:
            raise Exception(f"文件上传执行失败: {e}")
    
    async def _wait_for_upload_completion(self, page: Page, file_name: str, timeout: int = 120):
        """等待上传完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查上传进度或完成状态
                progress_selectors = [
                    f'text={file_name}',
                    '[data-test-id="upload-progress"]',
                    '.upload-complete'
                ]
                
                for selector in progress_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            # 检查是否上传完成
                            if 'complete' in await element.get_attribute('class') or '':
                                return True
                    except:
                        continue
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"等待上传完成时出错: {e}")
                await asyncio.sleep(5)
        
        raise Exception(f"上传超时: {timeout}秒")
    
    async def _get_uploaded_document_info(self, page: Page, file_name: str) -> Tuple[str, str]:
        """获取上传后的文档信息"""
        try:
            # 查找文档链接
            doc_selectors = [
                f'a[title*="{file_name}"]',
                f'text={file_name}',
                f'[data-file-name="{file_name}"]'
            ]
            
            for selector in doc_selectors:
                try:
                    doc_element = await page.wait_for_selector(selector, timeout=5000)
                    if doc_element:
                        doc_url = await doc_element.get_attribute('href') or ''
                        
                        # 从URL提取文档ID
                        doc_id = self._extract_doc_id_from_url(doc_url)
                        
                        return doc_url, doc_id
                except:
                    continue
            
            # 如果无法获取具体链接，返回当前页面URL
            return page.url, ""
            
        except Exception as e:
            logger.warning(f"获取文档信息失败: {e}")
            return "", ""
    
    def _extract_doc_id_from_url(self, url: str) -> str:
        """从URL中提取文档ID"""
        try:
            # 腾讯文档URL格式：https://docs.qq.com/sheet/DOCID
            if '/sheet/' in url:
                return url.split('/sheet/')[-1].split('?')[0]
            elif '/doc/' in url:
                return url.split('/doc/')[-1].split('?')[0]
            elif '/slide/' in url:
                return url.split('/slide/')[-1].split('?')[0]
            return ""
        except:
            return ""
    
    def _record_upload_history(self, task: UploadTask, result: UploadResult):
        """记录上传历史"""
        try:
            conn = sqlite3.connect(self.upload_history_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO upload_history 
                (task_id, file_path, file_name, target_folder, tencent_doc_url, 
                 tencent_doc_id, upload_status, upload_time, file_size_bytes, 
                 error_message, retry_count, upload_duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id,
                task.file_path,
                task.file_name,
                task.target_folder,
                result.tencent_doc_url,
                result.tencent_doc_id,
                "SUCCESS" if result.success else "FAILED",
                result.upload_time,
                result.file_size_bytes,
                result.error_message,
                result.retry_count,
                result.upload_duration_seconds
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"记录上传历史失败: {e}")
    
    def _generate_upload_summary(self, results: List[UploadResult], 
                               total_time: float) -> Dict[str, Any]:
        """生成上传汇总结果"""
        successful_uploads = [r for r in results if r.success]
        failed_uploads = [r for r in results if not r.success]
        
        total_bytes = sum(r.file_size_bytes for r in successful_uploads)
        
        return {
            "batch_summary": {
                "total_tasks": len(results),
                "successful_uploads": len(successful_uploads),
                "failed_uploads": len(failed_uploads),
                "success_rate": len(successful_uploads) / len(results) if results else 0,
                "total_processing_time_seconds": total_time,
                "total_bytes_uploaded": total_bytes,
                "average_upload_time": sum(r.upload_duration_seconds for r in successful_uploads) / len(successful_uploads) if successful_uploads else 0
            },
            "upload_results": [asdict(result) for result in results],
            "successful_documents": [
                {
                    "task_id": r.task_id,
                    "tencent_doc_url": r.tencent_doc_url,
                    "tencent_doc_id": r.tencent_doc_id,
                    "upload_time": r.upload_time
                }
                for r in successful_uploads
            ],
            "failed_documents": [
                {
                    "task_id": r.task_id,
                    "error_message": r.error_message,
                    "retry_count": r.retry_count
                }
                for r in failed_uploads
            ],
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _update_upload_statistics(self, results: List[UploadResult]):
        """更新上传统计信息"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        self.upload_stats["total_uploads"] += len(results)
        self.upload_stats["successful_uploads"] += len(successful_results)
        self.upload_stats["failed_uploads"] += len(failed_results)
        
        if successful_results:
            total_time = sum(r.upload_duration_seconds for r in successful_results)
            self.upload_stats["total_upload_time"] += total_time
            self.upload_stats["average_upload_time"] = (
                self.upload_stats["total_upload_time"] / self.upload_stats["successful_uploads"]
            )
            
            self.upload_stats["total_bytes_uploaded"] += sum(
                r.file_size_bytes for r in successful_results
            )
    
    async def cleanup_resources(self):
        """清理资源"""
        try:
            # 关闭所有浏览器实例
            for browser in self.browser_pool:
                try:
                    await browser.close()
                except:
                    pass
            
            self.browser_pool.clear()
            logger.info("浏览器资源清理完成")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """获取上传统计信息"""
        return {
            "statistics": self.upload_stats.copy(),
            "configuration": {
                "max_concurrent_uploads": self.max_concurrent_uploads,
                "upload_timeout_seconds": self.upload_timeout_seconds,
                "retry_attempts": self.retry_attempts,
                "browser_pool_size": self.browser_pool_size,
                "max_file_size_mb": self.max_file_size_mb
            },
            "current_status": {
                "browser_pool_size": len(self.browser_pool),
                "total_uploaded_gb": self.upload_stats["total_bytes_uploaded"] / (1024**3)
            }
        }


class TencentDocUploadOrchestrator:
    """腾讯文档上传编排器 - 集成到主流程"""
    
    def __init__(self, upload_manager: TencentDocCloudUploadManager):
        self.upload_manager = upload_manager
    
    async def upload_analysis_results(self, analysis_results: List[Dict[str, Any]], 
                                    user_cookies: str,
                                    upload_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传分析结果文件到腾讯文档
        
        Args:
            analysis_results: 分析结果列表，每个包含文件路径等信息
            user_cookies: 用户认证cookies
            upload_config: 上传配置
                - target_folder: 目标文件夹名称
                - file_name_pattern: 文件名模式
                - cleanup_local_files: 是否清理本地文件
        
        Returns:
            上传结果汇总
        """
        
        # 准备上传任务
        upload_tasks = []
        
        for i, result in enumerate(analysis_results):
            if result.get("success") and result.get("output_file"):
                
                # 生成目标文件名
                original_name = Path(result["output_file"]).stem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_name = upload_config.get("file_name_pattern", "{original}_{timestamp}").format(
                    original=original_name,
                    timestamp=timestamp,
                    index=i+1
                )
                
                task = UploadTask(
                    task_id=f"upload_{i}_{int(time.time())}",
                    file_path=result["output_file"],
                    target_folder=upload_config.get("target_folder", "分析结果"),
                    file_name=target_name,
                    upload_priority=1,  # 分析结果文件高优先级
                    metadata={
                        "analysis_type": result.get("analysis_type", "unknown"),
                        "original_source": result.get("source_file", ""),
                        "analysis_timestamp": result.get("analysis_timestamp", ""),
                        "modifications_count": result.get("modifications_count", 0)
                    }
                )
                
                upload_tasks.append(task)
        
        if not upload_tasks:
            return {
                "success": False,
                "message": "没有可上传的分析结果文件",
                "upload_results": []
            }
        
        # 执行批量上传
        upload_summary = await self.upload_manager.upload_files_batch(
            upload_tasks, user_cookies
        )
        
        # 清理本地文件（如果配置要求）
        if upload_config.get("cleanup_local_files", True):
            self._cleanup_local_files(upload_tasks)
        
        return {
            "success": upload_summary["batch_summary"]["failed_uploads"] == 0,
            "upload_summary": upload_summary,
            "uploaded_documents": upload_summary["successful_documents"],
            "message": f"成功上传 {upload_summary['batch_summary']['successful_uploads']} 个文件到腾讯文档"
        }
    
    def _cleanup_local_files(self, upload_tasks: List[UploadTask]):
        """清理本地文件"""
        for task in upload_tasks:
            try:
                if os.path.exists(task.file_path):
                    os.remove(task.file_path)
                    logger.info(f"已清理本地文件: {task.file_path}")
            except Exception as e:
                logger.warning(f"清理本地文件失败 {task.file_path}: {e}")