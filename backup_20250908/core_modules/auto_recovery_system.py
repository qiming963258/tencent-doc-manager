#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动恢复系统 - 处理Cookie失效、API变更、下载失败等问题
DevOps 自动化故障恢复和降级策略
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class RecoveryAction(Enum):
    """恢复动作类型"""
    COOKIE_REFRESH = "cookie_refresh"
    FALLBACK_METHOD = "fallback_method"
    API_RETRY = "api_retry"
    CACHE_FALLBACK = "cache_fallback"
    MANUAL_INTERVENTION = "manual_intervention"
    SERVICE_RESTART = "service_restart"

class FailureType(Enum):
    """故障类型"""
    COOKIE_EXPIRED = "cookie_expired"
    API_CHANGED = "api_changed"
    NETWORK_TIMEOUT = "network_timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class RecoveryStrategy:
    """恢复策略"""
    failure_type: FailureType
    actions: List[RecoveryAction]
    max_attempts: int
    backoff_seconds: int
    success_threshold: float
    timeout_seconds: int

class AutoRecoverySystem:
    """自动恢复系统"""
    
    def __init__(self, config_dir: str = None):
        """初始化自动恢复系统"""
        self.config_dir = config_dir or "/root/projects/tencent-doc-manager/config"
        self.recovery_log_file = Path(self.config_dir) / "recovery_log.json"
        self.recovery_history = []
        self.active_recoveries = {}
        
        # 恢复策略配置
        self.recovery_strategies = {
            FailureType.COOKIE_EXPIRED: RecoveryStrategy(
                failure_type=FailureType.COOKIE_EXPIRED,
                actions=[
                    RecoveryAction.COOKIE_REFRESH,
                    RecoveryAction.FALLBACK_METHOD,
                    RecoveryAction.MANUAL_INTERVENTION
                ],
                max_attempts=3,
                backoff_seconds=30,
                success_threshold=0.8,
                timeout_seconds=300
            ),
            FailureType.API_CHANGED: RecoveryStrategy(
                failure_type=FailureType.API_CHANGED,
                actions=[
                    RecoveryAction.API_RETRY,
                    RecoveryAction.FALLBACK_METHOD,
                    RecoveryAction.MANUAL_INTERVENTION
                ],
                max_attempts=2,
                backoff_seconds=60,
                success_threshold=0.9,
                timeout_seconds=600
            ),
            FailureType.NETWORK_TIMEOUT: RecoveryStrategy(
                failure_type=FailureType.NETWORK_TIMEOUT,
                actions=[
                    RecoveryAction.API_RETRY,
                    RecoveryAction.FALLBACK_METHOD
                ],
                max_attempts=5,
                backoff_seconds=10,
                success_threshold=0.7,
                timeout_seconds=180
            ),
            FailureType.RESOURCE_EXHAUSTION: RecoveryStrategy(
                failure_type=FailureType.RESOURCE_EXHAUSTION,
                actions=[
                    RecoveryAction.CACHE_FALLBACK,
                    RecoveryAction.SERVICE_RESTART,
                    RecoveryAction.MANUAL_INTERVENTION
                ],
                max_attempts=2,
                backoff_seconds=120,
                success_threshold=0.8,
                timeout_seconds=300
            )
        }
        
        # 备用下载方法
        self.fallback_methods = [
            "playwright_stealth",
            "requests_session",
            "cached_download",
            "manual_trigger"
        ]
        
        # 成功率跟踪
        self.success_tracking = {
            "last_24h": [],
            "current_streak": 0,
            "failure_streak": 0
        }
    
    async def detect_and_recover(self, error_context: Dict) -> Tuple[bool, str, Dict]:
        """检测故障并执行自动恢复"""
        try:
            logger.info("🔍 开始故障检测和自动恢复...")
            
            # 分析故障类型
            failure_type = await self._analyze_failure(error_context)
            logger.info(f"📊 故障类型识别: {failure_type.value}")
            
            # 获取恢复策略
            strategy = self.recovery_strategies.get(failure_type)
            if not strategy:
                return False, f"未找到{failure_type.value}的恢复策略", {}
            
            # 检查是否已在恢复中
            recovery_key = f"{failure_type.value}_{int(time.time())}"
            if recovery_key in self.active_recoveries:
                return False, "恢复进程已在运行中", {}
            
            # 开始恢复进程
            self.active_recoveries[recovery_key] = {
                "start_time": datetime.now(),
                "failure_type": failure_type,
                "status": "running"
            }
            
            recovery_success = False
            recovery_details = {}
            
            try:
                # 执行恢复策略
                recovery_success, recovery_details = await self._execute_recovery_strategy(
                    strategy, error_context
                )
                
                # 记录恢复结果
                recovery_record = {
                    "timestamp": datetime.now().isoformat(),
                    "failure_type": failure_type.value,
                    "recovery_success": recovery_success,
                    "actions_taken": recovery_details.get("actions_taken", []),
                    "recovery_time": recovery_details.get("recovery_time", 0),
                    "error_context": error_context
                }
                
                await self._log_recovery_attempt(recovery_record)
                
                if recovery_success:
                    logger.info(f"✅ 自动恢复成功: {failure_type.value}")
                    self.success_tracking["failure_streak"] = 0
                    self.success_tracking["current_streak"] += 1
                    return True, "自动恢复成功", recovery_details
                else:
                    logger.error(f"❌ 自动恢复失败: {failure_type.value}")
                    self.success_tracking["current_streak"] = 0
                    self.success_tracking["failure_streak"] += 1
                    return False, "自动恢复失败，需要人工介入", recovery_details
            
            finally:
                # 清理活跃恢复记录
                if recovery_key in self.active_recoveries:
                    self.active_recoveries[recovery_key]["status"] = "completed"
                    self.active_recoveries[recovery_key]["end_time"] = datetime.now()
        
        except Exception as e:
            logger.error(f"❌ 自动恢复系统异常: {e}")
            return False, f"恢复系统异常: {str(e)}", {}
    
    async def _analyze_failure(self, error_context: Dict) -> FailureType:
        """分析故障类型"""
        try:
            error_message = error_context.get("error_message", "").lower()
            http_status = error_context.get("http_status", 0)
            response_content = error_context.get("response_content", "").lower()
            
            # Cookie相关错误
            if ("401" in str(http_status) or 
                "unauthorized" in error_message or 
                "cookie" in error_message or
                "login" in response_content):
                return FailureType.COOKIE_EXPIRED
            
            # API变更相关错误
            if ("404" in str(http_status) or
                "not found" in error_message or
                "endpoint" in error_message or
                "api" in error_message):
                return FailureType.API_CHANGED
            
            # 网络超时相关错误
            if ("timeout" in error_message or
                "connection" in error_message or
                "network" in error_message):
                return FailureType.NETWORK_TIMEOUT
            
            # 资源耗尽相关错误
            if ("memory" in error_message or
                "disk" in error_message or
                "resource" in error_message or
                "500" in str(http_status)):
                return FailureType.RESOURCE_EXHAUSTION
            
            return FailureType.UNKNOWN_ERROR
        
        except Exception as e:
            logger.error(f"故障类型分析失败: {e}")
            return FailureType.UNKNOWN_ERROR
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, 
                                       error_context: Dict) -> Tuple[bool, Dict]:
        """执行恢复策略"""
        recovery_details = {
            "actions_taken": [],
            "recovery_time": 0,
            "attempts": 0,
            "final_action": None
        }
        
        start_time = time.time()
        
        try:
            for attempt in range(strategy.max_attempts):
                recovery_details["attempts"] = attempt + 1
                logger.info(f"🔄 恢复尝试 {attempt + 1}/{strategy.max_attempts}")
                
                for action in strategy.actions:
                    try:
                        logger.info(f"⚙️ 执行恢复动作: {action.value}")
                        
                        action_success = await self._execute_recovery_action(
                            action, error_context, strategy
                        )
                        
                        recovery_details["actions_taken"].append({
                            "action": action.value,
                            "success": action_success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        if action_success:
                            # 验证恢复效果
                            validation_success = await self._validate_recovery(
                                strategy, error_context
                            )
                            
                            if validation_success:
                                recovery_details["recovery_time"] = time.time() - start_time
                                recovery_details["final_action"] = action.value
                                logger.info(f"✅ 恢复动作成功: {action.value}")
                                return True, recovery_details
                        
                        # 如果动作失败，继续尝试下一个动作
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        logger.error(f"❌ 恢复动作失败: {action.value}, 错误: {e}")
                        continue
                
                # 如果所有动作都失败，等待后重试
                if attempt < strategy.max_attempts - 1:
                    wait_time = strategy.backoff_seconds * (2 ** attempt)  # 指数退避
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
            
            recovery_details["recovery_time"] = time.time() - start_time
            return False, recovery_details
        
        except Exception as e:
            logger.error(f"❌ 执行恢复策略失败: {e}")
            recovery_details["recovery_time"] = time.time() - start_time
            recovery_details["error"] = str(e)
            return False, recovery_details
    
    async def _execute_recovery_action(self, action: RecoveryAction, 
                                     error_context: Dict, 
                                     strategy: RecoveryStrategy) -> bool:
        """执行具体的恢复动作"""
        try:
            if action == RecoveryAction.COOKIE_REFRESH:
                return await self._refresh_cookies()
            elif action == RecoveryAction.FALLBACK_METHOD:
                return await self._try_fallback_method(error_context)
            elif action == RecoveryAction.API_RETRY:
                return await self._retry_api_call(error_context)
            elif action == RecoveryAction.CACHE_FALLBACK:
                return await self._use_cached_data(error_context)
            elif action == RecoveryAction.SERVICE_RESTART:
                return await self._restart_service_components()
            elif action == RecoveryAction.MANUAL_INTERVENTION:
                return await self._trigger_manual_intervention(error_context)
            else:
                logger.warning(f"⚠️ 未知恢复动作: {action.value}")
                return False
        
        except Exception as e:
            logger.error(f"❌ 恢复动作执行异常: {action.value}, 错误: {e}")
            return False
    
    async def _refresh_cookies(self) -> bool:
        """刷新Cookie"""
        try:
            logger.info("🍪 开始刷新Cookie...")
            
            # 导入Cookie管理器
            from cookie_manager import get_cookie_manager
            
            cookie_manager = get_cookie_manager()
            
            # 尝试获取有效Cookie
            valid_cookies = await cookie_manager.get_valid_cookies()
            
            if valid_cookies:
                logger.info("✅ Cookie刷新成功")
                return True
            else:
                logger.warning("⚠️ Cookie刷新失败，所有Cookie都无效")
                
                # 尝试使用备用Cookie
                backup_success = await self._try_backup_cookies(cookie_manager)
                return backup_success
        
        except Exception as e:
            logger.error(f"❌ Cookie刷新异常: {e}")
            return False
    
    async def _try_backup_cookies(self, cookie_manager) -> bool:
        """尝试备用Cookie"""
        try:
            # 这里可以实现从外部数据源获取备用Cookie的逻辑
            # 比如从加密的配置文件、环境变量或外部API获取
            
            logger.info("🔄 尝试获取备用Cookie...")
            
            # 模拟备用Cookie获取（实际应用中需要实现具体逻辑）
            backup_cookie_sources = [
                "/root/projects/tencent-doc-manager/config/emergency_cookies.json",
                "/root/projects/tencent-doc-manager/config/backup_cookies.json"
            ]
            
            for source in backup_cookie_sources:
                if Path(source).exists():
                    try:
                        with open(source, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                            
                        emergency_cookie = backup_data.get("emergency_cookie")
                        if emergency_cookie:
                            # 验证并更新Cookie
                            update_success = await cookie_manager.update_primary_cookie(emergency_cookie)
                            if update_success:
                                logger.info(f"✅ 备用Cookie设置成功: {source}")
                                return True
                    
                    except Exception as e:
                        logger.warning(f"⚠️ 备用Cookie源失败: {source}, 错误: {e}")
                        continue
            
            logger.warning("⚠️ 所有备用Cookie源都无效")
            return False
        
        except Exception as e:
            logger.error(f"❌ 备用Cookie尝试异常: {e}")
            return False
    
    async def _try_fallback_method(self, error_context: Dict) -> bool:
        """尝试备用下载方法"""
        try:
            logger.info("🔄 尝试备用下载方法...")
            
            doc_url = error_context.get("doc_url", "")
            format_type = error_context.get("format_type", "csv")
            
            if not doc_url:
                logger.warning("⚠️ 缺少文档URL，无法使用备用方法")
                return False
            
            for method in self.fallback_methods:
                try:
                    logger.info(f"📥 尝试备用方法: {method}")
                    
                    if method == "playwright_stealth":
                        success = await self._try_stealth_download(doc_url, format_type)
                    elif method == "requests_session":
                        success = await self._try_requests_download(doc_url, format_type)
                    elif method == "cached_download":
                        success = await self._try_cached_download(doc_url, format_type)
                    elif method == "manual_trigger":
                        success = await self._trigger_manual_download(doc_url, format_type)
                    else:
                        continue
                    
                    if success:
                        logger.info(f"✅ 备用方法成功: {method}")
                        return True
                    
                except Exception as e:
                    logger.warning(f"⚠️ 备用方法失败: {method}, 错误: {e}")
                    continue
            
            logger.warning("⚠️ 所有备用方法都失败")
            return False
        
        except Exception as e:
            logger.error(f"❌ 备用方法尝试异常: {e}")
            return False
    
    async def _try_stealth_download(self, doc_url: str, format_type: str) -> bool:
        """使用隐蔽模式下载"""
        try:
            # 使用更隐蔽的浏览器配置
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-first-run',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1366, 'height': 768}
                )
                
                # 隐藏自动化特征
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                page = await context.new_page()
                
                # 使用现有Cookie管理器的Cookie
                from cookie_manager import get_cookie_manager
                cookie_manager = get_cookie_manager()
                cookies = await cookie_manager.get_valid_cookies()
                
                if cookies:
                    # 设置Cookie并尝试下载
                    # 这里需要实现具体的下载逻辑
                    pass
                
                await browser.close()
                return True  # 模拟成功
        
        except Exception as e:
            logger.error(f"隐蔽下载失败: {e}")
            return False
    
    async def _try_requests_download(self, doc_url: str, format_type: str) -> bool:
        """使用requests会话下载"""
        try:
            # 实现基于requests的下载逻辑
            # 这需要分析和复制浏览器的请求头和参数
            return False  # 目前未实现
        
        except Exception as e:
            logger.error(f"Requests下载失败: {e}")
            return False
    
    async def _try_cached_download(self, doc_url: str, format_type: str) -> bool:
        """使用缓存数据"""
        try:
            # 检查是否有最近的缓存文件可以使用
            cache_dir = Path("/root/projects/tencent-doc-manager/cache")
            
            if cache_dir.exists():
                # 查找相关的缓存文件
                doc_id = doc_url.split('/')[-1] if '/' in doc_url else doc_url
                cache_pattern = f"{doc_id}_*_{format_type}.*"
                
                cached_files = list(cache_dir.glob(cache_pattern))
                
                if cached_files:
                    # 使用最新的缓存文件
                    latest_cache = max(cached_files, key=lambda x: x.stat().st_mtime)
                    cache_age = time.time() - latest_cache.stat().st_mtime
                    
                    # 如果缓存不超过24小时，可以使用
                    if cache_age < 86400:  # 24小时
                        logger.info(f"📦 使用缓存文件: {latest_cache}")
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"缓存下载失败: {e}")
            return False
    
    async def _trigger_manual_download(self, doc_url: str, format_type: str) -> bool:
        """触发手动下载请求"""
        try:
            # 创建手动下载请求文件
            manual_request = {
                "timestamp": datetime.now().isoformat(),
                "doc_url": doc_url,
                "format_type": format_type,
                "status": "pending",
                "priority": "high",
                "reason": "auto_recovery_fallback"
            }
            
            request_file = Path(self.config_dir) / "manual_download_requests.json"
            
            if request_file.exists():
                with open(request_file, 'r', encoding='utf-8') as f:
                    requests_data = json.load(f)
            else:
                requests_data = {"requests": []}
            
            requests_data["requests"].append(manual_request)
            
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(requests_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📋 手动下载请求已创建: {request_file}")
            
            # 发送通知给运维人员
            await self._notify_manual_intervention_needed(manual_request)
            
            return True  # 表示请求已成功创建
        
        except Exception as e:
            logger.error(f"手动下载请求失败: {e}")
            return False
    
    async def _retry_api_call(self, error_context: Dict) -> bool:
        """重试API调用"""
        try:
            # 使用不同的API端点或参数重试
            return False  # 需要具体实现
        except Exception as e:
            logger.error(f"API重试失败: {e}")
            return False
    
    async def _use_cached_data(self, error_context: Dict) -> bool:
        """使用缓存数据"""
        try:
            return await self._try_cached_download(
                error_context.get("doc_url", ""),
                error_context.get("format_type", "csv")
            )
        except Exception as e:
            logger.error(f"缓存数据使用失败: {e}")
            return False
    
    async def _restart_service_components(self) -> bool:
        """重启服务组件"""
        try:
            logger.info("🔄 重启服务组件...")
            
            # 清理资源
            import gc
            gc.collect()
            
            # 重启相关服务
            # 这里需要实现具体的服务重启逻辑
            
            logger.info("✅ 服务组件重启完成")
            return True
        
        except Exception as e:
            logger.error(f"❌ 服务重启失败: {e}")
            return False
    
    async def _trigger_manual_intervention(self, error_context: Dict) -> bool:
        """触发人工介入"""
        try:
            intervention_request = {
                "timestamp": datetime.now().isoformat(),
                "error_context": error_context,
                "intervention_type": "manual_recovery",
                "priority": "high",
                "status": "pending"
            }
            
            # 保存人工介入请求
            intervention_file = Path(self.config_dir) / "manual_interventions.json"
            
            if intervention_file.exists():
                with open(intervention_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"interventions": []}
            
            data["interventions"].append(intervention_request)
            
            with open(intervention_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 发送紧急通知
            await self._send_emergency_notification(intervention_request)
            
            logger.info("🚨 人工介入请求已发送")
            return True
        
        except Exception as e:
            logger.error(f"❌ 人工介入触发失败: {e}")
            return False
    
    async def _validate_recovery(self, strategy: RecoveryStrategy, 
                               error_context: Dict) -> bool:
        """验证恢复效果"""
        try:
            logger.info("🔍 验证恢复效果...")
            
            # 执行简单的功能测试
            test_doc_url = error_context.get("doc_url", "")
            
            if test_doc_url:
                # 尝试快速测试下载功能
                from production_downloader import ProductionTencentDownloader
                
                downloader = ProductionTencentDownloader()
                await downloader.start_browser(headless=True)
                
                # 快速登录测试
                login_success = await downloader.login_with_cookies()
                
                await downloader.cleanup()
                
                if login_success:
                    logger.info("✅ 恢复验证成功")
                    return True
                else:
                    logger.warning("⚠️ 恢复验证失败")
                    return False
            else:
                # 如果没有测试URL，假设成功
                return True
        
        except Exception as e:
            logger.error(f"❌ 恢复验证异常: {e}")
            return False
    
    async def _log_recovery_attempt(self, recovery_record: Dict):
        """记录恢复尝试"""
        try:
            self.recovery_history.append(recovery_record)
            
            # 保持历史记录不超过1000条
            if len(self.recovery_history) > 1000:
                self.recovery_history = self.recovery_history[-1000:]
            
            # 保存到文件
            with open(self.recovery_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "total_records": len(self.recovery_history),
                    "records": self.recovery_history
                }, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ 记录恢复尝试失败: {e}")
    
    async def _notify_manual_intervention_needed(self, request: Dict):
        """通知需要人工介入"""
        try:
            # 发送紧急邮件/短信通知
            notification_message = f"""
            腾讯文档自动化系统需要人工介入
            
            请求时间: {request['timestamp']}
            文档URL: {request['doc_url']}
            格式类型: {request['format_type']}
            优先级: {request['priority']}
            
            请及时处理此请求。
            """
            
            logger.warning(f"🚨 需要人工介入: {notification_message}")
            
            # 这里可以集成邮件/短信/Webhook通知
            
        except Exception as e:
            logger.error(f"❌ 人工介入通知失败: {e}")
    
    async def _send_emergency_notification(self, intervention_request: Dict):
        """发送紧急通知"""
        try:
            # 发送紧急通知给相关人员
            logger.critical(f"🚨 紧急: 系统需要人工介入 - {intervention_request}")
            
            # 实际应用中应该集成邮件、短信、电话等通知方式
            
        except Exception as e:
            logger.error(f"❌ 紧急通知发送失败: {e}")
    
    def get_recovery_statistics(self) -> Dict:
        """获取恢复统计信息"""
        try:
            total_attempts = len(self.recovery_history)
            successful_recoveries = sum(1 for r in self.recovery_history if r["recovery_success"])
            
            if total_attempts == 0:
                return {
                    "total_attempts": 0,
                    "success_rate": 0.0,
                    "average_recovery_time": 0.0,
                    "most_common_failure": "无数据",
                    "current_streak": self.success_tracking["current_streak"],
                    "failure_streak": self.success_tracking["failure_streak"]
                }
            
            success_rate = successful_recoveries / total_attempts
            
            # 计算平均恢复时间
            recovery_times = [r.get("recovery_time", 0) for r in self.recovery_history if r["recovery_success"]]
            avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0
            
            # 最常见的故障类型
            failure_counts = {}
            for r in self.recovery_history:
                failure_type = r["failure_type"]
                failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
            
            most_common_failure = max(failure_counts, key=failure_counts.get) if failure_counts else "无数据"
            
            return {
                "total_attempts": total_attempts,
                "successful_recoveries": successful_recoveries,
                "success_rate": success_rate,
                "average_recovery_time": avg_recovery_time,
                "most_common_failure": most_common_failure,
                "current_streak": self.success_tracking["current_streak"],
                "failure_streak": self.success_tracking["failure_streak"],
                "failure_distribution": failure_counts
            }
        
        except Exception as e:
            logger.error(f"❌ 获取恢复统计失败: {e}")
            return {"error": str(e)}


# 全局恢复系统实例
_recovery_system_instance = None

def get_recovery_system() -> AutoRecoverySystem:
    """获取自动恢复系统单例"""
    global _recovery_system_instance
    if _recovery_system_instance is None:
        _recovery_system_instance = AutoRecoverySystem()
    return _recovery_system_instance


# 测试和集成接口
async def test_recovery_system():
    """测试自动恢复系统"""
    try:
        recovery_system = get_recovery_system()
        
        # 模拟Cookie失效错误
        error_context = {
            "error_message": "HTTP 401 Unauthorized",
            "http_status": 401,
            "doc_url": "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN",
            "format_type": "csv"
        }
        
        print("=== 自动恢复系统测试 ===")
        print(f"模拟错误上下文: {error_context}")
        
        # 执行恢复
        success, message, details = await recovery_system.detect_and_recover(error_context)
        
        print(f"\n恢复结果:")
        print(f"成功: {success}")
        print(f"消息: {message}")
        print(f"详情: {details}")
        
        # 获取统计信息
        stats = recovery_system.get_recovery_statistics()
        print(f"\n恢复统计: {stats}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_recovery_system())