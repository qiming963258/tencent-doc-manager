#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控工具 - 监控系统资源使用和性能指标
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List
from dataclasses import dataclass, asdict
from browser_pool import get_browser_pool


@dataclass
class PerformanceMetrics:
    """性能指标数据"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    browser_instances: int
    active_tasks: int


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, interval=5):
        self.interval = interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 720  # 保留1小时的数据（5秒间隔）
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._task = None
        
    async def start(self):
        """开始监控"""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        self.logger.info("性能监控器已启动")
        
    async def stop(self):
        """停止监控"""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("性能监控器已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        
        while self._running:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_info = psutil.virtual_memory()
                
                # 磁盘IO
                current_disk_io = psutil.disk_io_counters()
                disk_read_delta = current_disk_io.read_bytes - last_disk_io.read_bytes
                disk_write_delta = current_disk_io.write_bytes - last_disk_io.write_bytes
                last_disk_io = current_disk_io
                
                # 网络IO
                current_network_io = psutil.net_io_counters()
                network_sent_delta = current_network_io.bytes_sent - last_network_io.bytes_sent
                network_recv_delta = current_network_io.bytes_recv - last_network_io.bytes_recv
                last_network_io = current_network_io
                
                # 浏览器池状态
                browser_instances = 0
                active_tasks = 0
                try:
                    browser_pool = await get_browser_pool()
                    stats = await browser_pool.get_pool_stats()
                    browser_instances = stats.get('total_instances', 0)
                    active_tasks = stats.get('in_use', 0)
                except:
                    pass
                
                # 创建性能指标
                metrics = PerformanceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_info.used / 1024 / 1024,
                    memory_percent=memory_info.percent,
                    disk_io_read=disk_read_delta,
                    disk_io_write=disk_write_delta,
                    network_sent=network_sent_delta,
                    network_recv=network_recv_delta,
                    browser_instances=browser_instances,
                    active_tasks=active_tasks
                )
                
                # 添加到历史记录
                self.metrics_history.append(metrics)
                
                # 保持历史记录大小
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                # 检查是否需要警告
                await self._check_alerts(metrics)
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(self.interval)
    
    async def _check_alerts(self, metrics: PerformanceMetrics):
        """检查告警条件"""
        alerts = []
        
        # CPU使用率告警
        if metrics.cpu_percent > 90:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        
        # 内存使用率告警
        if metrics.memory_percent > 85:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}% ({metrics.memory_mb:.0f}MB)")
        
        # 浏览器实例告警
        if metrics.browser_instances > 5:
            alerts.append(f"浏览器实例过多: {metrics.browser_instances}")
        
        # 记录告警
        for alert in alerts:
            self.logger.warning(f"性能告警: {alert}")
    
    def get_current_metrics(self) -> Dict:
        """获取当前指标"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        return asdict(latest)
    
    def get_metrics_summary(self, duration_minutes=10) -> Dict:
        """获取指定时间段的指标摘要"""
        if not self.metrics_history:
            return {}
        
        # 计算时间范围
        end_time = time.time()
        start_time = end_time - (duration_minutes * 60)
        
        # 过滤指标
        relevant_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= start_time
        ]
        
        if not relevant_metrics:
            return {}
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in relevant_metrics]
        memory_values = [m.memory_mb for m in relevant_metrics]
        memory_percent_values = [m.memory_percent for m in relevant_metrics]
        
        return {
            "duration_minutes": duration_minutes,
            "sample_count": len(relevant_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values),
                "avg_percent": sum(memory_percent_values) / len(memory_percent_values),
                "max_percent": max(memory_percent_values)
            },
            "browser_instances": {
                "max": max(m.browser_instances for m in relevant_metrics),
                "avg": sum(m.browser_instances for m in relevant_metrics) / len(relevant_metrics)
            },
            "active_tasks": {
                "max": max(m.active_tasks for m in relevant_metrics),
                "avg": sum(m.active_tasks for m in relevant_metrics) / len(relevant_metrics)
            }
        }
    
    def export_metrics_to_file(self, filepath: str, duration_minutes=60):
        """导出指标到文件"""
        import json
        
        end_time = time.time()
        start_time = end_time - (duration_minutes * 60)
        
        relevant_metrics = [
            asdict(m) for m in self.metrics_history
            if m.timestamp >= start_time
        ]
        
        export_data = {
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": duration_minutes,
            "metrics_count": len(relevant_metrics),
            "summary": self.get_metrics_summary(duration_minutes),
            "metrics": relevant_metrics
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"性能指标已导出到: {filepath}")


# 全局监控器实例
_performance_monitor = None

async def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start()
    return _performance_monitor

async def cleanup_performance_monitor():
    """清理性能监控器"""
    global _performance_monitor
    if _performance_monitor:
        await _performance_monitor.stop()
        _performance_monitor = None


async def main():
    """测试监控器"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    monitor = await get_performance_monitor()
    
    try:
        print("性能监控器运行中，按 Ctrl+C 停止...")
        
        # 运行60秒
        for i in range(12):
            await asyncio.sleep(5)
            current = monitor.get_current_metrics()
            print(f"CPU: {current.get('cpu_percent', 0):.1f}%, "
                  f"内存: {current.get('memory_mb', 0):.0f}MB "
                  f"({current.get('memory_percent', 0):.1f}%)")
        
        # 显示摘要
        summary = monitor.get_metrics_summary(1)  # 1分钟摘要
        print("\n=== 性能摘要 ===")
        print(f"CPU平均: {summary['cpu']['avg']:.1f}%, 最高: {summary['cpu']['max']:.1f}%")
        print(f"内存平均: {summary['memory']['avg_mb']:.0f}MB ({summary['memory']['avg_percent']:.1f}%)")
        
        # 导出指标
        monitor.export_metrics_to_file("performance_metrics.json", 1)
        
    finally:
        await cleanup_performance_monitor()


if __name__ == "__main__":
    asyncio.run(main())