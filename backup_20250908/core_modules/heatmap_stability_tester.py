#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 5: 热力图算法稳定性测试器
确保热力图算法在各种条件下保持稳定性能
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import time
import json
import logging
import math
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
import statistics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeatmapStabilityTester:
    """
    热力图算法稳定性测试器
    测试高斯平滑、数据生成、API响应等核心功能
    """
    
    def __init__(self, base_url: str = "http://localhost:8089"):
        """初始化稳定性测试器"""
        self.base_url = base_url
        self.test_results = []
        self.performance_metrics = {
            'api_response_times': [],
            'data_generation_times': [],
            'memory_usage': [],
            'algorithm_accuracy': [],
            'stability_score': 0.0
        }
        
        logger.info("✅ 热力图稳定性测试器初始化完成")
    
    def gaussian_smoothing_test(self, matrix: List[List[float]]) -> Dict:
        """测试高斯平滑算法的稳定性"""
        try:
            start_time = time.time()
            
            # 创建高斯核函数
            def gaussian_kernel(size: int, sigma: float) -> List[List[float]]:
                kernel = [[0.0 for _ in range(size)] for _ in range(size)]
                center = size // 2
                total = 0.0
                
                for y in range(size):
                    for x in range(size):
                        distance = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
                        value = math.exp(-(distance ** 2) / (2 * (sigma ** 2)))
                        kernel[y][x] = value
                        total += value
                
                # 标准化核
                for y in range(size):
                    for x in range(size):
                        kernel[y][x] /= total
                        
                return kernel
            
            # 应用高斯平滑
            def apply_gaussian_smooth(data: List[List[float]], kernel_size: int = 5, sigma: float = 1.5) -> List[List[float]]:
                kernel = gaussian_kernel(kernel_size, sigma)
                height = len(data)
                width = len(data[0])
                result = [[0.0 for _ in range(width)] for _ in range(height)]
                padding = kernel_size // 2
                
                for y in range(height):
                    for x in range(width):
                        weighted_sum = 0.0
                        weight_total = 0.0
                        
                        for ky in range(kernel_size):
                            for kx in range(kernel_size):
                                dy = y + ky - padding
                                dx = x + kx - padding
                                
                                if 0 <= dy < height and 0 <= dx < width:
                                    weight = kernel[ky][kx]
                                    weighted_sum += data[dy][dx] * weight
                                    weight_total += weight
                        
                        result[y][x] = weighted_sum / weight_total if weight_total > 0 else 0.0
                
                return result
            
            # 执行平滑算法
            smoothed_matrix = apply_gaussian_smooth(matrix)
            processing_time = time.time() - start_time
            
            # 计算平滑效果指标
            original_values = [cell for row in matrix for cell in row]
            smoothed_values = [cell for row in smoothed_matrix for cell in row]
            
            original_variance = statistics.variance(original_values) if len(original_values) > 1 else 0
            smoothed_variance = statistics.variance(smoothed_values) if len(smoothed_values) > 1 else 0
            smoothing_ratio = original_variance / max(smoothed_variance, 0.001)
            
            # 边缘保持测试
            edge_preservation = self._calculate_edge_preservation(matrix, smoothed_matrix)
            
            return {
                'success': True,
                'processing_time': processing_time,
                'smoothing_ratio': smoothing_ratio,
                'edge_preservation': edge_preservation,
                'matrix_size': f"{len(matrix)}x{len(matrix[0])}",
                'algorithm_stability': 'stable' if processing_time < 0.1 and smoothing_ratio > 1.0 else 'unstable'
            }
            
        except Exception as e:
            logger.error(f"高斯平滑测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'algorithm_stability': 'failed'
            }
    
    def _calculate_edge_preservation(self, original: List[List[float]], smoothed: List[List[float]]) -> float:
        """计算边缘保持度"""
        try:
            height = len(original)
            width = len(original[0])
            
            # 计算梯度
            original_gradients = []
            smoothed_gradients = []
            
            for y in range(1, height-1):
                for x in range(1, width-1):
                    # 原始梯度
                    orig_grad_x = original[y][x+1] - original[y][x-1]
                    orig_grad_y = original[y+1][x] - original[y-1][x]
                    orig_grad = (orig_grad_x**2 + orig_grad_y**2)**0.5
                    original_gradients.append(orig_grad)
                    
                    # 平滑后梯度
                    smooth_grad_x = smoothed[y][x+1] - smoothed[y][x-1]
                    smooth_grad_y = smoothed[y+1][x] - smoothed[y-1][x]
                    smooth_grad = (smooth_grad_x**2 + smooth_grad_y**2)**0.5
                    smoothed_gradients.append(smooth_grad)
            
            # 计算相关性
            if len(original_gradients) > 0:
                # 计算皮尔逊相关系数
                n = len(original_gradients)
                sum_x = sum(original_gradients)
                sum_y = sum(smoothed_gradients)
                sum_xx = sum(x*x for x in original_gradients)
                sum_yy = sum(y*y for y in smoothed_gradients)
                sum_xy = sum(x*y for x, y in zip(original_gradients, smoothed_gradients))
                
                numerator = n * sum_xy - sum_x * sum_y
                denominator = ((n * sum_xx - sum_x**2) * (n * sum_yy - sum_y**2))**0.5
                
                if denominator > 0:
                    correlation = numerator / denominator
                    return max(0.0, correlation)  # 返回正相关性
                else:
                    return 0.0
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    async def api_stability_test(self, num_requests: int = 20) -> Dict:
        """测试API稳定性和响应时间"""
        try:
            logger.info(f"📊 开始API稳定性测试: {num_requests}次请求")
            
            response_times = []
            success_count = 0
            error_count = 0
            
            for i in range(num_requests):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/data", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success') and 'heatmap_data' in data.get('data', {}):
                            response_times.append(response_time)
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"请求 {i+1} 失败: {e}")
                
                # 避免过于频繁的请求
                await asyncio.sleep(0.1)
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                response_stability = statistics.stdev(response_times) if len(response_times) > 1 else 0.0
            else:
                avg_response_time = float('inf')
                min_response_time = float('inf')
                max_response_time = float('inf')
                response_stability = float('inf')
            
            success_rate = (success_count / num_requests) * 100
            
            return {
                'success': True,
                'total_requests': num_requests,
                'successful_requests': success_count,
                'failed_requests': error_count,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'response_stability': response_stability,
                'api_stability': 'stable' if success_rate >= 95 and avg_response_time < 2.0 else 'unstable'
            }
            
        except Exception as e:
            logger.error(f"API稳定性测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'api_stability': 'failed'
            }
    
    async def load_test(self, concurrent_requests: int = 10) -> Dict:
        """负载测试"""
        try:
            logger.info(f"🚀 开始负载测试: {concurrent_requests}个并发请求")
            
            start_time = time.time()
            
            async def make_request():
                try:
                    response = requests.get(f"{self.base_url}/api/data", timeout=5)
                    return response.status_code == 200 and response.json().get('success', False)
                except:
                    return False
            
            # 并发执行请求
            with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, lambda: requests.get(f"{self.base_url}/api/data", timeout=5))
                    for _ in range(concurrent_requests)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            successful_responses = 0
            for result in results:
                if not isinstance(result, Exception):
                    try:
                        if result.status_code == 200 and result.json().get('success', False):
                            successful_responses += 1
                    except:
                        pass
            
            load_success_rate = (successful_responses / concurrent_requests) * 100
            throughput = concurrent_requests / total_time if total_time > 0 else 0
            
            return {
                'success': True,
                'concurrent_requests': concurrent_requests,
                'successful_responses': successful_responses,
                'total_time': total_time,
                'success_rate': load_success_rate,
                'throughput': throughput,  # 请求/秒
                'load_stability': 'stable' if load_success_rate >= 90 and throughput >= 5 else 'unstable'
            }
            
        except Exception as e:
            logger.error(f"负载测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'load_stability': 'failed'
            }
    
    def data_integrity_test(self) -> Dict:
        """数据完整性测试"""
        try:
            logger.info("🔍 开始数据完整性测试")
            
            response = requests.get(f"{self.base_url}/api/data", timeout=10)
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': '无法获取API响应',
                    'data_integrity': 'failed'
                }
            
            data = response.json()
            
            # 检查数据结构完整性
            required_fields = [
                'success', 'data', 'metadata', 'timestamp'
            ]
            
            data_fields = [
                'heatmap_data', 'tables', 'statistics', 'algorithm_settings'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if 'data' in data:
                for field in data_fields:
                    if field not in data['data']:
                        missing_fields.append(f"data.{field}")
            
            # 检查热力图矩阵完整性
            heatmap_data = data.get('data', {}).get('heatmap_data', [])
            matrix_valid = True
            matrix_errors = []
            
            if not heatmap_data:
                matrix_valid = False
                matrix_errors.append("热力图数据为空")
            else:
                expected_rows = 30
                expected_cols = 19
                
                if len(heatmap_data) != expected_rows:
                    matrix_valid = False
                    matrix_errors.append(f"行数错误: 期望{expected_rows}, 实际{len(heatmap_data)}")
                
                for i, row in enumerate(heatmap_data):
                    if len(row) != expected_cols:
                        matrix_valid = False
                        matrix_errors.append(f"第{i+1}行列数错误: 期望{expected_cols}, 实际{len(row)}")
                    
                    for j, cell in enumerate(row):
                        if not isinstance(cell, (int, float)):
                            matrix_valid = False
                            matrix_errors.append(f"单元格[{i+1},{j+1}]类型错误: {type(cell)}")
                        elif cell < 0 or cell > 1:
                            matrix_valid = False
                            matrix_errors.append(f"单元格[{i+1},{j+1}]值超出范围: {cell}")
            
            # 检查表格数据完整性
            tables = data.get('data', {}).get('tables', [])
            tables_valid = True
            table_errors = []
            
            if len(tables) != 30:
                tables_valid = False
                table_errors.append(f"表格数量错误: 期望30, 实际{len(tables)}")
            
            for i, table in enumerate(tables):
                required_table_fields = ['id', 'name', 'risk_level']
                for field in required_table_fields:
                    if field not in table:
                        tables_valid = False
                        table_errors.append(f"表格{i+1}缺少字段: {field}")
            
            return {
                'success': True,
                'missing_fields': missing_fields,
                'matrix_valid': matrix_valid,
                'matrix_errors': matrix_errors,
                'tables_valid': tables_valid,
                'table_errors': table_errors,
                'data_integrity': 'valid' if not missing_fields and matrix_valid and tables_valid else 'invalid'
            }
            
        except Exception as e:
            logger.error(f"数据完整性测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data_integrity': 'failed'
            }
    
    async def comprehensive_stability_test(self) -> Dict:
        """综合稳定性测试"""
        try:
            logger.info("🎯 开始综合稳定性测试")
            
            test_results = {}
            
            # 1. 获取测试数据
            response = requests.get(f"{self.base_url}/api/data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                heatmap_data = data.get('data', {}).get('heatmap_data', [])
            else:
                heatmap_data = [[0.5 for _ in range(19)] for _ in range(30)]  # 默认测试数据
            
            # 2. 高斯平滑测试
            gaussian_result = self.gaussian_smoothing_test(heatmap_data)
            test_results['gaussian_smoothing'] = gaussian_result
            
            # 3. API稳定性测试
            api_result = await self.api_stability_test(15)
            test_results['api_stability'] = api_result
            
            # 4. 负载测试
            load_result = await self.load_test(8)
            test_results['load_test'] = load_result
            
            # 5. 数据完整性测试
            integrity_result = self.data_integrity_test()
            test_results['data_integrity'] = integrity_result
            
            # 计算综合稳定性评分
            stability_score = self._calculate_stability_score(test_results)
            
            # 生成综合评估
            overall_status = self._get_overall_status(stability_score)
            
            return {
                'success': True,
                'test_results': test_results,
                'stability_score': stability_score,
                'overall_status': overall_status,
                'timestamp': datetime.now().isoformat(),
                'test_summary': self._generate_test_summary(test_results)
            }
            
        except Exception as e:
            logger.error(f"综合稳定性测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'overall_status': 'failed'
            }
    
    def _calculate_stability_score(self, test_results: Dict) -> float:
        """计算稳定性评分"""
        try:
            scores = []
            
            # 高斯平滑评分 (25%)
            gaussian = test_results.get('gaussian_smoothing', {})
            if gaussian.get('success') and gaussian.get('algorithm_stability') == 'stable':
                scores.append(100)
            elif gaussian.get('success'):
                scores.append(70)
            else:
                scores.append(0)
            
            # API稳定性评分 (30%)
            api = test_results.get('api_stability', {})
            if api.get('success') and api.get('api_stability') == 'stable':
                success_rate = api.get('success_rate', 0)
                scores.append(min(100, success_rate))
            else:
                scores.append(0)
            
            # 负载测试评分 (25%)
            load = test_results.get('load_test', {})
            if load.get('success') and load.get('load_stability') == 'stable':
                load_success_rate = load.get('success_rate', 0)
                scores.append(min(100, load_success_rate))
            else:
                scores.append(0)
            
            # 数据完整性评分 (20%)
            integrity = test_results.get('data_integrity', {})
            if integrity.get('success') and integrity.get('data_integrity') == 'valid':
                scores.append(100)
            elif integrity.get('success'):
                scores.append(50)
            else:
                scores.append(0)
            
            # 加权平均
            weights = [0.25, 0.30, 0.25, 0.20]
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            
            return round(weighted_score, 1)
            
        except Exception:
            return 0.0
    
    def _get_overall_status(self, stability_score: float) -> str:
        """获取综合状态评估"""
        if stability_score >= 95:
            return "🏅 A+ (热力图完美稳定)"
        elif stability_score >= 90:
            return "✅ A (热力图稳定运行)"
        elif stability_score >= 80:
            return "🟢 B+ (热力图良好稳定)"
        elif stability_score >= 70:
            return "🟡 B (热力图基本稳定)"
        elif stability_score >= 60:
            return "🟠 C+ (热力图轻微不稳定)"
        else:
            return "🔴 C (热力图不稳定)"
    
    def _generate_test_summary(self, test_results: Dict) -> Dict:
        """生成测试摘要"""
        summary = {
            'total_tests': len(test_results),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': {}
        }
        
        for test_name, result in test_results.items():
            if result.get('success'):
                summary['passed_tests'] += 1
                summary['test_details'][test_name] = '✅ 通过'
            else:
                summary['failed_tests'] += 1
                summary['test_details'][test_name] = '❌ 失败'
        
        return summary


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='热力图算法稳定性测试器')
    parser.add_argument('--url', default='http://localhost:8089', help='热力图服务器URL')
    parser.add_argument('--test-type', choices=['gaussian', 'api', 'load', 'integrity', 'comprehensive'], 
                       default='comprehensive', help='测试类型')
    parser.add_argument('--requests', type=int, default=20, help='API测试请求数')
    parser.add_argument('--concurrent', type=int, default=10, help='负载测试并发数')
    
    args = parser.parse_args()
    
    tester = HeatmapStabilityTester(args.url)
    
    try:
        if args.test_type == 'comprehensive':
            print("🎯 开始热力图算法综合稳定性测试...")
            result = await tester.comprehensive_stability_test()
            
            if result['success']:
                print(f"\n✅ 综合稳定性测试完成!")
                print(f"   稳定性评分: {result['stability_score']}/100")
                print(f"   综合状态: {result['overall_status']}")
                
                summary = result['test_summary']
                print(f"   测试通过: {summary['passed_tests']}/{summary['total_tests']}")
                
                for test_name, status in summary['test_details'].items():
                    print(f"     {test_name}: {status}")
                
                # 详细结果
                print(f"\n📊 详细测试结果:")
                for test_name, test_result in result['test_results'].items():
                    if test_result.get('success'):
                        if test_name == 'api_stability':
                            print(f"   API稳定性: 成功率{test_result.get('success_rate', 0):.1f}%, 平均响应{test_result.get('avg_response_time', 0):.3f}秒")
                        elif test_name == 'load_test':
                            print(f"   负载测试: 成功率{test_result.get('success_rate', 0):.1f}%, 吞吐量{test_result.get('throughput', 0):.1f}请求/秒")
                        elif test_name == 'gaussian_smoothing':
                            print(f"   高斯平滑: 处理时间{test_result.get('processing_time', 0):.3f}秒, 状态{test_result.get('algorithm_stability', 'unknown')}")
                        elif test_name == 'data_integrity':
                            print(f"   数据完整性: {test_result.get('data_integrity', 'unknown')}")
            else:
                print(f"\n❌ 综合稳定性测试失败: {result.get('error')}")
                
        print(f"\n🎉 热力图稳定性测试完成!")
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())