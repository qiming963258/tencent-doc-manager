#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动化系统 - 容量规划分析
DevOps 容量评估和扩展策略
"""

import asyncio
import json
import logging
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    concurrent_downloads: int
    avg_download_time: float
    success_rate: float
    queue_length: int

@dataclass
class CapacityLimits:
    """容量限制"""
    max_concurrent_downloads: int
    max_cpu_usage: float
    max_memory_usage: float
    max_disk_io_rate: float
    max_response_time: float
    min_success_rate: float

class CapacityPlanner:
    """容量规划器"""
    
    def __init__(self):
        """初始化容量规划器"""
        self.performance_history = []
        self.capacity_limits = CapacityLimits(
            max_concurrent_downloads=5,  # 基于当前测试结果
            max_cpu_usage=0.8,  # 80% CPU使用率
            max_memory_usage=0.75,  # 75% 内存使用率
            max_disk_io_rate=100.0,  # MB/s
            max_response_time=60.0,  # 60秒最大响应时间
            min_success_rate=0.85  # 85% 最低成功率
        )
        
        # 基于8月28日测试数据的基线
        self.baseline_performance = {
            "single_download_time": 42.0,  # 平均42秒
            "single_download_cpu": 0.15,   # 15% CPU使用率
            "single_download_memory": 0.05, # 5% 内存增长
            "file_size_csv": 71859,        # CSV文件大小
            "file_size_excel": 46335,      # Excel文件大小
            "success_rate": 1.0             # 100% 成功率
        }
    
    def analyze_single_instance_capacity(self) -> Dict[str, any]:
        """分析单实例处理能力"""
        try:
            logger.info("📊 开始单实例容量分析...")
            
            # 获取系统信息
            system_info = self._get_system_info()
            
            # 计算理论最大并发数
            theoretical_max = self._calculate_theoretical_max_concurrency()
            
            # 计算实际安全并发数
            safe_max = self._calculate_safe_max_concurrency()
            
            # 计算资源利用率
            resource_utilization = self._calculate_resource_utilization()
            
            # 计算吞吐量预测
            throughput_analysis = self._analyze_throughput_capacity()
            
            capacity_analysis = {
                "system_info": system_info,
                "capacity_limits": {
                    "theoretical_max_concurrent": theoretical_max,
                    "safe_max_concurrent": safe_max,
                    "recommended_concurrent": min(safe_max, self.capacity_limits.max_concurrent_downloads)
                },
                "resource_analysis": resource_utilization,
                "throughput_analysis": throughput_analysis,
                "bottleneck_analysis": self._identify_bottlenecks(),
                "scaling_recommendations": self._generate_scaling_recommendations(),
                "performance_projections": self._project_performance_under_load()
            }
            
            logger.info("✅ 单实例容量分析完成")
            return capacity_analysis
        
        except Exception as e:
            logger.error(f"❌ 单实例容量分析失败: {e}")
            return {"error": str(e)}
    
    def _get_system_info(self) -> Dict[str, any]:
        """获取系统信息"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free,
                "network_interfaces": list(psutil.net_io_counters(pernic=True).keys()),
                "platform": {
                    "system": os.uname().sysname,
                    "release": os.uname().release,
                    "machine": os.uname().machine
                }
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def _calculate_theoretical_max_concurrency(self) -> int:
        """计算理论最大并发数"""
        try:
            # 基于不同资源维度计算最大并发数
            
            # CPU维度: 假设每个下载任务占用15% CPU
            cpu_cores = psutil.cpu_count()
            cpu_max_concurrent = int((cpu_cores * self.capacity_limits.max_cpu_usage) / 
                                   self.baseline_performance["single_download_cpu"])
            
            # 内存维度: 假设每个下载任务占用5%的可用内存
            available_memory = psutil.virtual_memory().available
            total_memory = psutil.virtual_memory().total
            memory_max_concurrent = int((total_memory * self.capacity_limits.max_memory_usage) / 
                                      (total_memory * self.baseline_performance["single_download_memory"]))
            
            # 网络I/O维度: 基于带宽和文件大小
            avg_file_size = (self.baseline_performance["file_size_csv"] + 
                           self.baseline_performance["file_size_excel"]) / 2
            # 假设100Mbps带宽
            assumed_bandwidth_mbps = 100
            bandwidth_bytes_per_sec = (assumed_bandwidth_mbps * 1024 * 1024) / 8
            download_time = self.baseline_performance["single_download_time"]
            network_max_concurrent = int((bandwidth_bytes_per_sec * download_time) / avg_file_size)
            
            # 取最小值作为理论最大值
            theoretical_max = min(cpu_max_concurrent, memory_max_concurrent, network_max_concurrent)
            
            logger.info(f"理论最大并发计算: CPU={cpu_max_concurrent}, 内存={memory_max_concurrent}, 网络={network_max_concurrent}")
            
            return max(1, theoretical_max)  # 至少1个并发
        
        except Exception as e:
            logger.error(f"理论最大并发计算失败: {e}")
            return 1
    
    def _calculate_safe_max_concurrency(self) -> int:
        """计算安全最大并发数"""
        try:
            # 在理论最大值基础上应用安全系数
            theoretical_max = self._calculate_theoretical_max_concurrency()
            
            # 应用70%安全系数
            safety_factor = 0.7
            safe_max = int(theoretical_max * safety_factor)
            
            # 考虑Cookie管理器的限制（同时只能处理有限数量的会话）
            cookie_session_limit = 3  # 基于当前Cookie管理机制
            
            # 考虑腾讯文档的反爬虫限制
            anti_scraping_limit = 2  # 保守估计，避免触发反爬虫
            
            # 取最小值
            final_safe_max = min(safe_max, cookie_session_limit, anti_scraping_limit)
            
            return max(1, final_safe_max)
        
        except Exception as e:
            logger.error(f"安全最大并发计算失败: {e}")
            return 1
    
    def _calculate_resource_utilization(self) -> Dict[str, any]:
        """计算资源利用率"""
        try:
            current_usage = {
                "cpu_current": psutil.cpu_percent(interval=1),
                "memory_current": psutil.virtual_memory().percent,
                "disk_current": psutil.disk_usage('/').percent
            }
            
            # 预测在不同并发级别下的资源使用
            concurrency_levels = [1, 2, 3, 5, 8, 10]
            resource_projections = {}
            
            for level in concurrency_levels:
                projected_cpu = current_usage["cpu_current"] + (
                    level * self.baseline_performance["single_download_cpu"] * 100
                )
                projected_memory = current_usage["memory_current"] + (
                    level * self.baseline_performance["single_download_memory"] * 100
                )
                
                resource_projections[f"concurrent_{level}"] = {
                    "cpu_usage": min(100, projected_cpu),
                    "memory_usage": min(100, projected_memory),
                    "is_safe": (projected_cpu < self.capacity_limits.max_cpu_usage * 100 and
                              projected_memory < self.capacity_limits.max_memory_usage * 100)
                }
            
            return {
                "current_usage": current_usage,
                "projections": resource_projections,
                "safe_operating_range": {
                    "max_cpu_threshold": self.capacity_limits.max_cpu_usage * 100,
                    "max_memory_threshold": self.capacity_limits.max_memory_usage * 100
                }
            }
        
        except Exception as e:
            logger.error(f"资源利用率计算失败: {e}")
            return {}
    
    def _analyze_throughput_capacity(self) -> Dict[str, any]:
        """分析吞吐量容量"""
        try:
            # 基于当前性能基线计算不同场景下的吞吐量
            
            single_download_time = self.baseline_performance["single_download_time"]
            success_rate = self.baseline_performance["success_rate"]
            
            throughput_scenarios = {}
            
            # 串行处理（1个并发）
            throughput_scenarios["serial"] = {
                "concurrent_downloads": 1,
                "downloads_per_hour": int((3600 / single_download_time) * success_rate),
                "downloads_per_day": int((86400 / single_download_time) * success_rate),
                "avg_response_time": single_download_time
            }
            
            # 并行处理（不同并发级别）
            for concurrent in [2, 3, 5]:
                # 考虑并发开销（每增加1个并发，响应时间增加5%）
                overhead_factor = 1 + (concurrent - 1) * 0.05
                avg_response_time = single_download_time * overhead_factor
                
                # 考虑成功率可能的下降
                concurrent_success_rate = success_rate * (0.98 ** (concurrent - 1))
                
                effective_throughput = (concurrent / avg_response_time) * concurrent_success_rate
                
                throughput_scenarios[f"concurrent_{concurrent}"] = {
                    "concurrent_downloads": concurrent,
                    "downloads_per_hour": int(effective_throughput * 3600),
                    "downloads_per_day": int(effective_throughput * 86400),
                    "avg_response_time": avg_response_time,
                    "success_rate": concurrent_success_rate,
                    "efficiency": effective_throughput / concurrent  # 单线程效率
                }
            
            # 推荐配置
            best_efficiency = max(
                throughput_scenarios.items(),
                key=lambda x: x[1].get("efficiency", 0) if x[0] != "serial" else 0
            )
            
            return {
                "scenarios": throughput_scenarios,
                "recommended_config": {
                    "scenario": best_efficiency[0],
                    "details": best_efficiency[1]
                },
                "peak_throughput": {
                    "max_downloads_per_hour": max(s["downloads_per_hour"] for s in throughput_scenarios.values()),
                    "max_downloads_per_day": max(s["downloads_per_day"] for s in throughput_scenarios.values())
                }
            }
        
        except Exception as e:
            logger.error(f"吞吐量分析失败: {e}")
            return {}
    
    def _identify_bottlenecks(self) -> List[Dict[str, any]]:
        """识别系统瓶颈"""
        try:
            bottlenecks = []
            
            # CPU瓶颈分析
            cpu_cores = psutil.cpu_count()
            if cpu_cores < 4:
                bottlenecks.append({
                    "type": "cpu",
                    "severity": "medium",
                    "description": f"CPU核心数较少 ({cpu_cores}核)，可能影响并发处理能力",
                    "impact": "限制最大并发数到2-3个",
                    "recommendation": "考虑升级到至少4核CPU"
                })
            
            # 内存瓶颈分析
            total_memory_gb = psutil.virtual_memory().total / (1024**3)
            if total_memory_gb < 8:
                bottlenecks.append({
                    "type": "memory",
                    "severity": "high",
                    "description": f"内存容量较小 ({total_memory_gb:.1f}GB)",
                    "impact": "限制并发下载和浏览器实例数量",
                    "recommendation": "建议升级到至少8GB内存"
                })
            
            # 网络带宽瓶颈（基于文件大小和下载时间推测）
            avg_file_size_mb = (self.baseline_performance["file_size_csv"] + 
                               self.baseline_performance["file_size_excel"]) / 2 / (1024**2)
            download_time = self.baseline_performance["single_download_time"]
            estimated_bandwidth_mbps = (avg_file_size_mb * 8) / download_time
            
            if estimated_bandwidth_mbps < 10:  # 低于10Mbps
                bottlenecks.append({
                    "type": "network",
                    "severity": "medium",
                    "description": f"网络带宽可能较低 (估计 {estimated_bandwidth_mbps:.1f}Mbps)",
                    "impact": "影响并发下载性能",
                    "recommendation": "检查网络连接质量，考虑升级带宽"
                })
            
            # Cookie管理瓶颈
            bottlenecks.append({
                "type": "authentication",
                "severity": "high",
                "description": "Cookie管理机制限制了会话并发数",
                "impact": "单Cookie账户限制并发下载数量",
                "recommendation": "实施多Cookie轮转机制或Cookie池"
            })
            
            # 反爬虫限制
            bottlenecks.append({
                "type": "anti_scraping",
                "severity": "high",
                "description": "腾讯文档反爬虫机制限制请求频率",
                "impact": "过高的并发可能导致IP封禁或账户限制",
                "recommendation": "实施请求限流和延迟策略"
            })
            
            return bottlenecks
        
        except Exception as e:
            logger.error(f"瓶颈分析失败: {e}")
            return []
    
    def _generate_scaling_recommendations(self) -> Dict[str, any]:
        """生成扩展建议"""
        try:
            recommendations = {
                "horizontal_scaling": {
                    "description": "增加更多实例来提高整体吞吐量",
                    "strategies": [
                        {
                            "strategy": "多实例部署",
                            "implementation": "使用Docker容器部署多个实例",
                            "pros": ["线性扩展能力", "故障隔离", "负载分散"],
                            "cons": ["需要负载均衡器", "Cookie管理复杂化"],
                            "estimated_cost": "medium"
                        },
                        {
                            "strategy": "分布式队列",
                            "implementation": "使用Redis/RabbitMQ实现任务分发",
                            "pros": ["任务均衡分配", "失败重试机制", "监控便利"],
                            "cons": ["架构复杂化", "新增依赖组件"],
                            "estimated_cost": "high"
                        }
                    ]
                },
                "vertical_scaling": {
                    "description": "提升单实例硬件配置",
                    "strategies": [
                        {
                            "strategy": "CPU升级",
                            "implementation": "升级到8核或更多CPU",
                            "expected_improvement": "并发处理能力提升2-3倍",
                            "estimated_cost": "medium"
                        },
                        {
                            "strategy": "内存升级",
                            "implementation": "升级到16GB或更多内存",
                            "expected_improvement": "支持更多浏览器实例",
                            "estimated_cost": "low"
                        },
                        {
                            "strategy": "SSD存储",
                            "implementation": "使用高速SSD存储",
                            "expected_improvement": "I/O性能提升5-10倍",
                            "estimated_cost": "medium"
                        }
                    ]
                },
                "optimization_strategies": {
                    "description": "软件层面优化策略",
                    "strategies": [
                        {
                            "strategy": "浏览器池化",
                            "implementation": "复用浏览器实例，减少启动开销",
                            "expected_improvement": "响应时间减少30-50%",
                            "difficulty": "medium"
                        },
                        {
                            "strategy": "Cookie池管理",
                            "implementation": "维护多个有效Cookie，轮转使用",
                            "expected_improvement": "并发能力提升3-5倍",
                            "difficulty": "high"
                        },
                        {
                            "strategy": "智能重试机制",
                            "implementation": "基于错误类型的差异化重试策略",
                            "expected_improvement": "成功率提升5-10%",
                            "difficulty": "low"
                        },
                        {
                            "strategy": "缓存机制",
                            "implementation": "缓存最近下载的文档，避免重复下载",
                            "expected_improvement": "减少50-80%重复请求",
                            "difficulty": "medium"
                        }
                    ]
                }
            }
            
            # 基于当前系统状况的推荐优先级
            system_info = self._get_system_info()
            cpu_cores = system_info.get("cpu_count", 1)
            memory_gb = system_info.get("memory_total", 0) / (1024**3)
            
            priority_recommendations = []
            
            if memory_gb < 8:
                priority_recommendations.append("内存升级（高优先级）")
            if cpu_cores < 4:
                priority_recommendations.append("CPU升级（中优先级）")
                
            priority_recommendations.extend([
                "Cookie池管理实现（高优先级）",
                "浏览器池化（中优先级）",
                "智能重试机制（低优先级）"
            ])
            
            recommendations["priority_recommendations"] = priority_recommendations
            
            return recommendations
        
        except Exception as e:
            logger.error(f"扩展建议生成失败: {e}")
            return {}
    
    def _project_performance_under_load(self) -> Dict[str, any]:
        """预测负载下的性能表现"""
        try:
            load_scenarios = {
                "light_load": {"requests_per_hour": 10, "concurrent_avg": 1},
                "medium_load": {"requests_per_hour": 50, "concurrent_avg": 2},
                "heavy_load": {"requests_per_hour": 100, "concurrent_avg": 3},
                "peak_load": {"requests_per_hour": 200, "concurrent_avg": 5}
            }
            
            projections = {}
            
            for scenario_name, scenario in load_scenarios.items():
                requests_per_hour = scenario["requests_per_hour"]
                avg_concurrent = scenario["concurrent_avg"]
                
                # 计算资源使用预测
                cpu_usage = min(100, avg_concurrent * self.baseline_performance["single_download_cpu"] * 100)
                memory_usage = min(100, avg_concurrent * self.baseline_performance["single_download_memory"] * 100)
                
                # 计算响应时间（考虑排队延迟）
                service_rate = 3600 / self.baseline_performance["single_download_time"]  # 每小时处理能力
                if requests_per_hour < service_rate:
                    # 轻负载，无排队
                    avg_response_time = self.baseline_performance["single_download_time"]
                    queue_length = 0
                else:
                    # 重负载，有排队
                    utilization = requests_per_hour / service_rate
                    avg_response_time = self.baseline_performance["single_download_time"] / (1 - utilization)
                    queue_length = (utilization ** 2) / (1 - utilization)
                
                # 计算成功率（负载越高，成功率可能下降）
                success_rate = self.baseline_performance["success_rate"] * (0.95 ** (avg_concurrent - 1))
                
                projections[scenario_name] = {
                    "requests_per_hour": requests_per_hour,
                    "avg_concurrent": avg_concurrent,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "avg_response_time": avg_response_time,
                    "queue_length": queue_length,
                    "success_rate": success_rate,
                    "system_stable": (cpu_usage < 80 and memory_usage < 75 and avg_response_time < 120),
                    "recommendations": self._get_load_recommendations(cpu_usage, memory_usage, avg_response_time)
                }
            
            return {
                "scenarios": projections,
                "capacity_ceiling": self._calculate_capacity_ceiling(),
                "performance_degradation_points": self._identify_degradation_points(projections)
            }
        
        except Exception as e:
            logger.error(f"性能预测失败: {e}")
            return {}
    
    def _get_load_recommendations(self, cpu_usage: float, memory_usage: float, response_time: float) -> List[str]:
        """基于负载情况生成建议"""
        recommendations = []
        
        if cpu_usage > 80:
            recommendations.append("CPU使用率过高，建议增加CPU核心或减少并发数")
        if memory_usage > 75:
            recommendations.append("内存使用率过高，建议增加内存或优化内存使用")
        if response_time > 90:
            recommendations.append("响应时间过长，建议增加并发处理能力或优化流程")
        
        if not recommendations:
            recommendations.append("系统运行正常，可继续当前配置")
        
        return recommendations
    
    def _calculate_capacity_ceiling(self) -> Dict[str, any]:
        """计算容量上限"""
        try:
            # 基于不同资源限制计算理论上限
            cpu_ceiling = int(80 / (self.baseline_performance["single_download_cpu"] * 100))
            memory_ceiling = int(75 / (self.baseline_performance["single_download_memory"] * 100))
            
            # 考虑响应时间限制
            max_acceptable_response_time = 120  # 秒
            response_time_ceiling = int(max_acceptable_response_time / self.baseline_performance["single_download_time"])
            
            theoretical_ceiling = min(cpu_ceiling, memory_ceiling, response_time_ceiling)
            
            # 应用安全系数
            practical_ceiling = int(theoretical_ceiling * 0.8)
            
            return {
                "theoretical_max_concurrent": theoretical_ceiling,
                "practical_max_concurrent": practical_ceiling,
                "limiting_factors": {
                    "cpu_limit": cpu_ceiling,
                    "memory_limit": memory_ceiling,
                    "response_time_limit": response_time_ceiling
                },
                "max_throughput_per_hour": int(practical_ceiling * (3600 / self.baseline_performance["single_download_time"])),
                "max_throughput_per_day": int(practical_ceiling * (86400 / self.baseline_performance["single_download_time"]))
            }
        
        except Exception as e:
            logger.error(f"容量上限计算失败: {e}")
            return {}
    
    def _identify_degradation_points(self, projections: Dict) -> List[Dict[str, any]]:
        """识别性能降级点"""
        degradation_points = []
        
        for scenario_name, projection in projections.items():
            if not projection["system_stable"]:
                degradation_points.append({
                    "scenario": scenario_name,
                    "requests_per_hour": projection["requests_per_hour"],
                    "degradation_reason": self._get_degradation_reason(projection),
                    "impact": "系统性能显著下降",
                    "mitigation": "需要扩容或优化"
                })
        
        return degradation_points
    
    def _get_degradation_reason(self, projection: Dict) -> str:
        """获取性能降级原因"""
        reasons = []
        
        if projection["cpu_usage"] >= 80:
            reasons.append("CPU使用率过高")
        if projection["memory_usage"] >= 75:
            reasons.append("内存使用率过高")
        if projection["avg_response_time"] >= 120:
            reasons.append("响应时间过长")
        
        return "; ".join(reasons) if reasons else "未知原因"
    
    def generate_capacity_report(self) -> Dict[str, any]:
        """生成完整的容量规划报告"""
        try:
            logger.info("📋 生成容量规划报告...")
            
            # 分析单实例容量
            single_instance_analysis = self.analyze_single_instance_capacity()
            
            # 生成多实例扩展方案
            multi_instance_scenarios = self._analyze_multi_instance_scaling()
            
            # 成本效益分析
            cost_benefit_analysis = self._perform_cost_benefit_analysis()
            
            # 风险评估
            risk_assessment = self._assess_scaling_risks()
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_version": "1.0",
                    "baseline_date": "2025-08-28",
                    "baseline_success_rate": self.baseline_performance["success_rate"]
                },
                "executive_summary": {
                    "current_capacity": single_instance_analysis.get("capacity_limits", {}),
                    "key_bottlenecks": [b["type"] for b in single_instance_analysis.get("bottleneck_analysis", [])],
                    "recommended_actions": single_instance_analysis.get("scaling_recommendations", {}).get("priority_recommendations", [])
                },
                "detailed_analysis": {
                    "single_instance": single_instance_analysis,
                    "multi_instance_scaling": multi_instance_scenarios,
                    "cost_benefit": cost_benefit_analysis,
                    "risk_assessment": risk_assessment
                },
                "implementation_roadmap": self._create_implementation_roadmap(),
                "monitoring_recommendations": self._generate_monitoring_recommendations()
            }
            
            # 保存报告
            report_file = f"/root/projects/tencent-doc-manager/reports/capacity_planning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"✅ 容量规划报告已生成: {report_file}")
            
            return report
        
        except Exception as e:
            logger.error(f"❌ 容量规划报告生成失败: {e}")
            return {"error": str(e)}
    
    def _analyze_multi_instance_scaling(self) -> Dict[str, any]:
        """分析多实例扩展方案"""
        try:
            scaling_scenarios = {}
            
            # 2-10实例的扩展方案
            for instance_count in range(2, 11):
                # 线性扩展假设（实际可能有额外开销）
                theoretical_throughput = instance_count * (3600 / self.baseline_performance["single_download_time"])
                
                # 考虑协调开销（每增加一个实例，效率下降2%）
                efficiency_factor = 0.98 ** (instance_count - 1)
                actual_throughput = theoretical_throughput * efficiency_factor
                
                # 成本估算（基于云服务器价格）
                estimated_hourly_cost = instance_count * 0.5  # $0.5/小时每实例
                cost_per_download = estimated_hourly_cost / actual_throughput
                
                scaling_scenarios[f"{instance_count}_instances"] = {
                    "instance_count": instance_count,
                    "theoretical_throughput_per_hour": int(theoretical_throughput),
                    "actual_throughput_per_hour": int(actual_throughput),
                    "efficiency_factor": efficiency_factor,
                    "estimated_hourly_cost_usd": estimated_hourly_cost,
                    "cost_per_download_usd": cost_per_download,
                    "scalability_bottlenecks": self._identify_scaling_bottlenecks(instance_count)
                }
            
            # 找出最佳性价比配置
            best_value = min(
                scaling_scenarios.items(),
                key=lambda x: x[1]["cost_per_download_usd"]
            )
            
            return {
                "scenarios": scaling_scenarios,
                "best_value_config": {
                    "scenario": best_value[0],
                    "details": best_value[1]
                },
                "scaling_considerations": [
                    "Cookie管理需要在多实例间协调",
                    "负载均衡器增加额外延迟",
                    "监控和日志收集复杂化",
                    "故障恢复需要跨实例协调"
                ]
            }
        
        except Exception as e:
            logger.error(f"多实例扩展分析失败: {e}")
            return {}
    
    def _identify_scaling_bottlenecks(self, instance_count: int) -> List[str]:
        """识别扩展瓶颈"""
        bottlenecks = []
        
        if instance_count > 3:
            bottlenecks.append("Cookie管理复杂化")
        if instance_count > 5:
            bottlenecks.append("可能触发腾讯文档的IP级别限制")
        if instance_count > 8:
            bottlenecks.append("协调开销显著影响效率")
        
        return bottlenecks
    
    def _perform_cost_benefit_analysis(self) -> Dict[str, any]:
        """执行成本效益分析"""
        try:
            # 基础成本（单实例）
            single_instance_cost = {
                "hardware_monthly": 100,  # $100/月 基础服务器
                "bandwidth_monthly": 50,   # $50/月 带宽费用
                "maintenance_monthly": 30,  # $30/月 维护费用
                "total_monthly": 180
            }
            
            # 扩展方案成本分析
            scaling_options = [
                {
                    "name": "垂直扩展（CPU+内存升级）",
                    "additional_cost_monthly": 80,
                    "performance_improvement": 2.5,
                    "implementation_complexity": "low",
                    "roi_months": 3
                },
                {
                    "name": "水平扩展（3实例）",
                    "additional_cost_monthly": 360,
                    "performance_improvement": 2.8,
                    "implementation_complexity": "medium",
                    "roi_months": 6
                },
                {
                    "name": "混合扩展（2实例+硬件升级）",
                    "additional_cost_monthly": 260,
                    "performance_improvement": 4.0,
                    "implementation_complexity": "medium",
                    "roi_months": 4
                }
            ]
            
            # 计算每种方案的性价比
            for option in scaling_options:
                total_cost = single_instance_cost["total_monthly"] + option["additional_cost_monthly"]
                cost_per_performance_unit = total_cost / option["performance_improvement"]
                option["cost_per_performance_unit"] = cost_per_performance_unit
                option["total_monthly_cost"] = total_cost
            
            # 推荐方案
            best_roi = min(scaling_options, key=lambda x: x["cost_per_performance_unit"])
            
            return {
                "baseline_cost": single_instance_cost,
                "scaling_options": scaling_options,
                "recommended_option": best_roi,
                "break_even_analysis": {
                    "monthly_processing_volume_threshold": 1000,  # 每月1000次下载为盈亏平衡点
                    "cost_savings_percentage": 25  # 自动化相比人工节省25%成本
                }
            }
        
        except Exception as e:
            logger.error(f"成本效益分析失败: {e}")
            return {}
    
    def _assess_scaling_risks(self) -> Dict[str, any]:
        """评估扩展风险"""
        risks = {
            "technical_risks": [
                {
                    "risk": "Cookie管理复杂化",
                    "probability": "high",
                    "impact": "medium",
                    "mitigation": "实施Cookie池和轮转机制",
                    "monitoring": "Cookie有效性和使用率监控"
                },
                {
                    "risk": "反爬虫检测增强",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation": "降低请求频率，增加随机延迟",
                    "monitoring": "成功率和错误类型监控"
                },
                {
                    "risk": "系统复杂性增加",
                    "probability": "high",
                    "impact": "medium",
                    "mitigation": "完善监控和自动化运维",
                    "monitoring": "系统健康度和性能指标监控"
                }
            ],
            "business_risks": [
                {
                    "risk": "运营成本上升",
                    "probability": "medium",
                    "impact": "medium",
                    "mitigation": "基于实际使用量动态调整资源",
                    "monitoring": "成本效益比监控"
                },
                {
                    "risk": "服务依赖性增强",
                    "probability": "high",
                    "impact": "medium",
                    "mitigation": "实施降级机制和手动备份方案",
                    "monitoring": "服务可用性监控"
                }
            ],
            "operational_risks": [
                {
                    "risk": "维护复杂性增加",
                    "probability": "high",
                    "impact": "low",
                    "mitigation": "标准化部署和运维流程",
                    "monitoring": "运维效率和响应时间监控"
                },
                {
                    "risk": "故障影响范围扩大",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation": "实施故障隔离和快速恢复机制",
                    "monitoring": "故障检测和恢复时间监控"
                }
            ]
        }
        
        return risks
    
    def _create_implementation_roadmap(self) -> Dict[str, any]:
        """创建实施路线图"""
        roadmap = {
            "phase_1": {
                "name": "基础优化阶段",
                "duration": "2-4周",
                "objectives": [
                    "实施浏览器池化",
                    "优化Cookie管理机制",
                    "添加基础监控"
                ],
                "expected_improvement": "30-50%性能提升",
                "investment": "低",
                "risk": "低"
            },
            "phase_2": {
                "name": "垂直扩展阶段",
                "duration": "1-2周",
                "objectives": [
                    "升级硬件配置",
                    "优化资源利用",
                    "实施智能重试机制"
                ],
                "expected_improvement": "100-150%性能提升",
                "investment": "中",
                "risk": "低"
            },
            "phase_3": {
                "name": "水平扩展阶段",
                "duration": "4-6周",
                "objectives": [
                    "实施多实例部署",
                    "构建负载均衡",
                    "实施分布式Cookie管理"
                ],
                "expected_improvement": "200-300%性能提升",
                "investment": "高",
                "risk": "中"
            },
            "phase_4": {
                "name": "智能优化阶段",
                "duration": "2-3周",
                "objectives": [
                    "实施AI驱动的负载预测",
                    "自动化扩缩容",
                    "高级监控和告警"
                ],
                "expected_improvement": "优化运营效率",
                "investment": "中",
                "risk": "中"
            }
        }
        
        return roadmap
    
    def _generate_monitoring_recommendations(self) -> Dict[str, any]:
        """生成监控建议"""
        return {
            "key_metrics": [
                {
                    "metric": "并发下载数",
                    "threshold": "< 5个",
                    "alert_level": "warning"
                },
                {
                    "metric": "平均响应时间",
                    "threshold": "> 60秒",
                    "alert_level": "warning"
                },
                {
                    "metric": "CPU使用率",
                    "threshold": "> 80%",
                    "alert_level": "critical"
                },
                {
                    "metric": "内存使用率",
                    "threshold": "> 75%",
                    "alert_level": "warning"
                },
                {
                    "metric": "下载成功率",
                    "threshold": "< 85%",
                    "alert_level": "critical"
                }
            ],
            "dashboard_requirements": [
                "实时性能监控面板",
                "容量利用率趋势图",
                "错误率和失败原因分析",
                "成本效益追踪图表"
            ],
            "automated_responses": [
                "高负载时自动限流",
                "资源耗尽时自动清理",
                "连续失败时自动降级"
            ]
        }


