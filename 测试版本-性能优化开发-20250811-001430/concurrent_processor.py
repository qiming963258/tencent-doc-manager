#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档并发处理器 - 支持30+文档同时处理
提供高效的批量下载/上传解决方案
"""

import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """任务类型枚举"""
    DOWNLOAD = "download"
    UPLOAD = "upload"


@dataclass
class BatchTask:
    """批处理任务数据结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.DOWNLOAD
    status: TaskStatus = TaskStatus.PENDING
    url: Optional[str] = None
    file_path: Optional[str] = None
    username: str = ""
    cookies: str = ""
    format: str = "excel"
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """计算任务执行时间"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class BatchJob:
    """批处理作业"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: List[BatchTask] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @property
    def completed_tasks(self) -> int:
        return len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
    
    @property
    def failed_tasks(self) -> int:
        return len([t for t in self.tasks if t.status == TaskStatus.FAILED])
    
    @property
    def running_tasks(self) -> int:
        return len([t for t in self.tasks if t.status == TaskStatus.RUNNING])
    
    @property
    def overall_progress(self) -> float:
        """计算总体进度"""
        if not self.tasks:
            return 0.0
        return sum(t.progress for t in self.tasks) / len(self.tasks)
    
    @property
    def is_completed(self) -> bool:
        """检查是否全部完成"""
        return all(t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for t in self.tasks)


