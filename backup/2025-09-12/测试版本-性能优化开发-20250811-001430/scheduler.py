#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器 - Ubuntu 自动化定时采集系统核心组件
支持 cron 表达式和简化时间格式的任务调度
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import croniter
import pytz
from concurrent.futures import ThreadPoolExecutor
from collector import TencentDocumentCollector
from comparator import DocumentComparator
from storage import CollectionStorage


@dataclass 
class ScheduleConfig:
    """调度配置"""
    type: str  # "cron" | "simple"
    expression: str  # cron表达式或简化格式
    timezone: str = "Asia/Shanghai"


@dataclass
class TaskConfig:
    """任务配置"""
    task_id: str
    name: str
    schedule: ScheduleConfig
    urls: List[str]
    cookies: str
    options: Dict[str, Any]
    notification: Optional[Dict[str, Any]] = None


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # "running" | "completed" | "failed"
    results: Optional[Dict] = None
    error: Optional[str] = None


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, data_dir: str = "./data", max_concurrent: int = 2):
        self.data_dir = Path(data_dir)
        self.tasks_dir = self.data_dir / "tasks"
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        
        # 内部状态
        self.tasks: Dict[str, TaskConfig] = {}
        self.executions: Dict[str, TaskExecution] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        # 创建组件
        self.collector = TencentDocumentCollector(max_concurrent=max_concurrent)
        self.comparator = DocumentComparator()
        self.storage = CollectionStorage(str(self.data_dir))
        
        # 确保目录存在
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已有任务
        self._load_tasks()
    
    def _load_tasks(self):
        """加载任务配置"""
        try:
            for task_file in self.tasks_dir.glob("*.json"):
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                    task_config = self._dict_to_task_config(task_data)
                    self.tasks[task_config.task_id] = task_config
                    self.logger.info(f"已加载任务: {task_config.name}")
        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
    
    def _dict_to_task_config(self, data: Dict) -> TaskConfig:
        """字典转任务配置"""
        schedule_data = data["schedule"]
        schedule = ScheduleConfig(
            type=schedule_data["type"],
            expression=schedule_data["expression"],
            timezone=schedule_data.get("timezone", "Asia/Shanghai")
        )
        
        return TaskConfig(
            task_id=data["task_id"],
            name=data["name"],
            schedule=schedule,
            urls=data["urls"],
            cookies=data["cookies"],
            options=data["options"],
            notification=data.get("notification")
        )
    
    def add_task(self, task_config: TaskConfig) -> bool:
        """添加任务"""
        try:
            # 验证调度表达式
            if not self._validate_schedule(task_config.schedule):
                raise ValueError(f"无效的调度表达式: {task_config.schedule.expression}")
            
            # 保存任务配置
            self.tasks[task_config.task_id] = task_config
            task_file = self.tasks_dir / f"{task_config.task_id}.json"
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(task_config), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已添加任务: {task_config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            if task_id in self.tasks:
                del self.tasks[task_id]
                task_file = self.tasks_dir / f"{task_id}.json"
                if task_file.exists():
                    task_file.unlink()
                self.logger.info(f"已删除任务: {task_id}")
                return True
            else:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            return False
    
    def _validate_schedule(self, schedule: ScheduleConfig) -> bool:
        """验证调度配置"""
        try:
            if schedule.type == "cron":
                # 验证 cron 表达式
                croniter.croniter(schedule.expression)
                return True
            elif schedule.type == "simple":
                # 验证简化格式
                return self._validate_simple_schedule(schedule.expression)
            else:
                return False
        except:
            return False
    
    def _validate_simple_schedule(self, expression: str) -> bool:
        """验证简化调度表达式"""
        try:
            if expression.startswith("daily:"):
                # daily:09:00
                time_part = expression.split(":", 1)[1]
                datetime.strptime(time_part, "%H:%M")
                return True
            elif expression.startswith("hourly:"):
                # hourly:30
                minute_part = expression.split(":", 1)[1]
                minute = int(minute_part)
                return 0 <= minute <= 59
            elif expression.startswith("weekly:"):
                # weekly:monday:09:00
                parts = expression.split(":")
                if len(parts) == 3:
                    weekday, hour, minute = parts[1], parts[2], parts[3]
                    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    return weekday.lower() in weekdays
                return False
            elif expression.startswith("monthly:"):
                # monthly:1:09:00
                parts = expression.split(":")
                if len(parts) == 3:
                    day, hour, minute = parts[1], parts[2], parts[3]
                    return 1 <= int(day) <= 31
                return False
            else:
                return False
        except:
            return False
    
    def _get_next_run_time(self, schedule: ScheduleConfig) -> datetime:
        """获取下次执行时间"""
        tz = pytz.timezone(schedule.timezone)
        now = datetime.now(tz)
        
        if schedule.type == "cron":
            cron = croniter.croniter(schedule.expression, now)
            return cron.get_next(datetime)
        elif schedule.type == "simple":
            return self._get_next_simple_time(schedule.expression, now)
        else:
            raise ValueError(f"不支持的调度类型: {schedule.type}")
    
    def _get_next_simple_time(self, expression: str, now: datetime) -> datetime:
        """获取简化格式的下次执行时间"""
        if expression.startswith("daily:"):
            # daily:09:00
            time_str = expression.split(":", 1)[1]
            target_time = datetime.strptime(time_str, "%H:%M").time()
            next_run = now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
            
        elif expression.startswith("hourly:"):
            # hourly:30
            minute = int(expression.split(":", 1)[1])
            next_run = now.replace(minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
            return next_run
            
        elif expression.startswith("weekly:"):
            # weekly:monday:09:00
            parts = expression.split(":")
            weekday_name = parts[1].lower()
            target_time = datetime.strptime(f"{parts[2]}:{parts[3]}", "%H:%M").time()
            
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            target_weekday = weekdays.index(weekday_name)
            
            days_ahead = target_weekday - now.weekday()
            if days_ahead <= 0:  # 目标日期已过或是今天
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
            return next_run
            
        elif expression.startswith("monthly:"):
            # monthly:1:09:00
            parts = expression.split(":")
            target_day = int(parts[1])
            target_time = datetime.strptime(f"{parts[2]}:{parts[3]}", "%H:%M").time()
            
            next_run = now.replace(day=target_day, hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
            if next_run <= now:
                # 下个月
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
            return next_run
        
        else:
            raise ValueError(f"不支持的简化调度格式: {expression}")
    
    async def start(self):
        """启动调度器"""
        if self.running:
            return
            
        self.running = True
        self.logger.info("定时任务调度器已启动")
        
        while self.running:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"调度器循环异常: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        self.executor.shutdown(wait=True)
        await self.collector.cleanup()
        self.logger.info("定时任务调度器已停止")
    
    async def _check_and_execute_tasks(self):
        """检查并执行到期任务"""
        now = datetime.now()
        
        for task_id, task_config in self.tasks.items():
            try:
                next_run = self._get_next_run_time(task_config.schedule)
                
                # 检查是否需要执行（允许1分钟误差）
                if now >= next_run - timedelta(minutes=1) and now <= next_run + timedelta(minutes=1):
                    # 避免重复执行
                    if not self._is_task_running(task_id):
                        await self._execute_task(task_config)
                        
            except Exception as e:
                self.logger.error(f"检查任务 {task_id} 时异常: {e}")
    
    def _is_task_running(self, task_id: str) -> bool:
        """检查任务是否正在运行"""
        for execution in self.executions.values():
            if execution.task_id == task_id and execution.status == "running":
                return True
        return False
    
    async def _execute_task(self, task_config: TaskConfig):
        """执行任务"""
        execution_id = f"{task_config.task_id}_{int(time.time())}"
        execution = TaskExecution(
            task_id=task_config.task_id,
            execution_id=execution_id,
            start_time=time.time(),
            status="running"
        )
        
        self.executions[execution_id] = execution
        self.logger.info(f"开始执行任务: {task_config.name}")
        
        try:
            # 执行采集
            collection_results = await self.collector.collect_documents(
                task_config.urls,
                task_config.cookies,
                concurrent_limit=task_config.options.get("concurrent_limit", 2),
                timeout=task_config.options.get("timeout", 60)
            )
            
            # 保存采集结果
            collection_id = await self.storage.save_collection(
                task_config.task_id,
                collection_results
            )
            
            # 对比历史数据
            comparison_results = None
            if task_config.options.get("compare_with_previous", True):
                comparison_results = await self._compare_with_previous(
                    task_config.task_id,
                    collection_id,
                    collection_results
                )
            
            # 更新执行状态
            execution.end_time = time.time()
            execution.status = "completed"
            execution.results = {
                "collection_id": collection_id,
                "collection_results": collection_results,
                "comparison_results": comparison_results
            }
            
            self.logger.info(f"任务执行完成: {task_config.name}")
            
            # 发送通知
            if task_config.notification and task_config.notification.get("enabled", False):
                await self._send_notification(task_config, execution)
                
        except Exception as e:
            execution.end_time = time.time()
            execution.status = "failed"
            execution.error = str(e)
            self.logger.error(f"任务执行失败: {task_config.name} - {e}")
    
    async def _compare_with_previous(self, task_id: str, current_collection_id: str, current_results: Dict) -> Dict:
        """与历史数据对比"""
        try:
            # 获取最近的采集记录
            previous_collection = await self.storage.get_latest_collection(task_id, exclude_id=current_collection_id)
            
            if not previous_collection:
                return {"message": "没有历史数据可对比"}
            
            # 执行对比
            comparison_results = {}
            for url, current_data in current_results.items():
                if url in previous_collection.get("results", {}):
                    previous_data = previous_collection["results"][url]
                    if current_data.get("success") and previous_data.get("success"):
                        doc_comparison = await self.comparator.compare_documents(
                            previous_data["data_path"],
                            current_data["data_path"]
                        )
                        comparison_results[url] = doc_comparison
            
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"数据对比失败: {e}")
            return {"error": str(e)}
    
    async def _send_notification(self, task_config: TaskConfig, execution: TaskExecution):
        """发送通知"""
        try:
            notification_config = task_config.notification
            
            # 检查是否需要通知
            should_notify = False
            if execution.status == "failed" and notification_config.get("notify_on_error", False):
                should_notify = True
            elif execution.status == "completed":
                # 检查是否有变化
                if notification_config.get("notify_on_change", False):
                    comparison = execution.results.get("comparison_results", {})
                    has_changes = any(
                        comp.get("changes", {}).get("summary", {}).get("total_changes", 0) > 0 
                        for comp in comparison.values() 
                        if isinstance(comp, dict)
                    )
                    if has_changes:
                        should_notify = True
            
            if should_notify:
                # 这里可以实现 webhook 通知逻辑
                webhook_url = notification_config.get("webhook_url")
                if webhook_url:
                    # 发送 HTTP POST 请求到 webhook
                    self.logger.info(f"应该向 {webhook_url} 发送通知（未实现）")
                    
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
    
    def get_task_list(self) -> List[Dict]:
        """获取任务列表"""
        return [asdict(task) for task in self.tasks.values()]
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        if task_id not in self.tasks:
            return {"error": "任务不存在"}
        
        task_config = self.tasks[task_id]
        
        # 获取最近的执行记录
        recent_executions = [
            asdict(exec) for exec in self.executions.values()
            if exec.task_id == task_id
        ]
        recent_executions.sort(key=lambda x: x["start_time"], reverse=True)
        
        # 计算下次执行时间
        try:
            next_run = self._get_next_run_time(task_config.schedule)
            next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
        except:
            next_run_str = "计算失败"
        
        return {
            "task_config": asdict(task_config),
            "next_run_time": next_run_str,
            "recent_executions": recent_executions[:10],  # 最近10次
            "is_running": self._is_task_running(task_id)
        }


async def main():
    """测试调度器"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建调度器
    scheduler = TaskScheduler("./data/collections")
    
    # 添加测试任务
    test_task = TaskConfig(
        task_id="test_task",
        name="测试任务",
        schedule=ScheduleConfig(
            type="simple",
            expression="daily:09:00",
            timezone="Asia/Shanghai"
        ),
        urls=[
            "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2"
        ],
        cookies="your_cookies_here",
        options={
            "concurrent_limit": 1,
            "timeout": 60,
            "compare_with_previous": True,
            "keep_history_days": 7
        },
        notification={
            "enabled": True,
            "notify_on_change": True,
            "notify_on_error": True
        }
    )
    
    scheduler.add_task(test_task)
    
    try:
        print("调度器启动中...")
        print("按 Ctrl+C 停止")
        
        # 启动调度器
        await scheduler.start()
        
    except KeyboardInterrupt:
        print("正在停止调度器...")
        await scheduler.stop()
        print("调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())