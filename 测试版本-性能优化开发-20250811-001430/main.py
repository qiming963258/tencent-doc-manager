#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ubuntu 自动化定时采集系统主脚本
支持配置管理、任务调度、数据采集和差异对比的完整解决方案
"""

import asyncio
import argparse
import logging
import json
import signal
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from scheduler import TaskScheduler, TaskConfig, ScheduleConfig
from collector import CollectionManager
from comparator import BatchComparator
from storage import CollectionStorage


class CollectionSystemManager:
    """采集系统管理器"""
    
    def __init__(self, config_file: str = "./config/system.json", data_dir: str = "./data"):
        self.config_file = Path(config_file)
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # 创建目录
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.scheduler = None
        self.collection_manager = None
        self.comparator = None
        self.storage = None
        
        # 系统状态
        self.running = False
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载系统配置"""
        default_config = {
            "system": {
                "max_concurrent": 3,
                "log_level": "INFO",
                "data_retention_days": 30
            },
            "database": {
                "path": str(self.data_dir / "collections.db")
            },
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": ""
                }
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                return config
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
                return default_config
        else:
            # 创建默认配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已创建默认配置文件: {self.config_file}")
            return default_config
    
    async def initialize(self):
        """初始化系统组件"""
        try:
            # 配置日志
            log_level = getattr(logging, self.config["system"]["log_level"].upper())
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.data_dir / "system.log", encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            # 初始化组件
            max_concurrent = self.config["system"]["max_concurrent"]
            
            self.storage = CollectionStorage(str(self.data_dir))
            self.scheduler = TaskScheduler(str(self.data_dir), max_concurrent)
            self.collection_manager = CollectionManager(str(self.data_dir / "collections"))
            self.comparator = BatchComparator(max_concurrent)
            
            self.logger.info("系统组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise
    
    async def start(self):
        """启动采集系统"""
        if self.running:
            self.logger.warning("系统已在运行中")
            return
        
        try:
            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            self.logger.info("🚀 Ubuntu 自动化定时采集系统启动")
            
            # 启动调度器
            await self.scheduler.start()
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止采集系统"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("正在停止采集系统...")
        
        try:
            # 停止组件
            if self.scheduler:
                await self.scheduler.stop()
            
            if self.collection_manager:
                await self.collection_manager.cleanup()
            
            if self.storage:
                await self.storage.close()
            
            self.logger.info("采集系统已停止")
            
        except Exception as e:
            self.logger.error(f"停止系统时出错: {e}")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在优雅停止...")
        asyncio.create_task(self.stop())
    
    async def add_task(self, task_config_file: str) -> bool:
        """添加采集任务"""
        try:
            task_file = Path(task_config_file)
            if not task_file.exists():
                self.logger.error(f"任务配置文件不存在: {task_config_file}")
                return False
            
            # 读取任务配置
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 验证必要字段
            required_fields = ["task_id", "name", "schedule", "urls", "cookies"]
            for field in required_fields:
                if field not in task_data:
                    self.logger.error(f"任务配置缺少必要字段: {field}")
                    return False
            
            # 创建任务配置
            schedule_data = task_data["schedule"]
            schedule = ScheduleConfig(
                type=schedule_data["type"],
                expression=schedule_data["expression"],
                timezone=schedule_data.get("timezone", "Asia/Shanghai")
            )
            
            task_config = TaskConfig(
                task_id=task_data["task_id"],
                name=task_data["name"],
                schedule=schedule,
                urls=task_data["urls"],
                cookies=task_data["cookies"],
                options=task_data.get("options", {}),
                notification=task_data.get("notification")
            )
            
            # 添加任务
            success = self.scheduler.add_task(task_config)
            if success:
                self.logger.info(f"任务添加成功: {task_config.name}")
            else:
                self.logger.error(f"任务添加失败: {task_config.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False
    
    async def remove_task(self, task_id: str) -> bool:
        """删除采集任务"""
        try:
            success = self.scheduler.remove_task(task_id)
            if success:
                self.logger.info(f"任务删除成功: {task_id}")
            else:
                self.logger.error(f"任务删除失败: {task_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            return False
    
    async def list_tasks(self) -> Dict[str, Any]:
        """列出所有任务"""
        try:
            tasks = self.scheduler.get_task_list()
            return {
                "total_tasks": len(tasks),
                "tasks": tasks,
                "system_status": "running" if self.running else "stopped"
            }
        except Exception as e:
            self.logger.error(f"获取任务列表失败: {e}")
            return {"error": str(e)}
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            return self.scheduler.get_task_status(task_id)
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return {"error": str(e)}
    
    async def manual_execute(self, task_id: str) -> Dict[str, Any]:
        """手动执行任务"""
        try:
            if task_id not in self.scheduler.tasks:
                return {"error": f"任务不存在: {task_id}"}
            
            task_config = self.scheduler.tasks[task_id]
            
            # 执行采集
            collection_id = await self.collection_manager.create_collection_task(
                task_id=task_config.task_id,
                urls=task_config.urls,
                cookies=task_config.cookies,
                options=task_config.options
            )
            
            self.logger.info(f"手动执行任务完成: {task_id} -> {collection_id}")
            
            return {
                "success": True,
                "collection_id": collection_id,
                "task_name": task_config.name
            }
            
        except Exception as e:
            self.logger.error(f"手动执行任务失败: {e}")
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 获取存储统计
            storage_stats = await self.storage.get_storage_statistics()
            
            # 获取任务统计
            tasks = self.scheduler.get_task_list()
            active_tasks = sum(1 for task in tasks)
            
            return {
                "system": {
                    "running": self.running,
                    "version": "1.0.0",
                    "start_time": datetime.now().isoformat()
                },
                "tasks": {
                    "total": active_tasks,
                    "active": active_tasks if self.running else 0
                },
                "storage": storage_stats,
                "config": self.config
            }
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_data(self, days: int = None) -> Dict[str, Any]:
        """清理历史数据"""
        try:
            days = days or self.config["system"]["data_retention_days"]
            await self.storage.cleanup_old_data(days)
            
            return {
                "success": True,
                "cleaned_days": days,
                "message": f"已清理 {days} 天前的历史数据"
            }
            
        except Exception as e:
            self.logger.error(f"清理数据失败: {e}")
            return {"error": str(e)}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Ubuntu 自动化定时采集系统')
    parser.add_argument('command', choices=[
        'start', 'stop', 'add-task', 'remove-task', 
        'list-tasks', 'status', 'execute', 'cleanup'
    ], help='执行的命令')
    parser.add_argument('--config', default='./config/system.json', help='配置文件路径')
    parser.add_argument('--data-dir', default='./data', help='数据存储目录')
    parser.add_argument('--task-file', help='任务配置文件（add-task时使用）')
    parser.add_argument('--task-id', help='任务ID（remove-task/status/execute时使用）')
    parser.add_argument('--days', type=int, help='清理天数（cleanup时使用）')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    
    args = parser.parse_args()
    
    # 创建系统管理器
    system = CollectionSystemManager(args.config, args.data_dir)
    await system.initialize()
    
    try:
        if args.command == 'start':
            print("启动 Ubuntu 自动化定时采集系统...")
            await system.start()
            
            if args.daemon:
                print("系统以守护进程模式运行")
                while system.running:
                    await asyncio.sleep(60)
            else:
                print("按 Ctrl+C 停止系统")
                try:
                    while system.running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\n收到停止信号...")
        
        elif args.command == 'add-task':
            if not args.task_file:
                print("错误: 需要指定任务配置文件 --task-file")
                sys.exit(1)
            
            success = await system.add_task(args.task_file)
            if success:
                print("任务添加成功")
            else:
                print("任务添加失败")
                sys.exit(1)
        
        elif args.command == 'remove-task':
            if not args.task_id:
                print("错误: 需要指定任务ID --task-id")
                sys.exit(1)
            
            success = await system.remove_task(args.task_id)
            if success:
                print("任务删除成功")
            else:
                print("任务删除失败")
                sys.exit(1)
        
        elif args.command == 'list-tasks':
            result = await system.list_tasks()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.command == 'status':
            if args.task_id:
                result = await system.get_task_status(args.task_id)
            else:
                result = await system.get_system_status()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.command == 'execute':
            if not args.task_id:
                print("错误: 需要指定任务ID --task-id")
                sys.exit(1)
            
            result = await system.manual_execute(args.task_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.command == 'cleanup':
            result = await system.cleanup_data(args.days)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())