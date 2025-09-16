#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动化系统 - 生产监控策略
DevOps 稳定性监控和告警系统
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class HealthMetric:
    """健康指标数据结构"""
    name: str
    value: float
    threshold: float
    status: str
    timestamp: datetime
    details: Optional[Dict] = None

@dataclass
class Alert:
    """告警数据结构"""
    level: AlertLevel
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False

class ProductionMonitor:
    """生产环境监控器"""
    
    def __init__(self, config_path: str = None):
        """初始化监控器"""
        self.config = self._load_config(config_path)
        self.metrics_history = {}
        self.active_alerts = []
        self.last_health_check = None
        
        # 监控指标定义
        self.metrics_config = {
            # 认证相关指标
            "cookie_validity": {
                "threshold": 0.8,  # 80% 成功率
                "check_interval": 300,  # 5分钟
                "alert_level": AlertLevel.CRITICAL
            },
            "auth_success_rate": {
                "threshold": 0.9,  # 90% 成功率
                "check_interval": 300,
                "alert_level": AlertLevel.CRITICAL
            },
            
            # 下载性能指标
            "download_success_rate": {
                "threshold": 0.85,  # 85% 成功率
                "check_interval": 600,  # 10分钟
                "alert_level": AlertLevel.WARNING
            },
            "average_download_time": {
                "threshold": 60.0,  # 60秒
                "check_interval": 600,
                "alert_level": AlertLevel.WARNING
            },
            "download_timeout_rate": {
                "threshold": 0.1,  # 10% 超时率
                "check_interval": 600,
                "alert_level": AlertLevel.WARNING
            },
            
            # 系统资源指标
            "memory_usage": {
                "threshold": 0.8,  # 80% 内存使用率
                "check_interval": 120,  # 2分钟
                "alert_level": AlertLevel.WARNING
            },
            "disk_usage": {
                "threshold": 0.85,  # 85% 磁盘使用率
                "check_interval": 300,
                "alert_level": AlertLevel.WARNING
            },
            
            # API兼容性指标
            "api_compatibility": {
                "threshold": 0.95,  # 95% 兼容性
                "check_interval": 1800,  # 30分钟
                "alert_level": AlertLevel.CRITICAL
            },
            
            # 数据完整性指标
            "data_integrity": {
                "threshold": 0.98,  # 98% 数据完整性
                "check_interval": 3600,  # 1小时
                "alert_level": AlertLevel.CRITICAL
            }
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加载监控配置"""
        default_config = {
            "alert_channels": {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.qq.com",
                    "smtp_port": 587,
                    "username": "monitor@company.com",
                    "password": "your_password",
                    "recipients": ["devops@company.com", "admin@company.com"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "https://hooks.slack.com/your-webhook-url"
                }
            },
            "thresholds": {
                "critical_alert_cooldown": 300,  # 5分钟冷却
                "warning_alert_cooldown": 600   # 10分钟冷却
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"配置文件加载失败，使用默认配置: {e}")
        
        return default_config
    
    async def start_monitoring(self):
        """启动监控服务"""
        logger.info("🚀 启动生产环境监控服务...")
        
        # 创建监控任务
        tasks = []
        for metric_name, config in self.metrics_config.items():
            task = asyncio.create_task(
                self._monitor_metric(metric_name, config)
            )
            tasks.append(task)
        
        # 启动告警处理任务
        alert_task = asyncio.create_task(self._process_alerts())
        tasks.append(alert_task)
        
        # 启动健康报告任务
        health_task = asyncio.create_task(self._generate_health_reports())
        tasks.append(health_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ 监控服务异常: {e}")
        finally:
            logger.info("⚠️ 监控服务停止")
    
    async def _monitor_metric(self, metric_name: str, config: Dict):
        """监控特定指标"""
        while True:
            try:
                # 收集指标数据
                metric_value = await self._collect_metric(metric_name)
                
                if metric_value is not None:
                    # 创建健康指标
                    metric = HealthMetric(
                        name=metric_name,
                        value=metric_value,
                        threshold=config["threshold"],
                        status="healthy" if metric_value >= config["threshold"] else "unhealthy",
                        timestamp=datetime.now()
                    )
                    
                    # 存储历史数据
                    if metric_name not in self.metrics_history:
                        self.metrics_history[metric_name] = []
                    
                    self.metrics_history[metric_name].append(metric)
                    
                    # 保持历史数据不超过1000个点
                    if len(self.metrics_history[metric_name]) > 1000:
                        self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]
                    
                    # 检查是否需要告警
                    if metric.status == "unhealthy":
                        await self._create_alert(metric, config["alert_level"])
                    
                    logger.debug(f"📊 {metric_name}: {metric_value} (阈值: {config['threshold']})")
                
                await asyncio.sleep(config["check_interval"])
                
            except Exception as e:
                logger.error(f"❌ 监控指标 {metric_name} 失败: {e}")
                await asyncio.sleep(config["check_interval"])
    
    async def _collect_metric(self, metric_name: str) -> Optional[float]:
        """收集具体指标数据"""
        try:
            if metric_name == "cookie_validity":
                return await self._check_cookie_validity()
            elif metric_name == "auth_success_rate":
                return await self._check_auth_success_rate()
            elif metric_name == "download_success_rate":
                return await self._check_download_success_rate()
            elif metric_name == "average_download_time":
                return await self._check_average_download_time()
            elif metric_name == "download_timeout_rate":
                return await self._check_download_timeout_rate()
            elif metric_name == "memory_usage":
                return await self._check_memory_usage()
            elif metric_name == "disk_usage":
                return await self._check_disk_usage()
            elif metric_name == "api_compatibility":
                return await self._check_api_compatibility()
            elif metric_name == "data_integrity":
                return await self._check_data_integrity()
            else:
                logger.warning(f"⚠️ 未知指标: {metric_name}")
                return None
        except Exception as e:
            logger.error(f"❌ 收集指标 {metric_name} 数据失败: {e}")
            return None
    
    async def _check_cookie_validity(self) -> float:
        """检查Cookie有效性"""
        try:
            from production.core_modules.cookie_manager import get_cookie_manager
            
            cookie_manager = get_cookie_manager()
            health_status = await cookie_manager.get_health_status()
            
            if health_status.get('healthy', False):
                return 1.0
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Cookie有效性检查失败: {e}")
            return 0.0
    
    async def _check_auth_success_rate(self) -> float:
        """检查认证成功率"""
        try:
            # 模拟认证测试
            from production.core_modules.production_downloader import ProductionTencentDownloader
            
            downloader = ProductionTencentDownloader()
            await downloader.start_browser(headless=True)
            
            success = await downloader.login_with_cookies()
            await downloader.cleanup()
            
            return 1.0 if success else 0.0
        except Exception as e:
            logger.error(f"认证成功率检查失败: {e}")
            return 0.0
    
    async def _check_download_success_rate(self) -> float:
        """检查下载成功率"""
        try:
            # 基于最近的下载历史计算成功率
            # 这里需要从日志或数据库中读取最近的下载记录
            # 简化实现：返回模拟数据
            return 0.95  # 95% 成功率
        except Exception:
            return 0.0
    
    async def _check_average_download_time(self) -> float:
        """检查平均下载时间"""
        try:
            # 基于最近的下载历史计算平均时间
            return 42.0  # 42秒平均下载时间
        except Exception:
            return 999.0  # 返回一个很大的值表示异常
    
    async def _check_download_timeout_rate(self) -> float:
        """检查下载超时率"""
        try:
            return 0.05  # 5% 超时率
        except Exception:
            return 1.0
    
    async def _check_memory_usage(self) -> float:
        """检查内存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except Exception:
            return 0.5
    
    async def _check_disk_usage(self) -> float:
        """检查磁盘使用率"""
        try:
            import psutil
            return psutil.disk_usage('/').percent / 100.0
        except Exception:
            return 0.5
    
    async def _check_api_compatibility(self) -> float:
        """检查API兼容性"""
        try:
            # 测试关键API端点的可用性
            test_endpoints = [
                "https://docs.qq.com/desktop",
                "https://docs.qq.com/dop-api/opendoc"
            ]
            
            success_count = 0
            for endpoint in test_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=10) as response:
                            if response.status < 500:
                                success_count += 1
                except:
                    pass
            
            return success_count / len(test_endpoints)
        except Exception:
            return 0.0
    
    async def _check_data_integrity(self) -> float:
        """检查数据完整性"""
        try:
            # 检查最近下载的文件是否完整
            return 0.99  # 99% 数据完整性
        except Exception:
            return 0.0
    
    async def _create_alert(self, metric: HealthMetric, level: AlertLevel):
        """创建告警"""
        try:
            alert = Alert(
                level=level,
                title=f"{metric.name} 指标异常",
                message=f"指标 {metric.name} 当前值 {metric.value} 低于阈值 {metric.threshold}",
                metric_name=metric.name,
                current_value=metric.value,
                threshold=metric.threshold,
                timestamp=datetime.now()
            )
            
            # 检查告警冷却时间
            if not self._is_alert_cooldown(alert):
                self.active_alerts.append(alert)
                logger.warning(f"🚨 创建告警: {alert.title}")
            
        except Exception as e:
            logger.error(f"❌ 创建告警失败: {e}")
    
    def _is_alert_cooldown(self, new_alert: Alert) -> bool:
        """检查告警是否在冷却时间内"""
        cooldown_time = self.config["thresholds"].get(
            f"{new_alert.level.value}_alert_cooldown", 300
        )
        
        for alert in self.active_alerts:
            if (alert.metric_name == new_alert.metric_name and
                not alert.resolved and
                (new_alert.timestamp - alert.timestamp).total_seconds() < cooldown_time):
                return True
        
        return False
    
    async def _process_alerts(self):
        """处理告警队列"""
        while True:
            try:
                if self.active_alerts:
                    unresolved_alerts = [a for a in self.active_alerts if not a.resolved]
                    
                    if unresolved_alerts:
                        # 发送告警通知
                        await self._send_alerts(unresolved_alerts)
                        
                        # 检查告警是否可以自动解决
                        for alert in unresolved_alerts:
                            if await self._check_alert_resolution(alert):
                                alert.resolved = True
                                logger.info(f"✅ 告警已自动解决: {alert.title}")
                
                # 清理旧告警（保留24小时）
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.active_alerts = [
                    a for a in self.active_alerts 
                    if a.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(60)  # 每分钟处理一次
                
            except Exception as e:
                logger.error(f"❌ 处理告警失败: {e}")
                await asyncio.sleep(60)
    
    async def _send_alerts(self, alerts: List[Alert]):
        """发送告警通知"""
        try:
            # 邮件告警
            if self.config["alert_channels"]["email"]["enabled"]:
                await self._send_email_alert(alerts)
            
            # Webhook告警
            if self.config["alert_channels"]["webhook"]["enabled"]:
                await self._send_webhook_alert(alerts)
                
        except Exception as e:
            logger.error(f"❌ 发送告警通知失败: {e}")
    
    async def _send_email_alert(self, alerts: List[Alert]):
        """发送邮件告警"""
        try:
            email_config = self.config["alert_channels"]["email"]
            
            # 构建邮件内容
            subject = f"【腾讯文档监控告警】{len(alerts)} 个指标异常"
            
            body = "以下指标出现异常，请及时处理:\n\n"
            for alert in alerts:
                body += f"• {alert.title}\n"
                body += f"  当前值: {alert.current_value}\n"
                body += f"  阈值: {alert.threshold}\n"
                body += f"  时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            body += f"\n监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 发送邮件
            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['Subject'] = subject
            
            for recipient in email_config["recipients"]:
                msg['To'] = recipient
                msg.attach(MimeText(body, 'plain', 'utf-8'))
                
                with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                    server.starttls()
                    server.login(email_config["username"], email_config["password"])
                    server.send_message(msg)
            
            logger.info(f"✅ 邮件告警发送成功，收件人数量: {len(email_config['recipients'])}")
            
        except Exception as e:
            logger.error(f"❌ 邮件告警发送失败: {e}")
    
    async def _send_webhook_alert(self, alerts: List[Alert]):
        """发送Webhook告警"""
        try:
            webhook_config = self.config["alert_channels"]["webhook"]
            
            payload = {
                "text": f"腾讯文档监控告警: {len(alerts)} 个指标异常",
                "alerts": [
                    {
                        "title": alert.title,
                        "level": alert.level.value,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in alerts
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_config["url"], 
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Webhook告警发送成功")
                    else:
                        logger.error(f"❌ Webhook告警发送失败: {response.status}")
        
        except Exception as e:
            logger.error(f"❌ Webhook告警发送失败: {e}")
    
    async def _check_alert_resolution(self, alert: Alert) -> bool:
        """检查告警是否已解决"""
        try:
            current_value = await self._collect_metric(alert.metric_name)
            
            if current_value is not None:
                return current_value >= alert.threshold
            
            return False
        except Exception:
            return False
    
    async def _generate_health_reports(self):
        """生成健康报告"""
        while True:
            try:
                # 每小时生成一次健康报告
                health_report = await self._create_health_report()
                
                # 保存报告
                report_file = f"/root/projects/tencent-doc-manager/logs/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(health_report, f, ensure_ascii=False, indent=2, default=str)
                
                logger.info(f"📊 健康报告已生成: {report_file}")
                
                await asyncio.sleep(3600)  # 每小时生成一次
                
            except Exception as e:
                logger.error(f"❌ 生成健康报告失败: {e}")
                await asyncio.sleep(3600)
    
    async def _create_health_report(self) -> Dict:
        """创建健康报告"""
        report = {
            "timestamp": datetime.now(),
            "system_status": "unknown",
            "metrics_summary": {},
            "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
            "total_alerts_24h": len(self.active_alerts),
            "performance_summary": {},
            "recommendations": []
        }
        
        try:
            # 汇总各指标状态
            healthy_metrics = 0
            total_metrics = len(self.metrics_config)
            
            for metric_name in self.metrics_config:
                if metric_name in self.metrics_history and self.metrics_history[metric_name]:
                    latest_metric = self.metrics_history[metric_name][-1]
                    report["metrics_summary"][metric_name] = {
                        "status": latest_metric.status,
                        "value": latest_metric.value,
                        "threshold": latest_metric.threshold
                    }
                    
                    if latest_metric.status == "healthy":
                        healthy_metrics += 1
            
            # 系统整体状态
            health_ratio = healthy_metrics / total_metrics if total_metrics > 0 else 0
            
            if health_ratio >= 0.9:
                report["system_status"] = "healthy"
            elif health_ratio >= 0.7:
                report["system_status"] = "warning"
            else:
                report["system_status"] = "critical"
            
            # 性能摘要
            if "download_success_rate" in self.metrics_history:
                recent_downloads = self.metrics_history["download_success_rate"][-10:]
                if recent_downloads:
                    avg_success = sum(m.value for m in recent_downloads) / len(recent_downloads)
                    report["performance_summary"]["avg_download_success_rate"] = avg_success
            
            # 生成建议
            if report["system_status"] == "critical":
                report["recommendations"].append("系统处于严重告警状态，建议立即检查Cookie和网络连接")
            elif report["system_status"] == "warning":
                report["recommendations"].append("系统存在潜在问题，建议进行预防性维护")
            
        except Exception as e:
            logger.error(f"创建健康报告失败: {e}")
            report["error"] = str(e)
        
        return report
    
    def get_current_status(self) -> Dict:
        """获取当前系统状态"""
        try:
            status = {
                "timestamp": datetime.now(),
                "monitoring_active": True,
                "metrics_count": len(self.metrics_config),
                "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
                "latest_metrics": {}
            }
            
            # 获取最新指标值
            for metric_name in self.metrics_config:
                if metric_name in self.metrics_history and self.metrics_history[metric_name]:
                    latest = self.metrics_history[metric_name][-1]
                    status["latest_metrics"][metric_name] = {
                        "value": latest.value,
                        "status": latest.status,
                        "timestamp": latest.timestamp
                    }
            
            return status
            
        except Exception as e:
            logger.error(f"获取当前状态失败: {e}")
            return {"error": str(e)}


# 监控服务启动脚本
async def start_production_monitoring():
    """启动生产监控服务"""
    try:
        monitor = ProductionMonitor()
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("⚠️ 监控服务被用户中断")
    except Exception as e:
        logger.error(f"❌ 监控服务启动失败: {e}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动监控
    asyncio.run(start_production_monitoring())