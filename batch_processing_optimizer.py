# -*- coding: utf-8 -*-
"""
30表格批处理优化系统
大规模异构表格的并行处理和智能任务调度
"""

import asyncio
import concurrent.futures
import multiprocessing
from multiprocessing import Pool, Process, Queue, Manager
import queue
import time
import json
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import hashlib
import pickle
import threading
from collections import defaultdict, deque
import heapq
import os
import signal
import traceback

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessingTask:
    """批处理任务数据结构"""
    task_id: str
    file_path: str
    file_name: str
    file_size_bytes: int
    processing_priority: int = 1  # 1=高, 2=中, 3=低
    estimated_processing_time: float = 0.0  # 秒
    dependencies: List[str] = None  # 依赖的其他任务ID
    processing_options: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.dependencies is None:
            self.dependencies = []
        if self.processing_options is None:
            self.processing_options = {}


@dataclass
class BatchProcessingResult:
    """批处理结果数据结构"""
    task_id: str
    success: bool
    start_time: str
    end_time: str
    processing_duration: float
    worker_id: str
    result_data: Dict[str, Any] = None
    error_message: str = ""
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def __post_init__(self):
        if self.result_data is None:
            self.result_data = {}


@dataclass
class SystemResourceSnapshot:
    """系统资源快照"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    active_processes: int
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class IntelligentTaskScheduler:
    """智能任务调度器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 8)
        
        # 任务队列和状态管理
        self.task_queue = []  # 优先级队列
        self.pending_tasks = {}  # task_id -> task
        self.running_tasks = {}  # task_id -> (worker_id, start_time)
        self.completed_tasks = {}  # task_id -> result
        self.failed_tasks = {}  # task_id -> error_info
        
        # 依赖关系管理
        self.dependency_graph = defaultdict(set)  # task_id -> {dependent_task_ids}
        self.reverse_dependencies = defaultdict(set)  # task_id -> {prerequisite_task_ids}
        
        # 资源监控
        self.resource_monitor = SystemResourceMonitor()
        self.performance_predictor = ProcessingTimePredictor()
        
        # 调度策略配置
        self.scheduling_strategy = "intelligent"  # intelligent, priority, round_robin
        self.load_balancing_enabled = True
        self.dynamic_worker_scaling = True
        
        # 统计信息
        self.scheduling_stats = {
            "total_tasks_scheduled": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_processing_time": 0.0,
            "peak_concurrent_tasks": 0,
            "total_processing_time": 0.0
        }
    
    def add_task(self, task: BatchProcessingTask) -> str:
        """添加任务到调度队列"""
        # 估算处理时间
        if task.estimated_processing_time == 0.0:
            task.estimated_processing_time = self.performance_predictor.predict_processing_time(
                task.file_size_bytes, task.processing_options
            )
        
        # 添加到任务队列
        priority_score = self._calculate_task_priority(task)
        heapq.heappush(self.task_queue, (priority_score, task.created_at, task))
        
        # 更新依赖关系
        self._update_dependency_graph(task)
        
        # 存储任务
        self.pending_tasks[task.task_id] = task
        
        logger.info(f"任务添加到调度队列: {task.task_id}, 优先级: {priority_score}")
        
        return task.task_id
    
    def get_next_task(self, worker_capabilities: Dict[str, Any] = None) -> Optional[BatchProcessingTask]:
        """获取下一个可执行的任务"""
        while self.task_queue:
            priority_score, created_at, task = heapq.heappop(self.task_queue)
            
            # 检查任务是否仍然挂起
            if task.task_id not in self.pending_tasks:
                continue
            
            # 检查依赖关系
            if not self._are_dependencies_satisfied(task):
                # 依赖未满足，重新入队
                heapq.heappush(self.task_queue, (priority_score + 1, created_at, task))
                continue
            
            # 检查资源可用性
            if not self._check_resource_availability(task):
                # 资源不足，重新入队
                heapq.heappush(self.task_queue, (priority_score + 0.1, created_at, task))
                continue
            
            # 检查工作节点能力匹配
            if worker_capabilities and not self._check_worker_compatibility(task, worker_capabilities):
                continue
            
            # 移除任务并返回
            del self.pending_tasks[task.task_id]
            return task
        
        return None
    
    def mark_task_started(self, task_id: str, worker_id: str):
        """标记任务开始执行"""
        self.running_tasks[task_id] = (worker_id, datetime.now().isoformat())
        self.scheduling_stats["total_tasks_scheduled"] += 1
        
        # 更新峰值并发任务数
        current_concurrent = len(self.running_tasks)
        if current_concurrent > self.scheduling_stats["peak_concurrent_tasks"]:
            self.scheduling_stats["peak_concurrent_tasks"] = current_concurrent
    
    def mark_task_completed(self, task_id: str, result: BatchProcessingResult):
        """标记任务完成"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        self.completed_tasks[task_id] = result
        
        if result.success:
            self.scheduling_stats["tasks_completed"] += 1
        else:
            self.scheduling_stats["tasks_failed"] += 1
            self.failed_tasks[task_id] = result.error_message
        
        # 更新统计信息
        self.scheduling_stats["total_processing_time"] += result.processing_duration
        self.scheduling_stats["average_processing_time"] = (
            self.scheduling_stats["total_processing_time"] / 
            max(1, self.scheduling_stats["tasks_completed"])
        )
        
        # 检查并释放依赖此任务的其他任务
        self._release_dependent_tasks(task_id)
    
    def _calculate_task_priority(self, task: BatchProcessingTask) -> float:
        """计算任务优先级得分（数值越小优先级越高）"""
        base_priority = task.processing_priority
        
        # 文件大小因子（大文件优先处理，避免阻塞）
        size_factor = task.file_size_bytes / (1024 * 1024)  # MB
        size_score = min(size_factor / 100, 1.0)  # 最大1.0
        
        # 估算时间因子
        time_factor = min(task.estimated_processing_time / 300, 1.0)  # 5分钟为基准
        
        # 依赖关系因子（被依赖越多，优先级越高）
        dependency_factor = len(self.dependency_graph.get(task.task_id, set())) * 0.1
        
        # 综合得分
        priority_score = base_priority - size_score - time_factor - dependency_factor
        
        return priority_score
    
    def _update_dependency_graph(self, task: BatchProcessingTask):
        """更新依赖关系图"""
        for dep_task_id in task.dependencies:
            self.dependency_graph[dep_task_id].add(task.task_id)
            self.reverse_dependencies[task.task_id].add(dep_task_id)
    
    def _are_dependencies_satisfied(self, task: BatchProcessingTask) -> bool:
        """检查任务的依赖关系是否已满足"""
        for dep_task_id in task.dependencies:
            if dep_task_id not in self.completed_tasks:
                return False
            
            # 检查依赖任务是否成功完成
            dep_result = self.completed_tasks[dep_task_id]
            if not dep_result.success:
                return False
        
        return True
    
    def _check_resource_availability(self, task: BatchProcessingTask) -> bool:
        """检查系统资源是否足够执行任务"""
        if not self.load_balancing_enabled:
            return True
        
        current_resource = self.resource_monitor.get_current_snapshot()
        
        # CPU使用率检查
        if current_resource.cpu_percent > 90:
            return False
        
        # 内存使用率检查
        if current_resource.memory_percent > 85:
            return False
        
        # 估算任务所需内存（基于文件大小的简单估算）
        estimated_memory_mb = task.file_size_bytes / (1024 * 1024) * 2  # 2倍文件大小
        if estimated_memory_mb > current_resource.memory_available_gb * 1024 * 0.3:  # 不超过可用内存的30%
            return False
        
        return True
    
    def _check_worker_compatibility(self, task: BatchProcessingTask, 
                                  worker_capabilities: Dict[str, Any]) -> bool:
        """检查工作节点能力是否匹配任务需求"""
        # 检查处理选项中是否有特殊要求
        task_options = task.processing_options
        
        # AI分析需求检查
        if task_options.get("enable_ai_analysis") and not worker_capabilities.get("ai_capable"):
            return False
        
        # 可视化需求检查
        if task_options.get("enable_visualization") and not worker_capabilities.get("visualization_capable"):
            return False
        
        return True
    
    def _release_dependent_tasks(self, completed_task_id: str):
        """释放依赖已完成任务的其他任务"""
        dependent_tasks = self.dependency_graph.get(completed_task_id, set())
        
        for dependent_task_id in dependent_tasks:
            # 检查该任务的所有依赖是否都已完成
            if dependent_task_id in self.pending_tasks:
                task = self.pending_tasks[dependent_task_id]
                if self._are_dependencies_satisfied(task):
                    logger.info(f"任务 {dependent_task_id} 的依赖已满足，可以执行")


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.resource_history = deque(maxlen=100)  # 保留最近100个采样点
        self.monitoring_active = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始资源监控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("系统资源监控已启动")
    
    def stop_monitoring(self):
        """停止资源监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                snapshot = self._collect_resource_snapshot()
                self.resource_history.append(snapshot)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"资源监控出错: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_resource_snapshot(self) -> SystemResourceSnapshot:
        """收集系统资源快照"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # 活跃进程数
        active_processes = len(psutil.pids())
        
        return SystemResourceSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            active_processes=active_processes
        )
    
    def get_current_snapshot(self) -> SystemResourceSnapshot:
        """获取当前资源快照"""
        return self._collect_resource_snapshot()
    
    def get_resource_trend(self, lookback_minutes: int = 5) -> Dict[str, Any]:
        """获取资源使用趋势"""
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        
        recent_snapshots = [
            snapshot for snapshot in self.resource_history
            if datetime.fromisoformat(snapshot.timestamp) > cutoff_time
        ]
        
        if not recent_snapshots:
            return {"message": "无足够历史数据"}
        
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        memory_values = [s.memory_percent for s in recent_snapshots]
        
        return {
            "cpu_trend": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory_trend": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "current": memory_values[-1] if memory_values else 0
            },
            "sample_count": len(recent_snapshots),
            "time_range_minutes": lookback_minutes
        }


class ProcessingTimePredictor:
    """处理时间预测器"""
    
    def __init__(self):
        self.historical_data = []  # (file_size, options_hash, actual_time)
        self.base_processing_rates = {
            "csv_parsing": 50.0,  # MB/s
            "adaptive_comparison": 20.0,  # MB/s
            "ai_analysis": 5.0,  # items/s
            "visualization": 30.0  # MB/s
        }
    
    def predict_processing_time(self, file_size_bytes: int, 
                              processing_options: Dict[str, Any]) -> float:
        """预测处理时间（秒）"""
        
        file_size_mb = file_size_bytes / (1024 * 1024)
        total_time = 0.0
        
        # 基础CSV解析时间
        total_time += file_size_mb / self.base_processing_rates["csv_parsing"]
        
        # 自适应对比时间
        total_time += file_size_mb / self.base_processing_rates["adaptive_comparison"]
        
        # AI分析时间（如果启用）
        if processing_options.get("enable_ai_analysis"):
            # 估算可能的L2修改数量
            estimated_modifications = min(file_size_mb * 2, 50)  # 最多50个修改
            total_time += estimated_modifications / self.base_processing_rates["ai_analysis"]
        
        # 可视化时间（如果启用）
        if processing_options.get("enable_visualization"):
            total_time += file_size_mb / self.base_processing_rates["visualization"]
        
        # 网络上传时间（如果启用）
        if processing_options.get("upload_to_tencent"):
            # 假设网络速度为5MB/s
            total_time += file_size_mb / 5.0
        
        # 添加基础开销时间
        total_time += 10.0  # 10秒基础开销
        
        # 根据历史数据调整（如果有）
        if self.historical_data:
            adjustment_factor = self._calculate_adjustment_factor(file_size_bytes, processing_options)
            total_time *= adjustment_factor
        
        return max(total_time, 5.0)  # 最少5秒
    
    def record_actual_time(self, file_size_bytes: int, 
                          processing_options: Dict[str, Any],
                          actual_time: float):
        """记录实际处理时间，用于改进预测"""
        options_hash = hashlib.md5(
            json.dumps(processing_options, sort_keys=True).encode()
        ).hexdigest()
        
        self.historical_data.append((file_size_bytes, options_hash, actual_time))
        
        # 保留最近1000条记录
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]
    
    def _calculate_adjustment_factor(self, file_size_bytes: int, 
                                   processing_options: Dict[str, Any]) -> float:
        """基于历史数据计算调整因子"""
        options_hash = hashlib.md5(
            json.dumps(processing_options, sort_keys=True).encode()
        ).hexdigest()
        
        # 查找相似的历史记录
        similar_records = [
            (size, actual_time) for size, opt_hash, actual_time in self.historical_data
            if opt_hash == options_hash and abs(size - file_size_bytes) < file_size_bytes * 0.5
        ]
        
        if len(similar_records) < 3:
            return 1.0  # 数据不足，不调整
        
        # 计算实际时间与预测时间的比率
        ratios = []
        for size, actual_time in similar_records:
            predicted_time = self.predict_processing_time(size, processing_options)
            ratios.append(actual_time / predicted_time)
        
        # 返回中位数作为调整因子
        ratios.sort()
        return ratios[len(ratios) // 2]


class BatchProcessingCoordinator:
    """批处理协调器 - 总控制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 核心组件
        self.task_scheduler = IntelligentTaskScheduler(
            max_workers=self.config.get("max_workers", min(multiprocessing.cpu_count(), 8))
        )
        self.resource_monitor = SystemResourceMonitor()
        
        # 工作节点池
        self.worker_pool = []
        self.worker_capabilities = {}
        self.worker_status = {}  # worker_id -> {"status": "idle/busy", "current_task": task_id}
        
        # 批处理状态
        self.batch_id = None
        self.batch_start_time = None
        self.batch_status = "idle"  # idle, running, completed, failed
        
        # 结果收集
        self.batch_results = {}
        self.processing_statistics = {}
    
    async def process_files_batch(self, file_paths: List[str], 
                                processing_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理文件批次的主要方法
        
        Args:
            file_paths: 文件路径列表
            processing_options: 处理选项配置
            
        Returns:
            批处理结果汇总
        """
        
        # 生成批次ID
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.batch_start_time = datetime.now()
        self.batch_status = "running"
        
        logger.info(f"开始批处理，批次ID: {self.batch_id}, 文件数量: {len(file_paths)}")
        
        try:
            # 启动资源监控
            self.resource_monitor.start_monitoring()
            
            # 创建任务列表
            tasks = self._create_processing_tasks(file_paths, processing_options)
            
            # 添加任务到调度器
            for task in tasks:
                self.task_scheduler.add_task(task)
            
            # 启动工作节点池
            await self._initialize_worker_pool()
            
            # 执行批处理
            batch_results = await self._execute_batch_processing(tasks)
            
            # 生成处理统计
            self.processing_statistics = self._generate_processing_statistics(batch_results)
            
            self.batch_status = "completed"
            
            logger.info(f"批处理完成，批次ID: {self.batch_id}")
            
            return {
                "batch_id": self.batch_id,
                "success": True,
                "total_files": len(file_paths),
                "successful_files": sum(1 for r in batch_results.values() if r.success),
                "failed_files": sum(1 for r in batch_results.values() if not r.success),
                "total_processing_time": (datetime.now() - self.batch_start_time).total_seconds(),
                "results": {task_id: asdict(result) for task_id, result in batch_results.items()},
                "statistics": self.processing_statistics,
                "resource_usage": self.resource_monitor.get_resource_trend(
                    lookback_minutes=int((datetime.now() - self.batch_start_time).total_seconds() / 60) + 1
                )
            }
            
        except Exception as e:
            self.batch_status = "failed"
            logger.error(f"批处理失败，批次ID: {self.batch_id}, 错误: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "batch_id": self.batch_id,
                "success": False,
                "error": str(e),
                "partial_results": {task_id: asdict(result) for task_id, result in self.batch_results.items()}
            }
            
        finally:
            # 清理资源
            await self._cleanup_resources()
    
    def _create_processing_tasks(self, file_paths: List[str], 
                               processing_options: Dict[str, Any]) -> List[BatchProcessingTask]:
        """创建处理任务列表"""
        tasks = []
        
        for i, file_path in enumerate(file_paths):
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                logger.warning(f"文件不存在，跳过: {file_path}")
                continue
            
            # 计算文件大小和优先级
            file_size = file_path_obj.stat().st_size
            priority = self._calculate_file_priority(file_path_obj, file_size)
            
            task = BatchProcessingTask(
                task_id=f"{self.batch_id}_task_{i}",
                file_path=str(file_path),
                file_name=file_path_obj.name,
                file_size_bytes=file_size,
                processing_priority=priority,
                processing_options=processing_options.copy()
            )
            
            tasks.append(task)
        
        return tasks
    
    def _calculate_file_priority(self, file_path: Path, file_size: int) -> int:
        """计算文件处理优先级"""
        # 基于文件大小的优先级
        if file_size > 50 * 1024 * 1024:  # >50MB
            return 1  # 高优先级（先处理大文件避免阻塞）
        elif file_size > 10 * 1024 * 1024:  # >10MB
            return 2  # 中优先级
        else:
            return 3  # 低优先级
    
    async def _initialize_worker_pool(self):
        """初始化工作节点池"""
        max_workers = self.task_scheduler.max_workers
        
        logger.info(f"初始化工作节点池，节点数量: {max_workers}")
        
        # 这里可以扩展为分布式工作节点
        for i in range(max_workers):
            worker_id = f"worker_{i}"
            capabilities = {
                "ai_capable": True,  # 假设所有节点都支持AI
                "visualization_capable": True,
                "max_memory_mb": 4096,
                "max_file_size_mb": 500
            }
            
            self.worker_capabilities[worker_id] = capabilities
            self.worker_status[worker_id] = {"status": "idle", "current_task": None}
    
    async def _execute_batch_processing(self, tasks: List[BatchProcessingTask]) -> Dict[str, BatchProcessingResult]:
        """执行批处理"""
        results = {}
        
        # 创建工作协程
        worker_coroutines = []
        for worker_id in self.worker_capabilities:
            coroutine = self._worker_loop(worker_id)
            worker_coroutines.append(coroutine)
        
        # 等待所有任务完成
        try:
            await asyncio.gather(*worker_coroutines)
        except Exception as e:
            logger.error(f"工作节点执行出错: {e}")
        
        # 收集结果
        results.update(self.task_scheduler.completed_tasks)
        results.update({task_id: BatchProcessingResult(
            task_id=task_id,
            success=False,
            start_time="",
            end_time="",
            processing_duration=0.0,
            worker_id="",
            error_message=error_msg
        ) for task_id, error_msg in self.task_scheduler.failed_tasks.items()})
        
        return results
    
    async def _worker_loop(self, worker_id: str):
        """工作节点主循环"""
        while True:
            # 获取下一个任务
            task = self.task_scheduler.get_next_task(self.worker_capabilities[worker_id])
            
            if task is None:
                # 没有可用任务，检查是否还有未完成的任务
                if (len(self.task_scheduler.pending_tasks) == 0 and 
                    len(self.task_scheduler.running_tasks) == 0):
                    break  # 所有任务完成，退出
                
                # 等待一段时间后重试
                await asyncio.sleep(1)
                continue
            
            # 执行任务
            await self._execute_single_task(worker_id, task)
    
    async def _execute_single_task(self, worker_id: str, task: BatchProcessingTask):
        """执行单个任务"""
        start_time = datetime.now()
        
        # 更新工作节点状态
        self.worker_status[worker_id] = {"status": "busy", "current_task": task.task_id}
        self.task_scheduler.mark_task_started(task.task_id, worker_id)
        
        logger.info(f"工作节点 {worker_id} 开始处理任务 {task.task_id}")
        
        try:
            # 这里调用实际的文档处理逻辑
            # 需要导入之前编写的集成处理器
            from integrated_api_server import IntegratedDocumentProcessor
            
            processor = IntegratedDocumentProcessor(self.config)
            
            # 执行处理
            processing_result = await processor.process_document_batch(
                [task.file_path], 
                task.processing_options
            )
            
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            # 创建结果对象
            result = BatchProcessingResult(
                task_id=task.task_id,
                success=processing_result.get("successful_files", 0) > 0,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                processing_duration=processing_duration,
                worker_id=worker_id,
                result_data=processing_result
            )
            
            # 记录处理时间用于改进预测
            self.task_scheduler.performance_predictor.record_actual_time(
                task.file_size_bytes, 
                task.processing_options, 
                processing_duration
            )
            
            self.task_scheduler.mark_task_completed(task.task_id, result)
            
            logger.info(f"任务 {task.task_id} 处理完成，耗时: {processing_duration:.2f}秒")
            
        except Exception as e:
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            error_result = BatchProcessingResult(
                task_id=task.task_id,
                success=False,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                processing_duration=processing_duration,
                worker_id=worker_id,
                error_message=str(e)
            )
            
            self.task_scheduler.mark_task_completed(task.task_id, error_result)
            
            logger.error(f"任务 {task.task_id} 处理失败: {e}")
        
        finally:
            # 重置工作节点状态
            self.worker_status[worker_id] = {"status": "idle", "current_task": None}
    
    def _generate_processing_statistics(self, results: Dict[str, BatchProcessingResult]) -> Dict[str, Any]:
        """生成处理统计信息"""
        successful_results = [r for r in results.values() if r.success]
        failed_results = [r for r in results.values() if not r.success]
        
        if successful_results:
            processing_times = [r.processing_duration for r in successful_results]
            avg_processing_time = sum(processing_times) / len(processing_times)
            total_processing_time = sum(processing_times)
        else:
            avg_processing_time = 0.0
            total_processing_time = 0.0
        
        return {
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "average_processing_time": avg_processing_time,
            "total_processing_time": total_processing_time,
            "scheduler_stats": self.task_scheduler.scheduling_stats,
            "resource_efficiency": self._calculate_resource_efficiency()
        }
    
    def _calculate_resource_efficiency(self) -> Dict[str, float]:
        """计算资源使用效率"""
        resource_trend = self.resource_monitor.get_resource_trend()
        
        return {
            "cpu_efficiency": resource_trend.get("cpu_trend", {}).get("average", 0) / 100,
            "memory_efficiency": resource_trend.get("memory_trend", {}).get("average", 0) / 100,
            "worker_utilization": (
                self.task_scheduler.scheduling_stats["peak_concurrent_tasks"] / 
                max(1, self.task_scheduler.max_workers)
            )
        }
    
    async def _cleanup_resources(self):
        """清理资源"""
        try:
            # 停止资源监控
            self.resource_monitor.stop_monitoring()
            
            logger.info("批处理资源清理完成")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
    
    def get_batch_status(self) -> Dict[str, Any]:
        """获取批处理状态"""
        return {
            "batch_id": self.batch_id,
            "status": self.batch_status,
            "start_time": self.batch_start_time.isoformat() if self.batch_start_time else None,
            "running_time": (datetime.now() - self.batch_start_time).total_seconds() if self.batch_start_time else 0,
            "pending_tasks": len(self.task_scheduler.pending_tasks),
            "running_tasks": len(self.task_scheduler.running_tasks),
            "completed_tasks": len(self.task_scheduler.completed_tasks),
            "failed_tasks": len(self.task_scheduler.failed_tasks),
            "worker_status": self.worker_status,
            "current_resource_usage": self.resource_monitor.get_current_snapshot()
        }