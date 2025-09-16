#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水平扩展架构设计
实现多实例协调、负载均衡、Cookie池管理
"""

import asyncio
import json
import logging
import time
import uuid
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class InstanceStatus(Enum):
    """实例状态"""
    HEALTHY = "healthy"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"

@dataclass
class DownloadTask:
    """下载任务"""
    task_id: str
    doc_url: str
    doc_id: str
    format_type: str
    priority: int = 0
    created_at: datetime = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_instance: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_path: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class InstanceInfo:
    """实例信息"""
    instance_id: str
    host: str
    port: int
    status: InstanceStatus
    current_tasks: int
    max_concurrent_tasks: int
    last_heartbeat: datetime
    health_score: float
    total_processed: int
    success_rate: float
    avg_response_time: float
    
    def to_dict(self):
        return asdict(self)

class CookiePool:
    """Cookie池管理器"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.pool_key = "cookie_pool"
        self.usage_key = "cookie_usage"
        self.blacklist_key = "cookie_blacklist"
        
    async def add_cookie(self, cookie_data: Dict[str, Any]) -> bool:
        """添加Cookie到池中"""
        try:
            cookie_id = hashlib.md5(cookie_data["cookie_string"].encode()).hexdigest()
            
            cookie_info = {
                "cookie_id": cookie_id,
                "cookie_string": cookie_data["cookie_string"],
                "account_info": cookie_data.get("account_info", {}),
                "added_at": datetime.now().isoformat(),
                "last_used": None,
                "usage_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "is_active": True,
                "daily_usage_limit": cookie_data.get("daily_limit", 100),
                "concurrent_usage_limit": cookie_data.get("concurrent_limit", 2)
            }
            
            await self.redis_client.hset(self.pool_key, cookie_id, json.dumps(cookie_info))
            logger.info(f"✅ Cookie {cookie_id[:8]} 已添加到池中")
            return True
        
        except Exception as e:
            logger.error(f"❌ 添加Cookie失败: {e}")
            return False
    
    async def get_available_cookie(self, exclude_ids: List[str] = None) -> Optional[Dict[str, Any]]:
        """获取可用的Cookie"""
        try:
            exclude_ids = exclude_ids or []
            
            # 获取所有Cookie
            all_cookies = await self.redis_client.hgetall(self.pool_key)
            
            available_cookies = []
            
            for cookie_id, cookie_data in all_cookies.items():
                if isinstance(cookie_id, bytes):
                    cookie_id = cookie_id.decode()
                
                if cookie_id in exclude_ids:
                    continue
                
                cookie_info = json.loads(cookie_data)
                
                # 检查Cookie是否可用
                if not cookie_info.get("is_active", True):
                    continue
                
                # 检查是否在黑名单中
                is_blacklisted = await self.redis_client.sismember(self.blacklist_key, cookie_id)
                if is_blacklisted:
                    continue
                
                # 检查当前使用数量
                current_usage = await self._get_current_usage(cookie_id)
                if current_usage >= cookie_info.get("concurrent_usage_limit", 2):
                    continue
                
                # 检查每日使用限制
                daily_usage = await self._get_daily_usage(cookie_id)
                if daily_usage >= cookie_info.get("daily_usage_limit", 100):
                    continue
                
                # 计算优先级分数（基于成功率和使用频率）
                success_rate = cookie_info.get("success_count", 0) / max(cookie_info.get("usage_count", 1), 1)
                priority_score = success_rate - (current_usage * 0.1)
                
                available_cookies.append((cookie_id, cookie_info, priority_score))
            
            if not available_cookies:
                logger.warning("⚠️ 没有可用的Cookie")
                return None
            
            # 按优先级排序，选择最佳Cookie
            available_cookies.sort(key=lambda x: x[2], reverse=True)
            best_cookie_id, best_cookie_info, _ = available_cookies[0]
            
            # 标记为使用中
            await self._mark_cookie_in_use(best_cookie_id)
            
            logger.info(f"🍪 分配Cookie {best_cookie_id[:8]}")
            return {
                "cookie_id": best_cookie_id,
                "cookie_string": best_cookie_info["cookie_string"],
                "account_info": best_cookie_info.get("account_info", {})
            }
        
        except Exception as e:
            logger.error(f"❌ 获取可用Cookie失败: {e}")
            return None
    
    async def release_cookie(self, cookie_id: str, success: bool = True):
        """释放Cookie使用"""
        try:
            # 更新使用统计
            cookie_data = await self.redis_client.hget(self.pool_key, cookie_id)
            if cookie_data:
                cookie_info = json.loads(cookie_data)
                cookie_info["usage_count"] = cookie_info.get("usage_count", 0) + 1
                cookie_info["last_used"] = datetime.now().isoformat()
                
                if success:
                    cookie_info["success_count"] = cookie_info.get("success_count", 0) + 1
                else:
                    cookie_info["failure_count"] = cookie_info.get("failure_count", 0) + 1
                    
                    # 如果失败率过高，标记为不活跃
                    total_usage = cookie_info["usage_count"]
                    failure_rate = cookie_info["failure_count"] / total_usage
                    if total_usage >= 10 and failure_rate >= 0.5:
                        cookie_info["is_active"] = False
                        logger.warning(f"⚠️ Cookie {cookie_id[:8]} 因失败率过高被禁用")
                
                await self.redis_client.hset(self.pool_key, cookie_id, json.dumps(cookie_info))
            
            # 移除使用标记
            await self._unmark_cookie_in_use(cookie_id)
            
        except Exception as e:
            logger.error(f"❌ 释放Cookie失败: {e}")
    
    async def _get_current_usage(self, cookie_id: str) -> int:
        """获取Cookie当前使用数量"""
        try:
            usage_count = await self.redis_client.scard(f"{self.usage_key}:{cookie_id}")
            return usage_count
        except Exception:
            return 0
    
    async def _get_daily_usage(self, cookie_id: str) -> int:
        """获取Cookie每日使用次数"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            daily_key = f"daily_usage:{cookie_id}:{today}"
            usage = await self.redis_client.get(daily_key)
            return int(usage) if usage else 0
        except Exception:
            return 0
    
    async def _mark_cookie_in_use(self, cookie_id: str):
        """标记Cookie正在使用"""
        try:
            usage_id = str(uuid.uuid4())
            await self.redis_client.sadd(f"{self.usage_key}:{cookie_id}", usage_id)
            await self.redis_client.expire(f"{self.usage_key}:{cookie_id}", 300)  # 5分钟过期
            
            # 更新每日使用统计
            today = datetime.now().strftime('%Y-%m-%d')
            daily_key = f"daily_usage:{cookie_id}:{today}"
            await self.redis_client.incr(daily_key)
            await self.redis_client.expire(daily_key, 86400)  # 24小时过期
            
            return usage_id
        except Exception as e:
            logger.error(f"标记Cookie使用失败: {e}")
            return None
    
    async def _unmark_cookie_in_use(self, cookie_id: str, usage_id: str = None):
        """取消Cookie使用标记"""
        try:
            if usage_id:
                await self.redis_client.srem(f"{self.usage_key}:{cookie_id}", usage_id)
            else:
                # 清空所有使用标记
                await self.redis_client.delete(f"{self.usage_key}:{cookie_id}")
        except Exception as e:
            logger.error(f"取消Cookie使用标记失败: {e}")

class TaskDistributor:
    """任务分发器"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.task_queue_key = "download_tasks"
        self.processing_queue_key = "processing_tasks"
        self.completed_queue_key = "completed_tasks"
        self.instances_key = "instances"
        
    async def submit_task(self, task: DownloadTask) -> str:
        """提交任务到队列"""
        try:
            task_data = asdict(task)
            # 序列化datetime对象
            for key, value in task_data.items():
                if isinstance(value, datetime):
                    task_data[key] = value.isoformat()
            
            # 根据优先级添加到不同队列
            if task.priority > 5:
                queue_key = f"{self.task_queue_key}:high"
            elif task.priority > 2:
                queue_key = f"{self.task_queue_key}:normal"
            else:
                queue_key = f"{self.task_queue_key}:low"
            
            await self.redis_client.lpush(queue_key, json.dumps(task_data))
            
            logger.info(f"📋 任务 {task.task_id} 已提交到队列")
            return task.task_id
        
        except Exception as e:
            logger.error(f"❌ 任务提交失败: {e}")
            return None
    
    async def get_next_task(self, instance_id: str) -> Optional[DownloadTask]:
        """为实例获取下一个任务"""
        try:
            # 按优先级从队列中获取任务
            queues = [
                f"{self.task_queue_key}:high",
                f"{self.task_queue_key}:normal",
                f"{self.task_queue_key}:low"
            ]
            
            for queue_key in queues:
                task_data = await self.redis_client.brpop(queue_key, timeout=1)
                if task_data:
                    _, task_json = task_data
                    task_dict = json.loads(task_json)
                    
                    # 重建datetime对象
                    for key, value in task_dict.items():
                        if key.endswith('_at') and value:
                            task_dict[key] = datetime.fromisoformat(value)
                    
                    task = DownloadTask(**task_dict)
                    task.status = TaskStatus.ASSIGNED
                    task.assigned_instance = instance_id
                    task.assigned_at = datetime.now()
                    
                    # 移到处理队列
                    await self._move_to_processing(task)
                    
                    logger.info(f"📤 任务 {task.task_id} 分配给实例 {instance_id}")
                    return task
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取任务失败: {e}")
            return None
    
    async def _move_to_processing(self, task: DownloadTask):
        """将任务移到处理队列"""
        try:
            task_data = asdict(task)
            # 序列化datetime对象
            for key, value in task_data.items():
                if isinstance(value, datetime):
                    task_data[key] = value.isoformat()
            
            await self.redis_client.hset(
                self.processing_queue_key, 
                task.task_id, 
                json.dumps(task_data)
            )
        except Exception as e:
            logger.error(f"移动任务到处理队列失败: {e}")
    
    async def complete_task(self, task: DownloadTask, result: Dict[str, Any]):
        """完成任务"""
        try:
            task.status = TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result_path = result.get("file_path")
            task.error_message = result.get("error_message")
            
            # 移到完成队列
            task_data = asdict(task)
            for key, value in task_data.items():
                if isinstance(value, datetime):
                    task_data[key] = value.isoformat()
            
            await self.redis_client.hset(
                self.completed_queue_key,
                task.task_id,
                json.dumps(task_data)
            )
            
            # 从处理队列中移除
            await self.redis_client.hdel(self.processing_queue_key, task.task_id)
            
            logger.info(f"✅ 任务 {task.task_id} 已完成: {task.status.value}")
            
        except Exception as e:
            logger.error(f"❌ 完成任务失败: {e}")
    
    async def retry_task(self, task: DownloadTask):
        """重试任务"""
        try:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRY
                task.assigned_instance = None
                task.assigned_at = None
                
                # 重新提交到队列
                await self.submit_task(task)
                
                # 从处理队列移除
                await self.redis_client.hdel(self.processing_queue_key, task.task_id)
                
                logger.info(f"🔄 任务 {task.task_id} 重试 {task.retry_count}/{task.max_retries}")
            else:
                # 达到最大重试次数，标记为失败
                await self.complete_task(task, {"success": False, "error_message": "Max retries exceeded"})
                logger.error(f"❌ 任务 {task.task_id} 达到最大重试次数")
                
        except Exception as e:
            logger.error(f"❌ 任务重试失败: {e}")

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.instances_key = "instances"
        
    async def register_instance(self, instance: InstanceInfo):
        """注册实例"""
        try:
            instance_data = instance.to_dict()
            instance_data["last_heartbeat"] = instance.last_heartbeat.isoformat()
            
            await self.redis_client.hset(
                self.instances_key,
                instance.instance_id,
                json.dumps(instance_data)
            )
            
            logger.info(f"📡 实例 {instance.instance_id} 已注册")
            
        except Exception as e:
            logger.error(f"❌ 实例注册失败: {e}")
    
    async def update_instance_status(self, instance_id: str, status_update: Dict[str, Any]):
        """更新实例状态"""
        try:
            instance_data = await self.redis_client.hget(self.instances_key, instance_id)
            if instance_data:
                instance_info = json.loads(instance_data)
                instance_info.update(status_update)
                instance_info["last_heartbeat"] = datetime.now().isoformat()
                
                await self.redis_client.hset(
                    self.instances_key,
                    instance_id,
                    json.dumps(instance_info)
                )
                
        except Exception as e:
            logger.error(f"❌ 更新实例状态失败: {e}")
    
    async def get_best_instance(self) -> Optional[str]:
        """获取最佳实例ID"""
        try:
            all_instances = await self.redis_client.hgetall(self.instances_key)
            
            if not all_instances:
                return None
            
            healthy_instances = []
            
            for instance_id, instance_data in all_instances.items():
                if isinstance(instance_id, bytes):
                    instance_id = instance_id.decode()
                
                instance_info = json.loads(instance_data)
                
                # 检查实例健康状态
                last_heartbeat = datetime.fromisoformat(instance_info["last_heartbeat"])
                if datetime.now() - last_heartbeat > timedelta(minutes=2):
                    continue  # 实例可能离线
                
                if instance_info["status"] not in ["healthy", "busy"]:
                    continue  # 实例不健康
                
                if instance_info["current_tasks"] >= instance_info["max_concurrent_tasks"]:
                    continue  # 实例已满载
                
                # 计算实例负载分数（越低越好）
                load_score = (
                    (instance_info["current_tasks"] / instance_info["max_concurrent_tasks"]) * 0.4 +
                    (1 - instance_info["health_score"]) * 0.3 +
                    (instance_info["avg_response_time"] / 100.0) * 0.2 +
                    (1 - instance_info["success_rate"]) * 0.1
                )
                
                healthy_instances.append((instance_id, load_score))
            
            if not healthy_instances:
                return None
            
            # 选择负载分数最低的实例
            healthy_instances.sort(key=lambda x: x[1])
            return healthy_instances[0][0]
            
        except Exception as e:
            logger.error(f"❌ 获取最佳实例失败: {e}")
            return None
    
    async def get_all_instances(self) -> List[InstanceInfo]:
        """获取所有实例信息"""
        try:
            all_instances = await self.redis_client.hgetall(self.instances_key)
            instances = []
            
            for instance_id, instance_data in all_instances.items():
                if isinstance(instance_id, bytes):
                    instance_id = instance_id.decode()
                
                instance_info = json.loads(instance_data)
                instance_info["last_heartbeat"] = datetime.fromisoformat(instance_info["last_heartbeat"])
                instance_info["status"] = InstanceStatus(instance_info["status"])
                
                instances.append(InstanceInfo(**instance_info))
            
            return instances
            
        except Exception as e:
            logger.error(f"❌ 获取实例列表失败: {e}")
            return []

