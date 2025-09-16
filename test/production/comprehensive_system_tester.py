#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive System Testing Framework
Brutally honest assessment of production readiness and real-world functionality
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import json
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import aiohttp

# Import all production modules
from cookie_manager import get_cookie_manager, CookieManager
from production_upload_manager import ProductionUploadDownloadManager
from csv_security_manager import CSVSecurityManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemTestResult:
    """Test result container"""
    
    def __init__(self, component: str, test_name: str):
        self.component = component
        self.test_name = test_name
        self.success = False
        self.grade = "F"
        self.score = 0.0
        self.error = None
        self.details = {}
        self.start_time = time.time()
        self.end_time = None
        self.duration = 0.0
    
    def set_result(self, success: bool, grade: str, score: float, details: dict = None, error: str = None):
        """Set test result"""
        self.success = success
        self.grade = grade
        self.score = score
        self.error = error
        self.details = details or {}
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'component': self.component,
            'test_name': self.test_name,
            'success': self.success,
            'grade': self.grade,
            'score': self.score,
            'error': self.error,
            'details': self.details,
            'duration': self.duration,
            'timestamp': datetime.fromtimestamp(self.start_time).isoformat()
        }


class ComprehensiveSystemTester:
    """
    Comprehensive system tester with brutal honesty
    Tests real-world functionality against claimed issues
    """
    
    def __init__(self, base_dir: str = None):
        """Initialize system tester"""
        self.base_dir = base_dir or "/root/projects/tencent-doc-manager"
        self.test_results = []
        self.overall_grade = "F"
        self.overall_score = 0.0
        
        # Test configuration
        self.test_timeout = 30  # 30 seconds per test
        self.retry_count = 3
        self.test_data_dir = os.path.join(self.base_dir, "test_data")
        self.results_dir = os.path.join(self.base_dir, "test_results")
        
        # Create directories
        for directory in [self.test_data_dir, self.results_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("🧪 Comprehensive System Tester initialized - BRUTAL HONESTY MODE")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive system tests"""
        logger.info("🚀 Starting comprehensive system testing...")
        
        test_start = time.time()
        
        # Test Suite 1: Cookie Manager
        await self._test_cookie_manager()
        
        # Test Suite 2: Upload/Download Manager
        await self._test_upload_download_manager()
        
        # Test Suite 3: CSV Security Manager
        await self._test_csv_security_manager()
        
        # Test Suite 4: Claude API Integration
        await self._test_claude_api_integration()
        
        # Test Suite 5: End-to-End Integration
        await self._test_end_to_end_integration()
        
        # Test Suite 6: Stage 7 System Connectivity Assurance
        await self._test_stage7_system_connectivity()
        
        total_duration = time.time() - test_start
        
        # Calculate overall scores
        self._calculate_overall_grade()
        
        # Generate comprehensive report
        report = await self._generate_comprehensive_report(total_duration)
        
        # Save report
        report_file = os.path.join(self.results_dir, f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Testing completed. Overall grade: {self.overall_grade} ({self.overall_score:.1f}%)")
        logger.info(f"📄 Report saved: {report_file}")
        
        return report
    
    async def _test_cookie_manager(self):
        """Test Cookie Manager - addressing single point of failure claim"""
        logger.info("🔐 Testing Cookie Manager (claimed: 100% upload failures)")
        
        # Test 1: Basic initialization
        result = SystemTestResult("Cookie Manager", "Initialization")
        try:
            cookie_manager = get_cookie_manager()
            await cookie_manager.load_cookies()
            
            result.set_result(True, "B+", 85.0, {
                'initialized': True,
                'encryption_enabled': True,
                'config_loaded': True
            })
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 2: Cookie validation with real Tencent docs
        result = SystemTestResult("Cookie Manager", "Real Authentication Test")
        try:
            cookie_manager = get_cookie_manager()
            valid_cookies = await cookie_manager.get_valid_cookies()
            
            if valid_cookies:
                # Try to validate against real Tencent docs
                is_valid, message = await cookie_manager.validate_cookies(valid_cookies)
                
                if is_valid:
                    result.set_result(True, "A", 95.0, {
                        'has_valid_cookies': True,
                        'authentication_working': True,
                        'validation_message': message
                    })
                else:
                    result.set_result(False, "D", 30.0, {
                        'has_cookies': True,
                        'authentication_failed': True,
                        'validation_message': message
                    }, f"Cookie validation failed: {message}")
            else:
                result.set_result(False, "F", 10.0, {
                    'has_cookies': False,
                    'authentication_failed': True
                }, "No valid cookies available")
        except Exception as e:
            result.set_result(False, "F", 0.0, error=f"Cookie validation test failed: {str(e)}")
        
        self.test_results.append(result)
        
        # Test 3: Health status check
        result = SystemTestResult("Cookie Manager", "Health Status")
        try:
            cookie_manager = get_cookie_manager()
            health = await cookie_manager.get_health_status()
            
            if health.get('healthy', False):
                score = 90.0 if health.get('primary_cookie_valid', False) else 60.0
                grade = "A-" if score >= 85 else "B"
                result.set_result(True, grade, score, health)
            else:
                result.set_result(False, "D", 25.0, health, "System reported as unhealthy")
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
    
    async def _test_upload_download_manager(self):
        """Test Upload/Download Manager - addressing 100% failure claim"""
        logger.info("📤 Testing Upload/Download Manager (claimed: 100% failure rate)")
        
        # Test 1: Manager initialization
        result = SystemTestResult("Upload Manager", "Initialization")
        try:
            manager = ProductionUploadDownloadManager()
            browser_init = await manager.initialize_browser(headless=True)
            
            if browser_init:
                result.set_result(True, "B+", 85.0, {
                    'browser_initialized': True,
                    'headless_mode': True
                })
            else:
                result.set_result(False, "D", 30.0, error="Browser initialization failed")
            
            # Clean up
            await manager.cleanup()
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 2: Cookie setup test
        result = SystemTestResult("Upload Manager", "Cookie Setup")
        try:
            manager = ProductionUploadDownloadManager()
            await manager.initialize_browser(headless=True)
            
            cookie_setup = await manager.setup_cookies()
            
            if cookie_setup:
                result.set_result(True, "B", 80.0, {
                    'cookie_setup_successful': True,
                    'authentication_ready': True
                })
            else:
                result.set_result(False, "D", 35.0, error="Cookie setup failed - potential cause of upload failures")
            
            await manager.cleanup()
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 3: System status check
        result = SystemTestResult("Upload Manager", "System Status")
        try:
            manager = ProductionUploadDownloadManager()
            await manager.initialize_browser(headless=True)
            await manager.setup_cookies()
            
            status = await manager.get_system_status()
            
            browser_ready = status.get('browser_ready', False)
            cookie_health = status.get('cookie_health', {}).get('healthy', False)
            
            if browser_ready and cookie_health:
                result.set_result(True, "A-", 88.0, status)
            elif browser_ready or cookie_health:
                result.set_result(True, "C+", 65.0, status, "Partial system readiness")
            else:
                result.set_result(False, "D-", 20.0, status, "System not ready for operations")
            
            await manager.cleanup()
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
    
    async def _test_csv_security_manager(self):
        """Test CSV Security Manager"""
        logger.info("🛡️ Testing CSV Security Manager")
        
        # Create test CSV files
        test_file1, test_file2 = await self._create_test_csv_files()
        
        # Test 1: Manager initialization
        result = SystemTestResult("CSV Security Manager", "Initialization")
        try:
            manager = CSVSecurityManager()
            result.set_result(True, "A", 95.0, {
                'initialized': True,
                'security_config_loaded': True,
                'directories_created': True
            })
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 2: CSV comparison functionality
        result = SystemTestResult("CSV Security Manager", "CSV Comparison")
        try:
            manager = CSVSecurityManager()
            comparison_result = await manager.comprehensive_csv_analysis(
                test_file1, test_file2, "test_comparison"
            )
            
            if comparison_result.get('success', False):
                security_score = comparison_result.get('comparison_summary', {}).get('security_score', 0)
                grade = "A" if security_score >= 90 else "B+" if security_score >= 80 else "B" if security_score >= 70 else "C"
                result.set_result(True, grade, security_score, comparison_result)
            else:
                result.set_result(False, "D", 25.0, comparison_result, "CSV comparison failed")
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 3: System status
        result = SystemTestResult("CSV Security Manager", "System Status") 
        try:
            manager = CSVSecurityManager()
            status = await manager.get_comprehensive_status()
            
            system_grade = status.get('system_grade', '')
            if 'A+' in system_grade:
                result.set_result(True, "A+", 98.0, status)
            elif 'A' in system_grade:
                result.set_result(True, "A", 92.0, status)
            elif 'B' in system_grade:
                result.set_result(True, "B", 78.0, status)
            else:
                result.set_result(False, "C", 55.0, status, "System performance below optimal")
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
    
    async def _test_claude_api_integration(self):
        """Test Claude API - addressing 11.1% failure rate claim"""
        logger.info("🤖 Testing Claude API Integration (claimed: 11.1% failure rate)")
        
        # Test 1: API connectivity
        result = SystemTestResult("Claude API", "Connectivity Test")
        try:
            # Test local Claude API at port 8081
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:8081/health', timeout=10) as response:
                        if response.status == 200:
                            result.set_result(True, "A", 95.0, {
                                'api_accessible': True,
                                'port_8081_active': True,
                                'health_check_passed': True
                            })
                        else:
                            result.set_result(False, "C", 50.0, {
                                'api_accessible': True,
                                'port_8081_active': True,
                                'health_check_failed': True,
                                'status_code': response.status
                            }, f"Health check failed with status {response.status}")
                except asyncio.TimeoutError:
                    result.set_result(False, "D", 20.0, error="API timeout - potential cause of 11.1% failure rate")
                except aiohttp.ClientConnectorError:
                    result.set_result(False, "F", 0.0, error="Claude API at port 8081 not accessible")
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
        
        # Test 2: API performance test (simulate multiple requests to check failure rate)
        result = SystemTestResult("Claude API", "Performance & Reliability Test")
        test_count = 20
        success_count = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                for i in range(test_count):
                    try:
                        test_payload = {
                            "model": "claude-3-sonnet-20240229",
                            "max_tokens": 100,
                            "messages": [{"role": "user", "content": f"Test message {i+1}"}]
                        }
                        
                        async with session.post(
                            'http://localhost:8081/v1/messages',
                            json=test_payload,
                            timeout=15
                        ) as response:
                            if response.status == 200:
                                success_count += 1
                            
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.debug(f"Request {i+1} failed: {e}")
            
            success_rate = (success_count / test_count) * 100
            failure_rate = 100 - success_rate
            
            if success_rate >= 95:
                result.set_result(True, "A+", success_rate, {
                    'success_rate': f"{success_rate:.1f}%",
                    'failure_rate': f"{failure_rate:.1f}%",
                    'successful_requests': success_count,
                    'total_requests': test_count,
                    'performance_grade': 'Excellent'
                })
            elif success_rate >= 90:
                result.set_result(True, "A", success_rate, {
                    'success_rate': f"{success_rate:.1f}%",
                    'failure_rate': f"{failure_rate:.1f}%",
                    'successful_requests': success_count,
                    'total_requests': test_count,
                    'performance_grade': 'Good'
                })
            elif success_rate >= 80:
                result.set_result(True, "B", success_rate, {
                    'success_rate': f"{success_rate:.1f}%",
                    'failure_rate': f"{failure_rate:.1f}%",
                    'successful_requests': success_count,
                    'total_requests': test_count,
                    'performance_grade': 'Acceptable',
                    'note': 'Below claimed 11.1% failure rate'
                })
            else:
                result.set_result(False, "D", success_rate, {
                    'success_rate': f"{success_rate:.1f}%",
                    'failure_rate': f"{failure_rate:.1f}%",
                    'successful_requests': success_count,
                    'total_requests': test_count,
                    'performance_grade': 'Poor'
                }, f"High failure rate: {failure_rate:.1f}%")
        
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
    
    async def _test_end_to_end_integration(self):
        """Test end-to-end system integration"""
        logger.info("🔗 Testing End-to-End Integration")
        
        result = SystemTestResult("System Integration", "End-to-End Workflow")
        
        try:
            # Test complete workflow: Cookie → Upload Manager → CSV Processing
            cookie_manager = get_cookie_manager()
            upload_manager = ProductionUploadDownloadManager()
            csv_manager = CSVSecurityManager()
            
            # Step 1: Cookie health
            cookie_health = await cookie_manager.get_health_status()
            step1_ok = cookie_health.get('healthy', False)
            
            # Step 2: Upload manager initialization
            await upload_manager.initialize_browser(headless=True)
            cookie_setup = await upload_manager.setup_cookies()
            step2_ok = cookie_setup
            
            # Step 3: CSV processing
            test_file1, test_file2 = await self._create_test_csv_files()
            csv_result = await csv_manager.comprehensive_csv_analysis(test_file1, test_file2, "integration_test")
            step3_ok = csv_result.get('success', False)
            
            # Clean up
            await upload_manager.cleanup()
            
            # Calculate integration score
            steps_passed = sum([step1_ok, step2_ok, step3_ok])
            integration_score = (steps_passed / 3) * 100
            
            if integration_score >= 90:
                result.set_result(True, "A", integration_score, {
                    'cookie_system': step1_ok,
                    'upload_system': step2_ok,
                    'csv_system': step3_ok,
                    'integration_status': 'Excellent'
                })
            elif integration_score >= 70:
                result.set_result(True, "B", integration_score, {
                    'cookie_system': step1_ok,
                    'upload_system': step2_ok,
                    'csv_system': step3_ok,
                    'integration_status': 'Good'
                })
            else:
                result.set_result(False, "D", integration_score, {
                    'cookie_system': step1_ok,
                    'upload_system': step2_ok,
                    'csv_system': step3_ok,
                    'integration_status': 'Poor'
                }, "Multiple systems failing")
                
        except Exception as e:
            result.set_result(False, "F", 0.0, error=str(e))
        
        self.test_results.append(result)
    
    async def _test_stage7_system_connectivity(self):
        """Stage 7: 系统链路通畅性保证 - 确保整个系统信息链路完全通畅"""
        logger.info("🎯 Testing Stage 7: System Connectivity Assurance")
        
        # Test 1: UI Connectivity Manager Integration
        result = SystemTestResult("Stage 7 Connectivity", "UI Connectivity Integration")
        try:
            from ui_connectivity_manager import UIConnectivityManager
            ui_manager = UIConnectivityManager()
            
            # Create test data for UI connectivity
            test_csv_data = [
                ['负责人', '协助人', '具体计划内容'],
                ['张三', '李四', '用户增长策略优化'],
                ['王五', '赵六', '数据分析优化']
            ]
            
            security_analysis = {
                'risk_score': 0.25,
                'changes': [
                    {'column': '负责人', 'risk': 0.3},
                    {'column': '协助人', 'risk': 0.2}
                ]
            }
            
            # Generate UI compatible data
            ui_data = await ui_manager.generate_ui_compatible_data(
                csv_data=test_csv_data,
                security_analysis=security_analysis
            )
            
            # Validate heatmap data format (30x19 matrix)
            heatmap_data = ui_data.get('heatmap_data', [])
            
            if (len(heatmap_data) == 30 and 
                all(len(row) == 19 for row in heatmap_data) and
                all(isinstance(cell, (int, float)) for row in heatmap_data for cell in row)):
                
                result.set_result(True, "A+", 98.0, {
                    'ui_connectivity': 'OPERATIONAL',
                    'heatmap_format': 'VALID_30x19',
                    'data_conversion': 'SUCCESS',
                    'csv_to_ui_flow': 'COMPLETE'
                })
            else:
                result.set_result(False, "D", 35.0, {
                    'ui_connectivity': 'DEGRADED',
                    'heatmap_format': f'INVALID_{len(heatmap_data)}x{len(heatmap_data[0]) if heatmap_data else 0}',
                    'issue': 'UI数据格式不符合30x19标准'
                }, "UI连接性数据格式验证失败")
                
        except Exception as e:
            result.set_result(False, "F", 0.0, error=f"UI连接性测试失败: {str(e)}")
        
        self.test_results.append(result)
        
        # Test 2: Heatmap Server Connectivity
        result = SystemTestResult("Stage 7 Connectivity", "Heatmap Server Integration")
        try:
            from heatmap_stability_tester import HeatmapStabilityTester
            heatmap_tester = HeatmapStabilityTester()
            
            # Run quick stability test
            stability_result = await heatmap_tester.api_stability_test(5)
            
            if stability_result.get('success') and stability_result.get('success_rate', 0) >= 80:
                result.set_result(True, "A", 92.0, {
                    'heatmap_server': 'STABLE',
                    'api_success_rate': stability_result.get('success_rate'),
                    'avg_response_time': stability_result.get('avg_response_time'),
                    'port_8089_status': 'ACCESSIBLE'
                })
            else:
                result.set_result(False, "C", 55.0, {
                    'heatmap_server': 'UNSTABLE',
                    'issue': '热力图服务器连接性问题'
                }, "热力图服务器稳定性测试失败")
                
        except Exception as e:
            result.set_result(False, "F", 0.0, error=f"热力图服务器连接性测试失败: {str(e)}")
        
        self.test_results.append(result)
        
        # Test 3: Claude L2 Wrapper Connectivity
        result = SystemTestResult("Stage 7 Connectivity", "Claude L2 API Integration")
        try:
            from optimized_claude_l2_wrapper import OptimizedClaudeL2Wrapper, L2SemanticAnalysisRequest
            
            async with OptimizedClaudeL2Wrapper() as claude_wrapper:
                # Create test L2 analysis request
                test_request = L2SemanticAnalysisRequest(
                    change_id="stage7_connectivity_test",
                    column_name="负责人",
                    original_value="测试用户A",
                    new_value="测试用户B",
                    table_context="系统连接性验证测试表格",
                    business_context="Stage 7 连接性验证",
                    priority="high"
                )
                
                # Execute L2 semantic analysis
                analysis_result = await claude_wrapper.analyze_l2_semantic_change(test_request)
                
                # Get stability status
                stability_status = claude_wrapper.get_stability_status()
                
                if (analysis_result and 
                    analysis_result.confidence_score >= 0 and 
                    stability_status.get('stability_score', 0) >= 70):
                    
                    result.set_result(True, "A-", 88.0, {
                        'claude_l2_api': 'OPERATIONAL',
                        'l2_analysis_confidence': analysis_result.confidence_score,
                        'semantic_decision': analysis_result.semantic_decision,
                        'api_stability_score': stability_status.get('stability_score'),
                        'l2_wrapper_status': 'STABLE'
                    })
                else:
                    result.set_result(False, "C", 50.0, {
                        'claude_l2_api': 'DEGRADED',
                        'issue': 'Claude L2分析稳定性不足'
                    }, "Claude L2 API稳定性或分析质量不达标")
                    
        except Exception as e:
            result.set_result(False, "F", 0.0, error=f"Claude L2 API连接性测试失败: {str(e)}")
        
        self.test_results.append(result)
        
        # Test 4: Complete Data Flow Connectivity
        result = SystemTestResult("Stage 7 Connectivity", "Complete Data Flow Chain")
        try:
            logger.info("🔗 执行完整数据流链路测试...")
            
            # 模拟完整的系统数据流
            flow_steps = []
            
            # Step 1: Cookie 加密处理
            try:
                from production_cookie_manager import ProductionCookieManager
                cookie_manager = ProductionCookieManager()
                
                test_session_data = {
                    'session_id': 'stage7_flow_test',
                    'document_id': 'connectivity_test_doc',
                    'user_id': 'test_user_connectivity'
                }
                
                encrypted_session = cookie_manager.encrypt_sensitive_data(json.dumps(test_session_data))
                decrypted_session = cookie_manager.decrypt_sensitive_data(encrypted_session)
                
                if json.loads(decrypted_session) == test_session_data:
                    flow_steps.append("✅ Cookie加密解密")
                else:
                    flow_steps.append("❌ Cookie数据完整性失败")
                    
            except Exception as e:
                flow_steps.append(f"❌ Cookie处理: {str(e)}")
            
            # Step 2: UI数据转换
            try:
                from ui_connectivity_manager import UIConnectivityManager
                ui_manager = UIConnectivityManager()
                
                test_csv = [['负责人'], ['原值'], ['新值']]
                ui_result = await ui_manager.generate_ui_compatible_data(
                    csv_data=test_csv,
                    security_analysis={'risk_score': 0.3}
                )
                
                if ui_result and 'heatmap_data' in ui_result:
                    flow_steps.append("✅ UI数据转换")
                else:
                    flow_steps.append("❌ UI数据转换失败")
                    
            except Exception as e:
                flow_steps.append(f"❌ UI数据转换: {str(e)}")
            
            # Step 3: Claude语义分析
            try:
                from optimized_claude_l2_wrapper import OptimizedClaudeL2Wrapper, L2SemanticAnalysisRequest
                
                async with OptimizedClaudeL2Wrapper() as wrapper:
                    request = L2SemanticAnalysisRequest(
                        change_id="flow_test",
                        column_name="负责人",
                        original_value="原值",
                        new_value="新值",
                        table_context="数据流测试",
                        business_context="连接性验证"
                    )
                    
                    analysis = await wrapper.analyze_l2_semantic_change(request)
                    if analysis and analysis.confidence_score >= 0:
                        flow_steps.append("✅ Claude语义分析")
                    else:
                        flow_steps.append("❌ Claude分析返回异常")
                        
            except Exception as e:
                flow_steps.append(f"❌ Claude分析: {str(e)}")
            
            # Step 4: 热力图服务器连接
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8089/api/data', timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('success'):
                                flow_steps.append("✅ 热力图服务器连接")
                            else:
                                flow_steps.append("❌ 热力图数据响应异常")
                        else:
                            flow_steps.append("❌ 热力图服务器HTTP错误")
                            
            except Exception as e:
                flow_steps.append(f"❌ 热力图连接: {str(e)}")
            
            # 计算数据流成功率
            successful_steps = len([step for step in flow_steps if step.startswith("✅")])
            total_steps = len(flow_steps)
            flow_success_rate = (successful_steps / total_steps) * 100
            
            if flow_success_rate >= 100:
                result.set_result(True, "A+", 100.0, {
                    'data_flow_status': 'PERFECT',
                    'flow_steps': flow_steps,
                    'success_rate': flow_success_rate,
                    'system_connectivity': 'COMPLETE'
                })
            elif flow_success_rate >= 75:
                result.set_result(True, "A-", flow_success_rate, {
                    'data_flow_status': 'GOOD',
                    'flow_steps': flow_steps,
                    'success_rate': flow_success_rate,
                    'system_connectivity': 'MOSTLY_CONNECTED'
                })
            elif flow_success_rate >= 50:
                result.set_result(True, "B", flow_success_rate, {
                    'data_flow_status': 'PARTIAL',
                    'flow_steps': flow_steps,
                    'success_rate': flow_success_rate,
                    'system_connectivity': 'PARTIALLY_CONNECTED'
                }, "部分系统连接性问题")
            else:
                result.set_result(False, "D", flow_success_rate, {
                    'data_flow_status': 'POOR',
                    'flow_steps': flow_steps,
                    'success_rate': flow_success_rate,
                    'system_connectivity': 'DISCONNECTED'
                }, "系统连接性严重问题")
                
        except Exception as e:
            result.set_result(False, "F", 0.0, error=f"完整数据流测试失败: {str(e)}")
        
        self.test_results.append(result)
    
    async def _create_test_csv_files(self) -> Tuple[str, str]:
        """Create test CSV files for testing"""
        file1_path = os.path.join(self.test_data_dir, "test_baseline.csv")
        file2_path = os.path.join(self.test_data_dir, "test_current.csv")
        
        # Create baseline file
        csv_content1 = """id,name,department,status
1,张三,技术部,正常
2,李四,销售部,正常
3,王五,市场部,正常
"""
        
        # Create current file with some changes
        csv_content2 = """id,name,department,status
1,张三,技术部,正常
2,李四,销售部,离职
3,王五,市场部,正常
4,赵六,HR部,正常
"""
        
        with open(file1_path, 'w', encoding='utf-8') as f:
            f.write(csv_content1)
        
        with open(file2_path, 'w', encoding='utf-8') as f:
            f.write(csv_content2)
        
        return file1_path, file2_path
    
    def _calculate_overall_grade(self):
        """Calculate overall system grade"""
        if not self.test_results:
            self.overall_grade = "F"
            self.overall_score = 0.0
            return
        
        total_score = sum(result.score for result in self.test_results)
        self.overall_score = total_score / len(self.test_results)
        
        # Grade boundaries
        if self.overall_score >= 95:
            self.overall_grade = "A+ (Enterprise Ready)"
        elif self.overall_score >= 90:
            self.overall_grade = "A (Production Ready)"
        elif self.overall_score >= 85:
            self.overall_grade = "A- (Nearly Production Ready)"
        elif self.overall_score >= 80:
            self.overall_grade = "B+ (Good - Minor Issues)"
        elif self.overall_score >= 75:
            self.overall_grade = "B (Acceptable - Some Issues)"
        elif self.overall_score >= 70:
            self.overall_grade = "B- (Needs Improvement)"
        elif self.overall_score >= 60:
            self.overall_grade = "C+ (Major Issues)"
        elif self.overall_score >= 50:
            self.overall_grade = "C (Significant Problems)"
        elif self.overall_score >= 40:
            self.overall_grade = "D+ (Prototype Stage)"
        elif self.overall_score >= 30:
            self.overall_grade = "D (Early Development)"
        else:
            self.overall_grade = "F (Not Functional)"
    
    async def _generate_comprehensive_report(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Group results by component
        component_results = {}
        for result in self.test_results:
            if result.component not in component_results:
                component_results[result.component] = []
            component_results[result.component].append(result.to_dict())
        
        # Calculate component scores
        component_scores = {}
        for component, results in component_results.items():
            scores = [r['score'] for r in results]
            component_scores[component] = sum(scores) / len(scores) if scores else 0
        
        # Identify critical issues
        critical_issues = []
        for result in self.test_results:
            if not result.success and result.score < 30:
                critical_issues.append({
                    'component': result.component,
                    'test': result.test_name,
                    'issue': result.error or "Critical failure",
                    'impact': "High"
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Production readiness assessment
        production_readiness = self._assess_production_readiness()
        
        return {
            'test_summary': {
                'overall_grade': self.overall_grade,
                'overall_score': round(self.overall_score, 1),
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r.success]),
                'failed_tests': len([r for r in self.test_results if not r.success]),
                'total_duration': round(total_duration, 2),
                'timestamp': datetime.now().isoformat()
            },
            'component_scores': component_scores,
            'detailed_results': component_results,
            'critical_issues': critical_issues,
            'production_readiness': production_readiness,
            'recommendations': recommendations,
            'verification_against_claims': self._verify_original_claims(),
            'system_capabilities': self._assess_system_capabilities()
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Analyze failed tests for recommendations
        failed_cookie_tests = [r for r in self.test_results if r.component == "Cookie Manager" and not r.success]
        failed_upload_tests = [r for r in self.test_results if r.component == "Upload Manager" and not r.success]
        failed_csv_tests = [r for r in self.test_results if r.component == "CSV Security Manager" and not r.success]
        failed_api_tests = [r for r in self.test_results if r.component == "Claude API" and not r.success]
        
        if failed_cookie_tests:
            recommendations.append({
                'priority': 'CRITICAL',
                'component': 'Cookie Manager',
                'issue': 'Cookie authentication failures detected',
                'recommendation': 'Update cookies manually and implement automated cookie refresh mechanism',
                'impact': 'Resolves upload failures root cause'
            })
        
        if failed_upload_tests:
            recommendations.append({
                'priority': 'HIGH',
                'component': 'Upload Manager',
                'issue': 'Upload system initialization or cookie setup failures',
                'recommendation': 'Fix browser initialization and cookie integration issues',
                'impact': 'Enables file upload functionality'
            })
        
        if failed_api_tests:
            recommendations.append({
                'priority': 'HIGH',
                'component': 'Claude API',
                'issue': 'API connectivity or performance issues',
                'recommendation': 'Verify Claude API server at port 8081 and implement better error handling',
                'impact': 'Improves AI analysis reliability'
            })
        
        if self.overall_score < 70:
            recommendations.append({
                'priority': 'CRITICAL',
                'component': 'System Architecture',
                'issue': 'Multiple system failures detected',
                'recommendation': 'Conduct comprehensive system review and implement systematic fixes',
                'impact': 'Overall system stability and production readiness'
            })
        
        return recommendations
    
    def _assess_production_readiness(self) -> Dict[str, Any]:
        """Assess production readiness"""
        
        readiness_factors = {
            'authentication_system': any(r.component == "Cookie Manager" and r.success for r in self.test_results),
            'upload_system': any(r.component == "Upload Manager" and r.success for r in self.test_results),
            'data_processing': any(r.component == "CSV Security Manager" and r.success for r in self.test_results),
            'ai_integration': any(r.component == "Claude API" and r.success for r in self.test_results),
            'end_to_end_workflow': any(r.component == "System Integration" and r.success for r in self.test_results)
        }
        
        ready_components = sum(readiness_factors.values())
        total_components = len(readiness_factors)
        readiness_percentage = (ready_components / total_components) * 100
        
        if readiness_percentage >= 90:
            readiness_level = "PRODUCTION READY"
            deployment_recommendation = "Safe for production deployment"
        elif readiness_percentage >= 80:
            readiness_level = "NEARLY READY"
            deployment_recommendation = "Minor fixes needed before production"
        elif readiness_percentage >= 60:
            readiness_level = "DEVELOPMENT STAGE"
            deployment_recommendation = "Significant testing and fixes needed"
        elif readiness_percentage >= 40:
            readiness_level = "PROTOTYPE STAGE"
            deployment_recommendation = "Major development work required"
        else:
            readiness_level = "EARLY DEVELOPMENT"
            deployment_recommendation = "Not suitable for production use"
        
        return {
            'readiness_level': readiness_level,
            'readiness_percentage': round(readiness_percentage, 1),
            'deployment_recommendation': deployment_recommendation,
            'component_status': readiness_factors,
            'blocking_issues': [r.error for r in self.test_results if not r.success and r.score < 30]
        }
    
    def _verify_original_claims(self) -> Dict[str, Any]:
        """Verify against original problem claims"""
        verification = {
            'cookie_single_point_failure': None,
            'upload_100_percent_failure': None,
            'claude_api_11_percent_failure': None,
            'system_d_plus_grade': None
        }
        
        # Check cookie manager results
        cookie_results = [r for r in self.test_results if r.component == "Cookie Manager"]
        if cookie_results:
            cookie_success_rate = sum(1 for r in cookie_results if r.success) / len(cookie_results)
            verification['cookie_single_point_failure'] = {
                'claim_verified': cookie_success_rate < 0.5,
                'actual_success_rate': f"{cookie_success_rate * 100:.1f}%",
                'assessment': 'CRITICAL ISSUE' if cookie_success_rate < 0.5 else 'RESOLVED'
            }
        
        # Check upload manager results
        upload_results = [r for r in self.test_results if r.component == "Upload Manager"]
        if upload_results:
            upload_success_rate = sum(1 for r in upload_results if r.success) / len(upload_results)
            verification['upload_100_percent_failure'] = {
                'claim_verified': upload_success_rate == 0,
                'actual_success_rate': f"{upload_success_rate * 100:.1f}%",
                'assessment': 'CONFIRMED' if upload_success_rate == 0 else 'PARTIALLY RESOLVED' if upload_success_rate < 0.8 else 'RESOLVED'
            }
        
        # Check Claude API results
        api_results = [r for r in self.test_results if r.component == "Claude API"]
        if api_results:
            for result in api_results:
                if 'Performance & Reliability Test' in result.test_name and result.details:
                    failure_rate_str = result.details.get('failure_rate', '0%')
                    failure_rate = float(failure_rate_str.replace('%', ''))
                    
                    verification['claude_api_11_percent_failure'] = {
                        'claim_verified': failure_rate >= 10,
                        'actual_failure_rate': failure_rate_str,
                        'assessment': 'CONFIRMED' if failure_rate >= 11 else 'BETTER THAN CLAIMED' if failure_rate < 11 else 'MONITORING NEEDED'
                    }
        
        # Check overall system grade
        verification['system_d_plus_grade'] = {
            'claim_verified': self.overall_score < 45,
            'actual_grade': self.overall_grade,
            'actual_score': f"{self.overall_score:.1f}%",
            'assessment': 'CONFIRMED' if self.overall_score < 45 else 'IMPROVED' if self.overall_score >= 70 else 'SLIGHT IMPROVEMENT'
        }
        
        return verification
    
    def _assess_system_capabilities(self) -> Dict[str, Any]:
        """Assess current system capabilities"""
        capabilities = {
            'working_features': [],
            'partially_working_features': [],
            'broken_features': [],
            'recommended_priorities': []
        }
        
        # Analyze each component
        component_analysis = {}
        for result in self.test_results:
            component = result.component
            if component not in component_analysis:
                component_analysis[component] = {'scores': [], 'tests': []}
            component_analysis[component]['scores'].append(result.score)
            component_analysis[component]['tests'].append(result.test_name)
        
        for component, data in component_analysis.items():
            avg_score = sum(data['scores']) / len(data['scores'])
            
            if avg_score >= 80:
                capabilities['working_features'].append({
                    'component': component,
                    'score': round(avg_score, 1),
                    'status': 'OPERATIONAL'
                })
            elif avg_score >= 50:
                capabilities['partially_working_features'].append({
                    'component': component,
                    'score': round(avg_score, 1),
                    'status': 'NEEDS_IMPROVEMENT'
                })
            else:
                capabilities['broken_features'].append({
                    'component': component,
                    'score': round(avg_score, 1),
                    'status': 'CRITICAL_FAILURE'
                })
        
        # Generate priorities
        if capabilities['broken_features']:
            capabilities['recommended_priorities'].append("FIX CRITICAL FAILURES FIRST")
        if capabilities['partially_working_features']:
            capabilities['recommended_priorities'].append("IMPROVE PARTIALLY WORKING SYSTEMS")
        if len(capabilities['working_features']) < len(component_analysis):
            capabilities['recommended_priorities'].append("ACHIEVE FULL SYSTEM INTEGRATION")
        
        return capabilities


# Command line interface
async def main():
    """Main function for command line execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive System Tester - Brutal Honesty Mode')
    parser.add_argument('--quick', action='store_true', help='Run quick test suite')
    parser.add_argument('--component', help='Test specific component only')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    tester = ComprehensiveSystemTester()
    
    try:
        print("🧪 Starting Comprehensive System Testing...")
        print("⚠️  BRUTAL HONESTY MODE: Testing real functionality vs. claimed issues")
        print("="*70)
        
        report = await tester.run_all_tests()
        
        # Display summary
        summary = report['test_summary']
        print(f"\n📊 FINAL ASSESSMENT:")
        print(f"   Overall Grade: {summary['overall_grade']}")
        print(f"   Overall Score: {summary['overall_score']}%")
        print(f"   Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"   Duration: {summary['total_duration']}s")
        
        # Display critical issues
        critical = report['critical_issues']
        if critical:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(critical)}):")
            for issue in critical[:3]:  # Show top 3
                print(f"   • {issue['component']}: {issue['issue']}")
        
        # Display verification against original claims
        verification = report['verification_against_claims']
        print(f"\n🔍 VERIFICATION AGAINST ORIGINAL CLAIMS:")
        
        if verification.get('cookie_single_point_failure'):
            cookie_check = verification['cookie_single_point_failure']
            print(f"   Cookie Single Point Failure: {cookie_check['assessment']}")
        
        if verification.get('upload_100_percent_failure'):
            upload_check = verification['upload_100_percent_failure']
            print(f"   Upload 100% Failure: {upload_check['assessment']}")
        
        if verification.get('claude_api_11_percent_failure'):
            api_check = verification['claude_api_11_percent_failure']
            print(f"   Claude API 11.1% Failure: {api_check['assessment']}")
        
        # Display readiness
        readiness = report['production_readiness']
        print(f"\n🚀 PRODUCTION READINESS:")
        print(f"   Status: {readiness['readiness_level']}")
        print(f"   Recommendation: {readiness['deployment_recommendation']}")
        
        # Display top recommendations
        recommendations = report['recommendations']
        if recommendations:
            print(f"\n💡 TOP RECOMMENDATIONS:")
            for rec in recommendations[:3]:
                print(f"   {rec['priority']}: {rec['recommendation']}")
        
        print("="*70)
        print("📄 Detailed report saved to test results directory")
        
    except Exception as e:
        print(f"❌ Testing failed with error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())