class ConcurrentProcessor:
    """并发处理器 - 优化速度版本"""
    
    def __init__(self, max_workers: int = 30, max_browsers: int = 10):
        """
        初始化并发处理器 - 针对速度优化
        
        Args:
            max_workers: 最大工作线程数 (提高到30)
            max_browsers: 最大浏览器实例数 (提高到10)
        """
        self.max_workers = max_workers
        self.max_browsers = max_browsers
        self.active_jobs: Dict[str, BatchJob] = {}
        self.browser_semaphore = asyncio.Semaphore(max_browsers)
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        
        logger.info(f"并发处理器初始化: 最大工作线程={max_workers}, 最大浏览器={max_browsers}")
    
    def create_download_job(self, name: str, urls: List[str], username: str, 
                          cookies: str, format: str = "excel") -> str:
        """
        创建批量下载作业 - 速度优化
        """
        # 去重URL提高效率
        unique_urls = list(set(urls))
        if len(unique_urls) != len(urls):
            logger.info(f"去重URL: {len(urls)} -> {len(unique_urls)}")
        
        tasks = []
        for url in unique_urls:
            task = BatchTask(
                type=TaskType.DOWNLOAD,
                url=url,
                username=username,
                cookies=cookies,
                format=format
            )
            tasks.append(task)
        
        job = BatchJob(name=name, tasks=tasks)
        
        with self._lock:
            self.active_jobs[job.id] = job
        
        logger.info(f"创建高速下载作业: {name}, 任务数: {len(unique_urls)}, 作业ID: {job.id}")
        return job.id
    
    def create_upload_job(self, name: str, file_paths: List[str], 
                         username: str, cookies: str) -> str:
        """
        创建批量上传作业 - 速度优化
        """
        # 去重文件路径，提高效率
        unique_paths = list(set(file_paths))
        if len(unique_paths) != len(file_paths):
            logger.info(f"去重文件: {len(file_paths)} -> {len(unique_paths)}")
        
        tasks = []
        for file_path in unique_paths:
            task = BatchTask(
                type=TaskType.UPLOAD,
                file_path=file_path,
                username=username,
                cookies=cookies
            )
            tasks.append(task)
        
        job = BatchJob(name=name, tasks=tasks)
        
        with self._lock:
            self.active_jobs[job.id] = job
        
        logger.info(f"创建高速上传作业: {name}, 任务数: {len(unique_paths)}, 作业ID: {job.id}")
        return job.id
    
    async def execute_job(self, job_id: str, progress_callback: Optional[Callable] = None) -> BatchJob:
        """
        执行批处理作业 - 最大并发速度
        """
        with self._lock:
            job = self.active_jobs.get(job_id)
        
        if not job:
            raise ValueError(f"作业不存在: {job_id}")
        
        logger.info(f"开始高速执行作业: {job.name}, 任务数: {job.total_tasks}")
        job.started_at = time.time()
        
        # 移除信号量限制，直接最大并发
        tasks = [self._execute_task(task, progress_callback) for task in job.tasks]
        
        # 使用gather实现真正的并发执行
        await asyncio.gather(*tasks, return_exceptions=True)
        
        job.completed_at = time.time()
        logger.info(f"作业完成: {job.name}, 成功: {job.completed_tasks}, 失败: {job.failed_tasks}, "
                   f"总耗时: {job.completed_at - job.started_at:.1f}秒")
        
        return job
    
    async def _execute_task(self, task: BatchTask, progress_callback: Optional[Callable] = None):
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.progress = 0.1
        
        if progress_callback:
            await self._safe_callback(progress_callback, task)
        
        try:
            if task.type == TaskType.DOWNLOAD:
                await self._execute_download_task(task, progress_callback)
            elif task.type == TaskType.UPLOAD:
                await self._execute_upload_task(task, progress_callback)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            raise
        finally:
            task.completed_at = time.time()
    
    async def _execute_download_task(self, task: BatchTask, progress_callback: Optional[Callable] = None):
        """执行下载任务 - 速度优化版本"""
        # 移除浏览器信号量限制，直接并发
        from tencent_export_automation import TencentDocAutoExporter
        
        exporter = TencentDocAutoExporter()
        
        try:
            task.progress = 0.2
            task.message = "启动浏览器..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            # 更快的浏览器启动
            await exporter.start_browser(headless=True)
            
            task.progress = 0.3
            task.message = "设置登录信息..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            if task.cookies:
                await exporter.login_with_cookies(task.cookies)
            
            task.progress = 0.5
            task.message = "开始下载文档..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            # 减少超时时间，提高速度
            result = await asyncio.wait_for(
                exporter.auto_export_document(task.url, task.format),
                timeout=30  # 从60秒减少到30秒
            )
            
            if result:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                task.message = "下载完成"
                task.result = {
                    "file_path": result[0] if isinstance(result, list) else result,
                    "files": result if isinstance(result, list) else [result]
                }
            else:
                raise Exception("下载失败，未获取到文件")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "下载超时"
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        finally:
            await exporter.cleanup()
            if progress_callback:
                await self._safe_callback(progress_callback, task)
    
    async def _execute_upload_task(self, task: BatchTask, progress_callback: Optional[Callable] = None):
        """执行上传任务 - 速度优化版本"""
        # 移除浏览器信号量限制，直接并发
        from tencent_upload_automation import TencentDocAutoUploader
        
        uploader = TencentDocAutoUploader()
        
        try:
            task.progress = 0.2
            task.message = "启动浏览器..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            # 更快的浏览器启动
            await uploader.start_browser(headless=True)
            
            task.progress = 0.3
            task.message = "设置登录信息..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            if task.cookies:
                await uploader.login_with_cookies(task.cookies)
            
            task.progress = 0.5
            task.message = "开始上传文件..."
            if progress_callback:
                await self._safe_callback(progress_callback, task)
            
            # 减少超时时间，提高速度
            result = await asyncio.wait_for(
                uploader.upload_file_to_main_page(task.file_path),
                timeout=25  # 上传超时时间稍短
            )
            
            if result:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                task.message = "上传完成"
                task.result = {"success": True, "url": result}
            else:
                raise Exception("上传失败")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "上传超时"
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        finally:
            await uploader.cleanup()
            if progress_callback:
                await self._safe_callback(progress_callback, task)
    
    async def _safe_callback(self, callback: Callable, task: BatchTask):
        """安全执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(task)
            else:
                callback(task)
        except Exception as e:
            logger.error(f"回调函数执行失败: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取作业状态"""
        with self._lock:
            job = self.active_jobs.get(job_id)
        
        if not job:
            return None
        
        return {
            "id": job.id,
            "name": job.name,
            "total_tasks": job.total_tasks,
            "completed_tasks": job.completed_tasks,
            "failed_tasks": job.failed_tasks,
            "running_tasks": job.running_tasks,
            "overall_progress": job.overall_progress,
            "is_completed": job.is_completed,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "tasks": [
                {
                    "id": task.id,
                    "status": task.status.value,
                    "progress": task.progress,
                    "message": task.message,
                    "error": task.error,
                    "duration": task.duration
                }
                for task in job.tasks
            ]
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """取消作业"""
        with self._lock:
            job = self.active_jobs.get(job_id)
        
        if not job:
            return False
        
        # 取消所有未开始的任务
        cancelled_count = 0
        for task in job.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                cancelled_count += 1
        
        logger.info(f"取消作业: {job.name}, 取消任务数: {cancelled_count}")
        return True
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """清理完成的作业"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            jobs_to_remove = []
            for job_id, job in self.active_jobs.items():
                if (job.is_completed and 
                    job.completed_at and 
                    current_time - job.completed_at > max_age_seconds):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
        
        if jobs_to_remove:
            logger.info(f"清理完成的作业: {len(jobs_to_remove)}个")
    
    async def shutdown(self):
        """关闭处理器"""
        logger.info("关闭并发处理器...")
        self.thread_executor.shutdown(wait=True)


# 全局处理器实例
_processor_instance: Optional[ConcurrentProcessor] = None


def get_processor() -> ConcurrentProcessor:
    """获取全局处理器实例"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = ConcurrentProcessor()
    return _processor_instance


async def main():
    """测试并发处理器"""
    processor = get_processor()
    
    # 测试批量下载
    urls = [
        "https://docs.qq.com/sheet/DWERJQXFDbFNtRGxq?tab=inoe5c",
        "https://docs.qq.com/sheet/DWERJQXFDbFNtRGxq?tab=bb08j2"
    ]
    
    job_id = processor.create_download_job(
        name="测试批量下载",
        urls=urls,
        username="test_user",
        cookies="",
        format="excel"
    )
    
    print(f"创建作业: {job_id}")
    
    async def progress_callback(task: BatchTask):
        print(f"任务 {task.id[:8]}... 状态: {task.status.value} 进度: {task.progress:.1%} 消息: {task.message}")
    
    try:
        job = await processor.execute_job(job_id, progress_callback)
        print(f"作业完成: 成功 {job.completed_tasks}/{job.total_tasks}")
    except Exception as e:
        print(f"作业执行失败: {e}")
    
    await processor.shutdown()


if __name__ == "__main__":
    asyncio.run(main())