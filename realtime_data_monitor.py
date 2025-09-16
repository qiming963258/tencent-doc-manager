#!/usr/bin/env python3
"""
实时数据流监控系统
监控整个数据处理管道，防止数据丢失、错位和传递异常
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class MonitoringAlert:
    """监控告警数据结构"""
    timestamp: str
    alert_type: str
    severity: str  # LOW/MEDIUM/HIGH/CRITICAL
    stage: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False

@dataclass
class PipelineMetrics:
    """管道指标数据结构"""
    timestamp: str
    stage: str
    input_count: int
    output_count: int
    processing_time: float
    success_rate: float
    data_integrity: float
    errors: List[str]

class DataFlowMonitor:
    """实时数据流监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化监控器
        
        Args:
            config: 监控配置
        """
        self.config = config or self._get_default_config()
        self.alerts = deque(maxlen=1000)  # 保存最近1000个告警
        self.metrics_history = deque(maxlen=5000)  # 保存最近5000个指标
        self.is_monitoring = False
        self.monitor_thread = None
        self.alert_callbacks = []
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 监控阈值
        self.thresholds = self.config.get("thresholds", {
            "min_column_coverage": 0.8,      # 最低80%列覆盖率
            "max_data_loss_rate": 0.1,       # 最高10%数据丢失率
            "min_visible_hotspots": 1,       # 至少1个可见热点
            "max_processing_time": 30.0,     # 最大处理时间30秒
            "min_success_rate": 0.95         # 最小成功率95%
        })
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认监控配置"""
        return {
            "monitoring_interval": 5.0,  # 监控间隔5秒
            "alert_retention_hours": 24,  # 告警保留24小时
            "metrics_retention_hours": 48,  # 指标保留48小时
            "enable_realtime_alerts": True,
            "alert_channels": ["console", "file"],
            "thresholds": {
                "min_column_coverage": 0.8,
                "max_data_loss_rate": 0.1,
                "min_visible_hotspots": 1,
                "max_processing_time": 30.0,
                "min_success_rate": 0.95
            }
        }
    
    def start_monitoring(self):
        """启动实时监控"""
        if self.is_monitoring:
            self.logger.warning("监控已经在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("🟢 实时数据流监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("🔴 实时数据流监控已停止")
    
    def _monitoring_loop(self):
        """监控主循环"""
        while self.is_monitoring:
            try:
                # 清理过期数据
                self._cleanup_expired_data()
                
                # 检查系统健康状态
                self._check_system_health()
                
                # 等待下一次监控周期
                time.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")
                time.sleep(1)  # 错误时短暂等待
    
    def record_stage_metrics(self, 
                           stage: str,
                           input_count: int,
                           output_count: int, 
                           processing_time: float,
                           success: bool = True,
                           errors: List[str] = None,
                           additional_data: Dict[str, Any] = None) -> bool:
        """
        记录阶段处理指标
        
        Args:
            stage: 处理阶段名称
            input_count: 输入数据量
            output_count: 输出数据量  
            processing_time: 处理时间
            success: 是否成功
            errors: 错误列表
            additional_data: 附加数据
        
        Returns:
            bool: 是否触发告警
        """
        
        timestamp = datetime.now().isoformat()
        
        # 计算数据完整性
        data_integrity = min(1.0, output_count / input_count) if input_count > 0 else 1.0
        
        # 创建指标记录
        metrics = PipelineMetrics(
            timestamp=timestamp,
            stage=stage,
            input_count=input_count,
            output_count=output_count,
            processing_time=processing_time,
            success_rate=1.0 if success else 0.0,
            data_integrity=data_integrity,
            errors=errors or []
        )
        
        # 保存指标
        self.metrics_history.append(metrics)
        
        # 检查是否需要告警
        alerts_triggered = self._check_stage_thresholds(metrics, additional_data or {})
        
        return len(alerts_triggered) > 0
    
    def _check_stage_thresholds(self, metrics: PipelineMetrics, additional_data: Dict[str, Any]) -> List[MonitoringAlert]:
        """检查阶段指标是否超出阈值"""
        
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # 检查数据完整性
        if metrics.data_integrity < (1.0 - self.thresholds["max_data_loss_rate"]):
            alert = MonitoringAlert(
                timestamp=timestamp,
                alert_type="data_integrity_low",
                severity="HIGH",
                stage=metrics.stage,
                message=f"数据完整性过低: {metrics.data_integrity:.1%}",
                details={
                    "threshold": 1.0 - self.thresholds["max_data_loss_rate"],
                    "actual": metrics.data_integrity,
                    "input_count": metrics.input_count,
                    "output_count": metrics.output_count
                }
            )
            alerts.append(alert)
        
        # 检查处理时间
        if metrics.processing_time > self.thresholds["max_processing_time"]:
            alert = MonitoringAlert(
                timestamp=timestamp,
                alert_type="processing_time_high",
                severity="MEDIUM",
                stage=metrics.stage,
                message=f"处理时间过长: {metrics.processing_time:.2f}秒",
                details={
                    "threshold": self.thresholds["max_processing_time"],
                    "actual": metrics.processing_time
                }
            )
            alerts.append(alert)
        
        # 检查列覆盖率（仅对智能映射阶段）
        if metrics.stage == "intelligent_mapping" and "column_coverage" in additional_data:
            coverage = additional_data["column_coverage"]
            if coverage < self.thresholds["min_column_coverage"]:
                alert = MonitoringAlert(
                    timestamp=timestamp,
                    alert_type="column_coverage_low",
                    severity="HIGH",
                    stage=metrics.stage,
                    message=f"列映射覆盖率过低: {coverage:.1%}",
                    details={
                        "threshold": self.thresholds["min_column_coverage"],
                        "actual": coverage,
                        "unmapped_columns": additional_data.get("unmapped_columns", [])
                    }
                )
                alerts.append(alert)
        
        # 检查可见热点数量（仅对热力图生成阶段）
        if metrics.stage == "heatmap_generation" and "visible_hotspots" in additional_data:
            hotspots = additional_data["visible_hotspots"]
            if hotspots < self.thresholds["min_visible_hotspots"]:
                alert = MonitoringAlert(
                    timestamp=timestamp,
                    alert_type="hotspots_insufficient",
                    severity="MEDIUM",
                    stage=metrics.stage,
                    message=f"可见热点数量不足: {hotspots}个",
                    details={
                        "threshold": self.thresholds["min_visible_hotspots"],
                        "actual": hotspots,
                        "expected": metrics.input_count
                    }
                )
                alerts.append(alert)
        
        # 检查错误
        if metrics.errors:
            alert = MonitoringAlert(
                timestamp=timestamp,
                alert_type="stage_errors",
                severity="HIGH" if len(metrics.errors) > 1 else "MEDIUM",
                stage=metrics.stage,
                message=f"阶段处理出现{len(metrics.errors)}个错误",
                details={
                    "error_count": len(metrics.errors),
                    "errors": metrics.errors
                }
            )
            alerts.append(alert)
        
        # 触发告警
        for alert in alerts:
            self._trigger_alert(alert)
        
        return alerts
    
    def _trigger_alert(self, alert: MonitoringAlert):
        """触发告警"""
        
        # 保存告警
        self.alerts.append(alert)
        
        # 输出到控制台
        if "console" in self.config.get("alert_channels", []):
            severity_icon = {
                "LOW": "🟡",
                "MEDIUM": "🟠", 
                "HIGH": "🔴",
                "CRITICAL": "💀"
            }.get(alert.severity, "⚪")
            
            print(f"{severity_icon} [{alert.severity}] {alert.stage}: {alert.message}")
        
        # 写入文件
        if "file" in self.config.get("alert_channels", []):
            self._write_alert_to_file(alert)
        
        # 调用注册的回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {str(e)}")
    
    def _write_alert_to_file(self, alert: MonitoringAlert):
        """写入告警到文件"""
        
        alert_file = "/root/projects/tencent-doc-manager/monitoring_alerts.jsonl"
        
        try:
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(alert), ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"写入告警文件失败: {str(e)}")
    
    def _check_system_health(self):
        """检查系统整体健康状态"""
        
        if not self.metrics_history:
            return
        
        # 检查最近的成功率
        recent_metrics = [m for m in self.metrics_history 
                         if datetime.fromisoformat(m.timestamp) > datetime.now() - timedelta(minutes=10)]
        
        if recent_metrics:
            avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
            
            if avg_success_rate < self.thresholds["min_success_rate"]:
                alert = MonitoringAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="system_health_degraded",
                    severity="CRITICAL",
                    stage="system",
                    message=f"系统成功率降低: {avg_success_rate:.1%}",
                    details={
                        "threshold": self.thresholds["min_success_rate"],
                        "actual": avg_success_rate,
                        "sample_size": len(recent_metrics)
                    }
                )
                self._trigger_alert(alert)
    
    def _cleanup_expired_data(self):
        """清理过期数据"""
        
        now = datetime.now()
        
        # 清理过期告警
        alert_cutoff = now - timedelta(hours=self.config["alert_retention_hours"])
        self.alerts = deque([a for a in self.alerts 
                           if datetime.fromisoformat(a.timestamp) > alert_cutoff], 
                          maxlen=1000)
        
        # 清理过期指标
        metrics_cutoff = now - timedelta(hours=self.config["metrics_retention_hours"])
        self.metrics_history = deque([m for m in self.metrics_history 
                                    if datetime.fromisoformat(m.timestamp) > metrics_cutoff], 
                                   maxlen=5000)
    
    def add_alert_callback(self, callback: Callable[[MonitoringAlert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前监控状态"""
        
        if not self.metrics_history:
            return {
                "status": "no_data",
                "monitoring": self.is_monitoring
            }
        
        recent_metrics = [m for m in self.metrics_history 
                         if datetime.fromisoformat(m.timestamp) > datetime.now() - timedelta(minutes=30)]
        
        if not recent_metrics:
            return {
                "status": "stale_data",
                "monitoring": self.is_monitoring,
                "last_update": self.metrics_history[-1].timestamp if self.metrics_history else None
            }
        
        # 计算整体健康指标
        avg_data_integrity = sum(m.data_integrity for m in recent_metrics) / len(recent_metrics)
        avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
        avg_processing_time = sum(m.processing_time for m in recent_metrics) / len(recent_metrics)
        
        # 统计未解决告警
        recent_alerts = [a for a in self.alerts 
                        if not a.resolved and 
                        datetime.fromisoformat(a.timestamp) > datetime.now() - timedelta(hours=1)]
        
        status = "healthy"
        if any(a.severity in ["CRITICAL", "HIGH"] for a in recent_alerts):
            status = "critical"
        elif any(a.severity == "MEDIUM" for a in recent_alerts):
            status = "warning"
        
        return {
            "status": status,
            "monitoring": self.is_monitoring,
            "last_update": recent_metrics[-1].timestamp,
            "metrics": {
                "data_integrity": avg_data_integrity,
                "success_rate": avg_success_rate,
                "avg_processing_time": avg_processing_time,
                "sample_size": len(recent_metrics)
            },
            "alerts": {
                "total": len(recent_alerts),
                "critical": len([a for a in recent_alerts if a.severity == "CRITICAL"]),
                "high": len([a for a in recent_alerts if a.severity == "HIGH"]),
                "medium": len([a for a in recent_alerts if a.severity == "MEDIUM"]),
                "low": len([a for a in recent_alerts if a.severity == "LOW"])
            }
        }
    
    def generate_monitoring_report(self, output_file: str = None) -> Dict[str, Any]:
        """生成监控报告"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_period": {
                "start": self.metrics_history[0].timestamp if self.metrics_history else None,
                "end": self.metrics_history[-1].timestamp if self.metrics_history else None,
                "duration_hours": 24 if self.metrics_history else 0
            },
            "system_status": self.get_current_status(),
            "metrics_summary": self._generate_metrics_summary(),
            "alert_summary": self._generate_alert_summary(),
            "recommendations": self._generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📊 监控报告已保存: {output_file}")
        
        return report
    
    def _generate_metrics_summary(self) -> Dict[str, Any]:
        """生成指标摘要"""
        
        if not self.metrics_history:
            return {"no_data": True}
        
        # 按阶段分组
        stage_metrics = {}
        for metric in self.metrics_history:
            if metric.stage not in stage_metrics:
                stage_metrics[metric.stage] = []
            stage_metrics[metric.stage].append(metric)
        
        summary = {}
        for stage, metrics in stage_metrics.items():
            summary[stage] = {
                "total_operations": len(metrics),
                "avg_data_integrity": sum(m.data_integrity for m in metrics) / len(metrics),
                "avg_processing_time": sum(m.processing_time for m in metrics) / len(metrics),
                "success_rate": sum(m.success_rate for m in metrics) / len(metrics),
                "total_errors": sum(len(m.errors) for m in metrics)
            }
        
        return summary
    
    def _generate_alert_summary(self) -> Dict[str, Any]:
        """生成告警摘要"""
        
        if not self.alerts:
            return {"total_alerts": 0}
        
        # 按类型和严重程度统计
        alert_types = {}
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        
        for alert in self.alerts:
            if alert.alert_type not in alert_types:
                alert_types[alert.alert_type] = 0
            alert_types[alert.alert_type] += 1
            severity_counts[alert.severity] += 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_type": alert_types,
            "by_severity": severity_counts,
            "unresolved": len([a for a in self.alerts if not a.resolved])
        }
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于告警历史生成建议
        recent_alerts = [a for a in self.alerts 
                        if datetime.fromisoformat(a.timestamp) > datetime.now() - timedelta(hours=24)]
        
        if any(a.alert_type == "data_integrity_low" for a in recent_alerts):
            recommendations.append({
                "priority": "HIGH",
                "category": "数据完整性",
                "action": "检查映射算法配置",
                "description": "数据完整性告警频发，建议检查列映射词典和强度计算配置"
            })
        
        if any(a.alert_type == "processing_time_high" for a in recent_alerts):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "性能优化",
                "action": "优化处理算法",
                "description": "处理时间过长，建议优化高斯平滑或矩阵计算算法"
            })
        
        if any(a.alert_type == "column_coverage_low" for a in recent_alerts):
            recommendations.append({
                "priority": "HIGH",
                "category": "映射算法",
                "action": "扩展语义词典",
                "description": "列映射覆盖率低，建议扩展智能映射算法的关键词库"
            })
        
        return recommendations