class HorizontalScalingManager:
    """水平扩展管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """初始化水平扩展管理器"""
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.cookie_pool = CookiePool(self.redis_client)
        self.task_distributor = TaskDistributor(self.redis_client)
        self.load_balancer = LoadBalancer(self.redis_client)
        
        self.scaling_config = {
            "min_instances": 1,
            "max_instances": 10,
            "target_cpu_utilization": 70,
            "scale_up_threshold": 80,
            "scale_down_threshold": 30,
            "cooldown_period": 300  # 5分钟冷却期
        }
        
        self.last_scaling_action = None
        
    async def submit_download_request(self, doc_url: str, format_type: str = "csv", 
                                    priority: int = 0) -> str:
        """提交下载请求"""
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 从URL提取文档ID
            doc_id = doc_url.split('/')[-1] if '/' in doc_url else doc_url
            
            # 创建任务
            task = DownloadTask(
                task_id=task_id,
                doc_url=doc_url,
                doc_id=doc_id,
                format_type=format_type,
                priority=priority
            )
            
            # 提交到任务队列
            submitted_id = await self.task_distributor.submit_task(task)
            
            if submitted_id:
                logger.info(f"📥 下载请求已提交: {task_id}")
                return task_id
            else:
                logger.error(f"❌ 下载请求提交失败")
                return None
        
        except Exception as e:
            logger.error(f"❌ 提交下载请求失败: {e}")
            return None
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            # 检查处理队列
            processing_task = await self.redis_client.hget(
                self.task_distributor.processing_queue_key, 
                task_id
            )
            if processing_task:
                task_data = json.loads(processing_task)
                return {
                    "status": "processing",
                    "details": task_data
                }
            
            # 检查完成队列
            completed_task = await self.redis_client.hget(
                self.task_distributor.completed_queue_key,
                task_id
            )
            if completed_task:
                task_data = json.loads(completed_task)
                return {
                    "status": "completed",
                    "details": task_data
                }
            
            # 检查待处理队列
            queues = [
                f"{self.task_distributor.task_queue_key}:high",
                f"{self.task_distributor.task_queue_key}:normal", 
                f"{self.task_distributor.task_queue_key}:low"
            ]
            
            for queue_key in queues:
                queue_length = await self.redis_client.llen(queue_key)
                if queue_length > 0:
                    # 这里简化处理，实际可以遍历队列查找特定任务
                    return {
                        "status": "pending",
                        "queue_position": "unknown",
                        "estimated_wait_time": queue_length * 45  # 假设每任务45秒
                    }
            
            return {
                "status": "not_found",
                "message": "Task not found in any queue"
            }
        
        except Exception as e:
            logger.error(f"❌ 获取任务状态失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def start_coordinator(self):
        """启动协调器"""
        try:
            logger.info("🚀 启动水平扩展协调器...")
            
            # 创建协调任务
            tasks = [
                asyncio.create_task(self._monitor_system_load()),
                asyncio.create_task(self._manage_scaling()),
                asyncio.create_task(self._cleanup_expired_tasks()),
                asyncio.create_task(self._health_check_instances())
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ 协调器启动失败: {e}")
    
    async def _monitor_system_load(self):
        """监控系统负载"""
        while True:
            try:
                # 获取所有实例信息
                instances = await self.load_balancer.get_all_instances()
                
                if instances:
                    # 计算平均负载
                    avg_cpu = sum(inst.health_score for inst in instances) / len(instances)
                    avg_tasks = sum(inst.current_tasks for inst in instances) / len(instances)
                    
                    # 计算队列长度
                    total_queue_length = 0
                    queues = [
                        f"{self.task_distributor.task_queue_key}:high",
                        f"{self.task_distributor.task_queue_key}:normal",
                        f"{self.task_distributor.task_queue_key}:low"
                    ]
                    
                    for queue in queues:
                        length = await self.redis_client.llen(queue)
                        total_queue_length += length
                    
                    # 存储监控数据
                    monitoring_data = {
                        "timestamp": datetime.now().isoformat(),
                        "active_instances": len(instances),
                        "avg_cpu_utilization": avg_cpu * 100,
                        "avg_concurrent_tasks": avg_tasks,
                        "total_queue_length": total_queue_length,
                        "healthy_instances": len([i for i in instances if i.status == InstanceStatus.HEALTHY])
                    }
                    
                    await self.redis_client.lpush("system_monitoring", json.dumps(monitoring_data))
                    await self.redis_client.ltrim("system_monitoring", 0, 999)  # 保留最新1000条记录
                    
                    logger.debug(f"📊 系统负载: CPU {avg_cpu*100:.1f}%, 队列 {total_queue_length}, 实例 {len(instances)}")
                
                await asyncio.sleep(30)  # 30秒监控一次
                
            except Exception as e:
                logger.error(f"❌ 系统负载监控失败: {e}")
                await asyncio.sleep(30)
    
    async def _manage_scaling(self):
        """管理自动扩缩容"""
        while True:
            try:
                # 检查是否在冷却期
                if (self.last_scaling_action and 
                    datetime.now() - self.last_scaling_action < timedelta(seconds=self.scaling_config["cooldown_period"])):
                    await asyncio.sleep(60)
                    continue
                
                instances = await self.load_balancer.get_all_instances()
                
                if not instances:
                    await asyncio.sleep(60)
                    continue
                
                # 计算扩缩容指标
                avg_cpu = sum(inst.health_score for inst in instances) / len(instances) * 100
                active_instances = len([i for i in instances if i.status in [InstanceStatus.HEALTHY, InstanceStatus.BUSY]])
                
                # 计算总队列长度
                total_queue = 0
                for queue_suffix in ["high", "normal", "low"]:
                    queue_key = f"{self.task_distributor.task_queue_key}:{queue_suffix}"
                    total_queue += await self.redis_client.llen(queue_key)
                
                # 扩容决策
                should_scale_up = (
                    avg_cpu > self.scaling_config["scale_up_threshold"] or
                    total_queue > active_instances * 3 or
                    active_instances < self.scaling_config["min_instances"]
                )
                
                # 缩容决策
                should_scale_down = (
                    avg_cpu < self.scaling_config["scale_down_threshold"] and
                    total_queue == 0 and
                    active_instances > self.scaling_config["min_instances"]
                )
                
                if should_scale_up and active_instances < self.scaling_config["max_instances"]:
                    await self._trigger_scale_up()
                elif should_scale_down:
                    await self._trigger_scale_down()
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"❌ 自动扩缩容管理失败: {e}")
                await asyncio.sleep(60)
    
    async def _trigger_scale_up(self):
        """触发扩容"""
        try:
            logger.info("📈 触发扩容操作")
            
            # 这里应该调用云服务API创建新实例
            # 暂时记录扩容事件
            scale_event = {
                "action": "scale_up",
                "timestamp": datetime.now().isoformat(),
                "reason": "High load detected"
            }
            
            await self.redis_client.lpush("scaling_events", json.dumps(scale_event))
            self.last_scaling_action = datetime.now()
            
            # 实际环境中，这里应该：
            # 1. 调用云服务API创建新的Docker容器/虚拟机
            # 2. 配置新实例的环境变量和配置
            # 3. 启动新实例的服务进程
            
        except Exception as e:
            logger.error(f"❌ 扩容操作失败: {e}")
    
    async def _trigger_scale_down(self):
        """触发缩容"""
        try:
            logger.info("📉 触发缩容操作")
            
            # 选择最空闲的实例进行下线
            instances = await self.load_balancer.get_all_instances()
            idle_instances = [
                inst for inst in instances 
                if inst.current_tasks == 0 and inst.status == InstanceStatus.HEALTHY
            ]
            
            if idle_instances:
                # 选择处理任务最少的实例
                target_instance = min(idle_instances, key=lambda x: x.total_processed)
                
                # 标记实例为下线状态
                await self.load_balancer.update_instance_status(
                    target_instance.instance_id,
                    {"status": "offline"}
                )
                
                scale_event = {
                    "action": "scale_down",
                    "timestamp": datetime.now().isoformat(),
                    "target_instance": target_instance.instance_id,
                    "reason": "Low load detected"
                }
                
                await self.redis_client.lpush("scaling_events", json.dumps(scale_event))
                self.last_scaling_action = datetime.now()
                
                logger.info(f"📉 实例 {target_instance.instance_id} 已标记下线")
        
        except Exception as e:
            logger.error(f"❌ 缩容操作失败: {e}")
    
    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        while True:
            try:
                # 清理超时的处理中任务
                processing_tasks = await self.redis_client.hgetall(
                    self.task_distributor.processing_queue_key
                )
                
                current_time = datetime.now()
                
                for task_id, task_data in processing_tasks.items():
                    task_info = json.loads(task_data)
                    assigned_at = datetime.fromisoformat(task_info["assigned_at"])
                    
                    # 如果任务超过10分钟还未完成，认为超时
                    if current_time - assigned_at > timedelta(minutes=10):
                        logger.warning(f"⏰ 任务 {task_id} 超时，重新调度")
                        
                        # 重建任务对象
                        task_dict = task_info.copy()
                        for key, value in task_dict.items():
                            if key.endswith('_at') and value:
                                task_dict[key] = datetime.fromisoformat(value)
                        
                        task = DownloadTask(**task_dict)
                        await self.task_distributor.retry_task(task)
                
                # 清理过期的Cookie使用标记
                # 清理过期的实例心跳记录
                
                await asyncio.sleep(300)  # 5分钟清理一次
                
            except Exception as e:
                logger.error(f"❌ 清理过期任务失败: {e}")
                await asyncio.sleep(300)
    
    async def _health_check_instances(self):
        """健康检查实例"""
        while True:
            try:
                instances = await self.load_balancer.get_all_instances()
                current_time = datetime.now()
                
                for instance in instances:
                    time_since_heartbeat = current_time - instance.last_heartbeat
                    
                    if time_since_heartbeat > timedelta(minutes=5):
                        # 实例可能离线
                        await self.load_balancer.update_instance_status(
                            instance.instance_id,
                            {"status": "offline"}
                        )
                        logger.warning(f"⚠️ 实例 {instance.instance_id} 可能离线")
                    elif time_since_heartbeat > timedelta(minutes=2):
                        # 实例响应缓慢
                        await self.load_balancer.update_instance_status(
                            instance.instance_id,
                            {"status": "degraded"}
                        )
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"❌ 实例健康检查失败: {e}")
                await asyncio.sleep(60)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 这里应该返回系统的实时状态
            # 简化实现，返回基本信息
            return {
                "status": "running",
                "coordinator_active": True,
                "scaling_config": self.scaling_config,
                "last_scaling_action": self.last_scaling_action.isoformat() if self.last_scaling_action else None
            }
        except Exception as e:
            logger.error(f"❌ 获取系统状态失败: {e}")
            return {"status": "error", "message": str(e)}


# 工具函数
async def setup_test_environment():
    """设置测试环境"""
    try:
        manager = HorizontalScalingManager()
        
        # 添加测试Cookie
        test_cookies = [
            {
                "cookie_string": "test_cookie_1=value1; test_cookie_2=value2",
                "account_info": {"account_id": "test1", "username": "testuser1"},
                "daily_limit": 100,
                "concurrent_limit": 2
            },
            {
                "cookie_string": "test_cookie_3=value3; test_cookie_4=value4", 
                "account_info": {"account_id": "test2", "username": "testuser2"},
                "daily_limit": 150,
                "concurrent_limit": 3
            }
        ]
        
        for cookie_data in test_cookies:
            await manager.cookie_pool.add_cookie(cookie_data)
        
        # 注册测试实例
        test_instance = InstanceInfo(
            instance_id="test-instance-1",
            host="localhost",
            port=8080,
            status=InstanceStatus.HEALTHY,
            current_tasks=0,
            max_concurrent_tasks=3,
            last_heartbeat=datetime.now(),
            health_score=0.85,
            total_processed=0,
            success_rate=0.95,
            avg_response_time=42.0
        )
        
        await manager.load_balancer.register_instance(test_instance)
        
        logger.info("✅ 测试环境设置完成")
        return manager
        
    except Exception as e:
        logger.error(f"❌ 测试环境设置失败: {e}")
        return None


async def main():
    """主函数 - 演示水平扩展系统"""
    try:
        print("=== 腾讯文档水平扩展架构演示 ===")
        
        # 设置测试环境
        manager = await setup_test_environment()
        if not manager:
            print("❌ 测试环境设置失败")
            return
        
        # 提交测试任务
        test_urls = [
            "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN",
            "https://docs.qq.com/sheet/DRFppYm15RGZ2WExN", 
            "https://docs.qq.com/sheet/DRHZrS1hOS3pwRGZB"
        ]
        
        submitted_tasks = []
        for url in test_urls:
            task_id = await manager.submit_download_request(url, "csv", priority=1)
            if task_id:
                submitted_tasks.append(task_id)
                print(f"✅ 任务提交成功: {task_id}")
        
        # 查询任务状态
        await asyncio.sleep(2)
        for task_id in submitted_tasks:
            status = await manager.get_task_status(task_id)
            print(f"📋 任务 {task_id[:8]} 状态: {status['status']}")
        
        # 获取系统状态
        system_status = manager.get_system_status()
        print(f"\n🖥️ 系统状态: {system_status}")
        
        print("\n✅ 演示完成")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(main())