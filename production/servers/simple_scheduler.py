#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化定时任务调度器 - 专用于热力图服务器集成
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
    """简化任务调度器"""
    
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
            
            # 计算下个月的目标日期
            next_run = now.replace(day=target_day, hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
            if next_run <= now:
                # 移动到下个月
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            
            return next_run
        
        else:
            raise ValueError(f"不支持的简化调度表达式: {expression}")
    
    def start(self):
        """启动调度器"""
        if self.running:
            self.logger.warning("调度器已在运行")
            return
        
        self.running = True
        self.logger.info("调度器已启动")
        
        # 这里可以添加具体的调度逻辑
        # 简化版本暂时只标记为运行状态
        
    def stop(self):
        """停止调度器"""
        if not self.running:
            self.logger.warning("调度器未在运行")
            return
        
        self.running = False
        self.logger.info("调度器已停止")
    
    def execute_task(self, task_id: str) -> bool:
        """手动执行任务"""
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        execution_id = f"{task_id}_{int(time.time())}"
        
        execution = TaskExecution(
            task_id=task_id,
            execution_id=execution_id,
            start_time=time.time(),
            status="running"
        )
        
        self.executions[execution_id] = execution
        
        try:
            # 这里应该是实际的任务执行逻辑
            # 简化版本暂时只记录执行状态
            self.logger.info(f"执行任务: {task.name}")
            
            # 模拟任务执行
            time.sleep(1)
            
            execution.end_time = time.time()
            execution.status = "completed"
            execution.results = {"message": "任务执行成功（模拟）"}
            
            return True
            
        except Exception as e:
            execution.end_time = time.time()
            execution.status = "failed"
            execution.error = str(e)
            self.logger.error(f"任务执行失败: {e}")
            return False


if __name__ == "__main__":
    # 测试调度器
    scheduler = TaskScheduler()
    print("简化调度器启动成功")