def test_monitoring_system():
    """测试监控系统"""
    
    print("🧪 测试实时数据流监控系统")
    print("=" * 50)
    
    # 创建监控器
    monitor = DataFlowMonitor()
    
    # 添加告警回调
    def alert_handler(alert: MonitoringAlert):
        print(f"📢 告警处理器收到: {alert.alert_type} - {alert.message}")
    
    monitor.add_alert_callback(alert_handler)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 模拟一些指标记录
    print("\n📊 模拟数据处理流程...")
    
    # 正常处理
    monitor.record_stage_metrics(
        stage="csv_comparison",
        input_count=5,
        output_count=5,
        processing_time=2.5,
        success=True
    )
    
    # 映射阶段 - 触发覆盖率告警
    monitor.record_stage_metrics(
        stage="intelligent_mapping", 
        input_count=5,
        output_count=3,
        processing_time=8.0,
        success=True,
        additional_data={
            "column_coverage": 0.6,  # 低于0.8阈值
            "unmapped_columns": ["工资", "部门"]
        }
    )
    
    # 热力图生成 - 触发热点不足告警
    monitor.record_stage_metrics(
        stage="heatmap_generation",
        input_count=3,
        output_count=1,
        processing_time=15.0,
        success=True,
        additional_data={
            "visible_hotspots": 0  # 低于1的阈值
        }
    )
    
    # 等待监控处理
    time.sleep(2)
    
    # 获取状态
    status = monitor.get_current_status()
    print(f"\n🎯 系统状态: {status['status']}")
    print(f"数据完整性: {status['metrics']['data_integrity']:.1%}")
    print(f"成功率: {status['metrics']['success_rate']:.1%}")
    print(f"未解决告警: {status['alerts']['total']}个")
    
    # 生成报告
    report = monitor.generate_monitoring_report(
        "/root/projects/tencent-doc-manager/monitoring_report.json"
    )
    
    # 停止监控
    monitor.stop_monitoring()
    
    print("\n🎉 监控系统测试完成")
    return monitor

if __name__ == "__main__":
    test_monitoring_system()