async def main():
    """主函数"""
    try:
        print("=== 腾讯文档系统容量规划分析 ===")
        
        planner = CapacityPlanner()
        
        # 生成完整的容量规划报告
        report = planner.generate_capacity_report()
        
        if "error" not in report:
            print("\n✅ 容量规划分析完成")
            print(f"📊 单实例理论最大并发: {report['detailed_analysis']['single_instance']['capacity_limits']['theoretical_max_concurrent']}")
            print(f"🔒 单实例安全最大并发: {report['detailed_analysis']['single_instance']['capacity_limits']['safe_max_concurrent']}")
            print(f"💡 推荐并发数: {report['detailed_analysis']['single_instance']['capacity_limits']['recommended_concurrent']}")
            
            print(f"\n📈 预计吞吐量:")
            throughput = report['detailed_analysis']['single_instance']['throughput_analysis']['recommended_config']['details']
            print(f"   - 每小时: {throughput['downloads_per_hour']} 次下载")
            print(f"   - 每天: {throughput['downloads_per_day']} 次下载")
            
            print(f"\n⚠️ 主要瓶颈:")
            for bottleneck in report['detailed_analysis']['single_instance']['bottleneck_analysis']:
                print(f"   - {bottleneck['type']}: {bottleneck['description']}")
        else:
            print(f"❌ 分析失败: {report['error']}")
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行分析
    asyncio.run(main())