import requests
import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any
import concurrent.futures
from datetime import datetime

class ClaudeWrapperTestClient:
    """Claude封装服务测试客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> Dict[str, Any]:
        """测试健康检查接口"""
        print("🔍 测试健康检查接口...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 健康检查成功:")
            print(f"   状态: {result['status']}")
            print(f"   运行时间: {result['uptime']:.2f}秒")
            print(f"   代理URL: {result['proxy_url']}")
            print(f"   可用模型: {len(result['models_available'])}个")
            return result
        except Exception as e:
            print(f"❌ 健康检查失败: {str(e)}")
            return {}
    
    def test_models(self) -> Dict[str, Any]:
        """测试模型列表接口"""
        print("\n🔍 测试模型列表接口...")
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 模型列表获取成功:")
            print(f"   默认模型: {result['default_model']}")
            print(f"   可用模型:")
            for model in result['models']:
                print(f"     - {model['id']} ({model['type']})")
            return result
        except Exception as e:
            print(f"❌ 模型列表获取失败: {str(e)}")
            return {}
    
    def test_basic_chat(self) -> Dict[str, Any]:
        """测试基础聊天功能"""
        print("\n🔍 测试基础聊天功能...")
        try:
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/chat", json={
                "messages": [
                    {"role": "user", "content": "你好！请简单介绍一下你自己。"}
                ],
                "max_tokens": 100
            })
            response.raise_for_status()
            result = response.json()
            response_time = time.time() - start_time
            
            print(f"✅ 基础聊天测试成功:")
            print(f"   响应时间: {response_time:.2f}秒")
            print(f"   使用模型: {result['model']}")
            print(f"   响应内容: {result['choices'][0]['message']['content'][:100]}...")
            print(f"   Token使用: {result.get('usage', {})}")
            return result
        except Exception as e:
            print(f"❌ 基础聊天测试失败: {str(e)}")
            return {}
    
    def test_intelligent_analyze(self) -> Dict[str, Any]:
        """测试智能分析功能"""
        print("\n🔍 测试智能分析功能...")
        
        test_cases = [
            {
                "content": "项目负责人从张三改为李四",
                "analysis_type": "risk_assessment",
                "context": {"table_name": "项目管理表", "column": "负责人"}
            },
            {
                "content": "目标对齐从'提升用户体验'改为'降低运营成本'",
                "analysis_type": "risk_assessment", 
                "context": {"table_name": "目标管理表", "column": "目标对齐"}
            },
            {
                "content": "完成进度从60%更新为85%",
                "analysis_type": "content_analysis",
                "context": {"table_name": "进度跟踪表", "column": "完成进度"}
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases):
            try:
                start_time = time.time()
                response = self.session.post(f"{self.base_url}/analyze", json=test_case)
                response.raise_for_status()
                result = response.json()
                response_time = time.time() - start_time
                
                print(f"✅ 智能分析测试 {i+1} 成功:")
                print(f"   分析类型: {result['analysis_type']}")
                print(f"   风险等级: {result.get('risk_level', 'N/A')}")
                print(f"   置信度: {result['confidence']:.2f}")
                print(f"   处理时间: {response_time:.2f}秒")
                print(f"   分析结果: {result['result'][:150]}...")
                results.append(result)
                
            except Exception as e:
                print(f"❌ 智能分析测试 {i+1} 失败: {str(e)}")
        
        return results
    
    def test_batch_analyze(self) -> Dict[str, Any]:
        """测试批量分析功能"""
        print("\n🔍 测试批量分析功能...")
        
        batch_request = {
            "requests": [
                {
                    "content": "负责人：张三 → 李四",
                    "analysis_type": "risk_assessment",
                    "context": {"column": "负责人"}
                },
                {
                    "content": "预计完成时间：2025-08-15 → 2025-08-20",
                    "analysis_type": "risk_assessment", 
                    "context": {"column": "预计完成时间"}
                },
                {
                    "content": "重要程度：高 → 中",
                    "analysis_type": "risk_assessment",
                    "context": {"column": "重要程度"}
                }
            ],
            "parallel": True
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/batch", json=batch_request)
            response.raise_for_status()
            result = response.json()
            response_time = time.time() - start_time
            
            print(f"✅ 批量分析测试成功:")
            print(f"   总处理数量: {result['total_count']}")
            print(f"   成功数量: {result['success_count']}")
            print(f"   失败数量: {result['failed_count']}")
            print(f"   总处理时间: {response_time:.2f}秒")
            print(f"   平均处理时间: {response_time/result['total_count']:.2f}秒/个")
            return result
            
        except Exception as e:
            print(f"❌ 批量分析测试失败: {str(e)}")
            return {}
    
    def test_stream_chat(self) -> bool:
        """测试流式聊天功能"""
        print("\n🔍 测试流式聊天功能...")
        
        try:
            start_time = time.time()
            with self.session.post(f"{self.base_url}/chat/stream", json={
                "messages": [
                    {"role": "user", "content": "请写一个简短的关于AI技术发展的总结，大约100字。"}
                ],
                "max_tokens": 200
            }, stream=True) as response:
                
                response.raise_for_status()
                chunks_received = 0
                total_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                            try:
                                chunk_data = json.loads(line_str[6:])  # 去除 'data: '
                                if chunk_data.get('choices') and chunk_data['choices'][0].get('delta', {}).get('content'):
                                    content = chunk_data['choices'][0]['delta']['content']
                                    total_content += content
                                    chunks_received += 1
                            except json.JSONDecodeError:
                                continue
                
                response_time = time.time() - start_time
                print(f"✅ 流式聊天测试成功:")
                print(f"   接收块数: {chunks_received}")
                print(f"   总响应时间: {response_time:.2f}秒")
                print(f"   流式内容: {total_content[:200]}...")
                return True
                
        except Exception as e:
            print(f"❌ 流式聊天测试失败: {str(e)}")
            return False
    
    def test_concurrent_requests(self, concurrent_count: int = 10) -> Dict[str, Any]:
        """测试并发请求处理能力"""
        print(f"\n🔍 测试并发请求处理能力 ({concurrent_count}个并发)...")
        
        def single_request(request_id: int):
            try:
                start_time = time.time()
                response = requests.post(f"{self.base_url}/analyze", json={
                    "content": f"测试请求 #{request_id}: 负责人从张三改为李四",
                    "analysis_type": "risk_assessment",
                    "context": {"request_id": request_id}
                }, timeout=30)
                response.raise_for_status()
                response_time = time.time() - start_time
                return {
                    "request_id": request_id,
                    "success": True,
                    "response_time": response_time,
                    "result": response.json()
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": None
                }
        
        # 执行并发请求
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(single_request, i) for i in range(concurrent_count)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # 统计结果
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        print(f"✅ 并发测试完成:")
        print(f"   总请求数: {concurrent_count}")
        print(f"   成功请求数: {len(successful_requests)}")
        print(f"   失败请求数: {len(failed_requests)}")
        print(f"   总耗时: {total_time:.2f}秒")
        print(f"   平均响应时间: {avg_response_time:.2f}秒")
        print(f"   最快响应时间: {min_response_time:.2f}秒")
        print(f"   最慢响应时间: {max_response_time:.2f}秒")
        print(f"   吞吐量: {len(successful_requests)/total_time:.2f} 请求/秒")
        
        if failed_requests:
            print(f"⚠️ 失败请求详情:")
            for req in failed_requests[:3]:  # 只显示前3个失败请求
                print(f"   请求#{req['request_id']}: {req['error']}")
        
        return {
            "total_requests": concurrent_count,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "throughput": len(successful_requests)/total_time if total_time > 0 else 0
        }
    
    def run_comprehensive_tests(self):
        """运行完整的测试套件"""
        print("🧪 开始运行Claude封装程序完整测试套件")
        print("=" * 60)
        
        test_results = {}
        
        # 基础功能测试
        test_results["health"] = self.test_health()
        test_results["models"] = self.test_models()
        test_results["basic_chat"] = self.test_basic_chat()
        test_results["intelligent_analyze"] = self.test_intelligent_analyze()
        test_results["batch_analyze"] = self.test_batch_analyze()
        test_results["stream_chat"] = self.test_stream_chat()
        
        # 性能测试
        test_results["concurrent_10"] = self.test_concurrent_requests(10)
        test_results["concurrent_20"] = self.test_concurrent_requests(20)
        
        # 生成测试报告
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")
        print(f"   健康检查: {'✅' if test_results['health'] else '❌'}")
        print(f"   模型列表: {'✅' if test_results['models'] else '❌'}")
        print(f"   基础聊天: {'✅' if test_results['basic_chat'] else '❌'}")
        print(f"   智能分析: {'✅' if test_results['intelligent_analyze'] else '❌'}")
        print(f"   批量分析: {'✅' if test_results['batch_analyze'] else '❌'}")
        print(f"   流式聊天: {'✅' if test_results['stream_chat'] else '❌'}")
        print(f"   10并发测试: 成功率 {test_results['concurrent_10']['successful_requests']}/{test_results['concurrent_10']['total_requests']}")
        print(f"   20并发测试: 成功率 {test_results['concurrent_20']['successful_requests']}/{test_results['concurrent_20']['total_requests']}")
        
        return test_results

if __name__ == "__main__":
    # 创建测试客户端
    test_client = ClaudeWrapperTestClient()
    
    # 运行完整测试
    results = test_client.run_comprehensive_tests()
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"test_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 测试结果已保存到: test_results_{timestamp}.json")