#!/usr/bin/env python3
"""
Claude封装程序系统集成测试
验证Claude封装程序与腾讯文档管理系统的完整集成
"""

import asyncio
import requests
import json
import time
import pandas as pd
import os
from datetime import datetime
import tempfile

class SystemIntegrationTester:
    """系统集成测试器"""
    
    def __init__(self):
        self.claude_wrapper_url = "http://localhost:8081"
        self.main_system_url = "http://localhost:5000"
        self.test_results = {}
        
    def test_claude_wrapper_health(self) -> dict:
        """测试Claude封装程序健康状态"""
        try:
            response = requests.get(f"{self.claude_wrapper_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "success",
                    "claude_wrapper_healthy": health_data.get("status") == "healthy",
                    "models_available": len(health_data.get("models_available", [])),
                    "api_success_rate": health_data.get("api_stats", {}).get("success_rate", 0)
                }
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_main_system_health(self) -> dict:
        """测试主系统健康状态"""
        try:
            response = requests.get(f"{self.main_system_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                component_status = health_data.get("component_status", {})
                return {
                    "status": "success",
                    "main_system_healthy": health_data.get("status") == "healthy",
                    "ai_analyzer_available": component_status.get("ai_analyzer", False),
                    "system_stats": health_data.get("system_stats", {})
                }
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_integration_through_ai_analysis(self) -> dict:
        """通过AI分析测试系统集成"""
        try:
            # 创建测试CSV文件
            test_data = pd.DataFrame({
                "序号": [1, 2, 3],
                "项目类型": ["A类项目", "B类项目", "C类项目"],
                "负责人": ["张三", "李四", "王五"],
                "具体计划内容": ["原计划A", "原计划B", "原计划C"],
                "完成进度": ["50%", "75%", "25%"]
            })
            
            # 创建修改后的数据
            modified_data = test_data.copy()
            modified_data.loc[0, "负责人"] = "赵六"  # L2级别修改
            modified_data.loc[1, "具体计划内容"] = "新计划B"  # L2级别修改
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                test_data.to_csv(f.name, index=False, encoding='utf-8-sig')
                original_file = f.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                modified_data.to_csv(f.name, index=False, encoding='utf-8-sig')
                modified_file = f.name
            
            # 测试单文件分析
            start_time = time.time()
            with open(modified_file, 'rb') as f:
                files = {'file': ('test_modified.csv', f, 'text/csv')}
                data = {
                    'username': 'integration_test_user',
                    'enable_ai': 'true',
                    'enable_visualization': 'false'  # 关闭可视化以加快测试
                }
                
                response = requests.post(
                    f"{self.main_system_url}/api/v2/analysis/single",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            analysis_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id")
                
                # 等待分析完成
                max_wait_time = 120  # 最多等待2分钟
                wait_start = time.time()
                
                while time.time() - wait_start < max_wait_time:
                    status_response = requests.get(
                        f"{self.main_system_url}/api/v2/jobs/{job_id}/status",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        job_status = status_data.get("job_status", {}).get("status")
                        
                        if job_status == "completed":
                            # 获取分析结果
                            result_response = requests.get(
                                f"{self.main_system_url}/api/v2/jobs/{job_id}/result",
                                timeout=10
                            )
                            
                            if result_response.status_code == 200:
                                analysis_result = result_response.json()
                                
                                # 检查AI分析结果
                                ai_results = analysis_result.get("result", {}).get("ai_analysis_results", {})
                                individual_analyses = ai_results.get("individual_analyses", {})
                                
                                return {
                                    "status": "success",
                                    "job_id": job_id,
                                    "analysis_time": analysis_time,
                                    "processing_time": status_data.get("job_status", {}).get("processing_time_seconds", 0),
                                    "ai_analyses_count": len(individual_analyses),
                                    "ai_analysis_available": bool(individual_analyses),
                                    "sample_ai_result": list(individual_analyses.values())[0] if individual_analyses else None
                                }
                            else:
                                return {"status": "failed", "error": "无法获取分析结果"}
                        elif job_status == "failed":
                            error_msg = status_data.get("job_status", {}).get("error_message")
                            return {"status": "failed", "error": f"分析失败: {error_msg}"}
                    
                    time.sleep(2)
                
                return {"status": "timeout", "error": "分析超时"}
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            # 清理临时文件
            try:
                if 'original_file' in locals():
                    os.unlink(original_file)
                if 'modified_file' in locals():
                    os.unlink(modified_file)
            except:
                pass
    
    def test_direct_claude_wrapper_integration(self) -> dict:
        """直接测试Claude封装程序集成"""
        try:
            # 导入集成适配器
            import sys
            sys.path.append('/root/projects/tencent-doc-manager')
            
            from claude_wrapper_integration import ClaudeWrapperClient, ClaudeWrapperConfig
            
            async def run_integration_test():
                config = ClaudeWrapperConfig(base_url=self.claude_wrapper_url)
                
                async with ClaudeWrapperClient(config) as client:
                    # 健康检查
                    health = await client.check_health()
                    
                    # 单个风险分析
                    analysis = await client.analyze_risk(
                        "项目负责人从张三改为李四，需要重新分配工作任务",
                        {"table_name": "测试表格", "column_name": "负责人"}
                    )
                    
                    # 批量分析
                    modifications = [
                        {
                            "modification_id": "test_1",
                            "table_name": "项目管理表",
                            "column_name": "负责人",
                            "original_value": "张三",
                            "new_value": "李四"
                        },
                        {
                            "modification_id": "test_2", 
                            "table_name": "项目管理表",
                            "column_name": "具体计划内容",
                            "original_value": "原计划A",
                            "new_value": "新计划A"
                        }
                    ]
                    
                    batch_results = await client.analyze_modification_batch(modifications)
                    
                    return {
                        "health_check": health,
                        "single_analysis": analysis,
                        "batch_analysis": {
                            "total_processed": len(batch_results),
                            "successful_analyses": len([r for r in batch_results if not r.get("error")]),
                            "sample_result": batch_results[0] if batch_results else None
                        }
                    }
            
            # 运行异步测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_integration_test())
                return {"status": "success", "results": result}
            finally:
                loop.close()
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def run_complete_integration_test(self) -> dict:
        """运行完整的集成测试套件"""
        print("🚀 开始Claude封装程序系统集成测试")
        print("=" * 60)
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {}
        }
        
        # 1. Claude封装程序健康检查
        print("1. 🏥 测试Claude封装程序健康状态...")
        claude_health = self.test_claude_wrapper_health()
        test_results["claude_wrapper_health"] = claude_health
        print(f"   状态: {claude_health['status']}")
        
        # 2. 主系统健康检查
        print("2. 🏥 测试主系统健康状态...")
        main_health = self.test_main_system_health()
        test_results["main_system_health"] = main_health
        print(f"   状态: {main_health['status']}")
        
        # 3. 直接集成测试
        print("3. 🔗 测试直接集成适配器...")
        direct_integration = self.test_direct_claude_wrapper_integration()
        test_results["direct_integration"] = direct_integration
        print(f"   状态: {direct_integration['status']}")
        
        # 4. 端到端集成测试
        print("4. 🏁 测试端到端系统集成...")
        if claude_health.get("status") == "success" and main_health.get("status") == "success":
            e2e_integration = self.test_integration_through_ai_analysis()
            test_results["end_to_end_integration"] = e2e_integration
            print(f"   状态: {e2e_integration['status']}")
        else:
            print("   跳过：前置条件不满足")
            test_results["end_to_end_integration"] = {"status": "skipped", "reason": "前置健康检查失败"}
        
        # 生成测试总结
        test_results["test_summary"] = self._generate_test_summary(test_results)
        
        return test_results
    
    def _generate_test_summary(self, results: dict) -> dict:
        """生成测试总结"""
        summary = {
            "overall_status": "success",
            "successful_tests": 0,
            "total_tests": 0,
            "key_findings": [],
            "recommendations": []
        }
        
        tests = ["claude_wrapper_health", "main_system_health", "direct_integration", "end_to_end_integration"]
        
        for test_name in tests:
            if test_name in results:
                summary["total_tests"] += 1
                test_result = results[test_name]
                
                if test_result.get("status") in ["success", "skipped"]:
                    summary["successful_tests"] += 1
                else:
                    summary["overall_status"] = "partial_failure"
        
        # 分析关键发现
        claude_health = results.get("claude_wrapper_health", {})
        if claude_health.get("claude_wrapper_healthy"):
            summary["key_findings"].append("Claude封装程序运行正常")
        
        main_health = results.get("main_system_health", {})
        if main_health.get("ai_analyzer_available"):
            summary["key_findings"].append("主系统AI分析器集成成功")
        
        direct_test = results.get("direct_integration", {})
        if direct_test.get("status") == "success":
            summary["key_findings"].append("直接集成适配器工作正常")
        
        e2e_test = results.get("end_to_end_integration", {})
        if e2e_test.get("status") == "success":
            summary["key_findings"].append("端到端集成测试通过")
            if e2e_test.get("ai_analysis_available"):
                summary["key_findings"].append("AI分析功能完全集成")
        
        # 生成建议
        if summary["overall_status"] == "success":
            summary["recommendations"].append("系统集成完成，可以投入生产使用")
        else:
            summary["recommendations"].append("请检查失败的测试项并修复问题")
        
        return summary

def main():
    """主函数"""
    tester = SystemIntegrationTester()
    
    try:
        results = tester.run_complete_integration_test()
        
        # 输出详细结果
        print("\n" + "=" * 60)
        print("📊 集成测试结果详情")
        print("=" * 60)
        
        # 输出各项测试结果
        for test_name, test_result in results.items():
            if test_name in ["claude_wrapper_health", "main_system_health", "direct_integration", "end_to_end_integration"]:
                print(f"\n🧪 {test_name}:")
                if isinstance(test_result, dict):
                    for key, value in test_result.items():
                        if key != "results":  # 避免输出过长的结果
                            print(f"   {key}: {value}")
        
        # 输出测试总结
        summary = results.get("test_summary", {})
        print(f"\n" + "=" * 60)
        print("🎯 集成测试总结")
        print("=" * 60)
        print(f"🏆 总体状态: {summary.get('overall_status')}")
        print(f"📊 成功率: {summary.get('successful_tests')}/{summary.get('total_tests')}")
        
        print(f"\n🔍 关键发现:")
        for finding in summary.get("key_findings", []):
            print(f"  ✓ {finding}")
        
        print(f"\n📋 建议:")
        for rec in summary.get("recommendations", []):
            print(f"  • {rec}")
        
        # 保存结果
        result_file = f"integration_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {result_file}")
        print("\n🎉 系统集成测试完成!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ 集成测试执行失败: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    main()