#!/usr/bin/env python3
"""
实际功能测试脚本 - 基于真实测试结果
"""

import requests
import json
import asyncio
import sys
import time
from datetime import datetime

def test_claude_wrapper_direct():
    """直接测试Claude封装程序"""
    print("🧪 测试1: Claude封装程序直接调用")
    
    try:
        # 健康检查
        health_resp = requests.get("http://localhost:8081/health", timeout=10)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            print(f"   ✅ 健康检查: {health_data['status']}")
            print(f"   📊 API成功率: {health_data['api_stats']['success_rate']:.1f}%")
            print(f"   🤖 可用模型: {len(health_data['models_available'])}个")
        else:
            print(f"   ❌ 健康检查失败: HTTP {health_resp.status_code}")
            return False

        # AI分析测试
        start_time = time.time()
        analysis_resp = requests.post(
            "http://localhost:8081/analyze",
            json={
                "content": "项目负责人从张三变更为李四，需要重新安排工作分配",
                "analysis_type": "risk_assessment",
                "context": {"table_name": "项目管理表", "column_name": "负责人"}
            },
            timeout=30
        )
        
        if analysis_resp.status_code == 200:
            analysis_data = analysis_resp.json()
            actual_time = time.time() - start_time
            print(f"   ✅ AI分析成功")
            print(f"   🎯 置信度: {analysis_data.get('confidence', 0)}")
            print(f"   ⚠️  风险等级: {analysis_data.get('risk_level', 'N/A')}")
            print(f"   ⏱️  实际响应时间: {actual_time:.1f}秒")
            print(f"   📝 分析结果长度: {len(analysis_data.get('result', ''))}")
            return True
        else:
            print(f"   ❌ AI分析失败: HTTP {analysis_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False

def test_main_system_health():
    """测试主系统健康状态"""
    print("\n🧪 测试2: 主系统健康状态")
    
    try:
        resp = requests.get("http://localhost:5000/api/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ 主系统状态: {data['status']}")
            print(f"   🤖 AI分析器: {data['component_status']['ai_analyzer']}")
            print(f"   🎨 Excel可视化: {data['component_status']['excel_visualizer']}")
            print(f"   💾 数据库: {data['component_status']['database']}")
            
            stats = data['system_stats']
            print(f"   📊 总分析: {stats['total_analyses']}")
            print(f"   ✅ 成功分析: {stats['successful_analyses']}")
            print(f"   🚀 运行时间: {stats['uptime_hours']:.1f}小时")
            return True
        else:
            print(f"   ❌ 主系统健康检查失败: HTTP {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False

def test_integration_adapter():
    """测试集成适配器"""
    print("\n🧪 测试3: 集成适配器功能")
    
    try:
        # 导入集成模块
        sys.path.append('/root/projects/tencent-doc-manager')
        from claude_wrapper_integration import ClaudeWrapperClient, ClaudeWrapperConfig, AISemanticAnalysisOrchestrator
        
        async def run_integration_test():
            # 测试直接客户端
            config = ClaudeWrapperConfig(base_url="http://localhost:8081")
            async with ClaudeWrapperClient(config) as client:
                health = await client.check_health()
                print(f"   ✅ 客户端健康检查: {health.get('status')}")
                
                # 单个分析
                analysis = await client.analyze_risk("协助人从李四改为王五")
                print(f"   ✅ 单个分析: 置信度{analysis.get('confidence', 0)}")
                
                # 批量分析测试
                modifications = [
                    {"modification_id": "test_1", "table_name": "测试表", "column_name": "负责人", 
                     "original_value": "张三", "new_value": "李四"},
                    {"modification_id": "test_2", "table_name": "测试表", "column_name": "具体计划内容",
                     "original_value": "原计划", "new_value": "新计划"}
                ]
                
                batch_results = await client.analyze_modification_batch(modifications)
                print(f"   ✅ 批量分析: 处理{len(batch_results)}个修改")
                successful_analyses = [r for r in batch_results if not r.get("error")]
                print(f"   📊 成功率: {len(successful_analyses)}/{len(batch_results)}")
                
                return len(successful_analyses) == len(batch_results)
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_integration_test())
            print(f"   🏆 集成适配器测试: {'通过' if success else '部分失败'}")
            return success
        finally:
            loop.close()
            
    except Exception as e:
        print(f"   ❌ 集成适配器测试异常: {e}")
        return False

def test_system_stats():
    """测试系统统计功能"""
    print("\n🧪 测试4: 系统统计功能")
    
    try:
        resp = requests.get("http://localhost:5000/api/v2/system/stats", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            stats = data['system_statistics']
            
            print(f"   ✅ 系统版本: {stats['service_info']['version']}")
            print(f"   👥 注册用户: {stats['users']['total_registered']}")
            print(f"   📋 总作业数: {stats['jobs']['total_jobs']}")
            
            components = stats['components']
            available_components = sum(1 for comp in components.values() if comp)
            print(f"   🔧 可用组件: {available_components}/{len(components)}")
            
            return True
        else:
            print(f"   ❌ 系统统计失败: HTTP {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False

def test_file_upload_basic():
    """测试基本文件上传功能"""
    print("\n🧪 测试5: 文件上传功能")
    
    try:
        # 测试简单的文件上传
        with open('test_modified.csv', 'rb') as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            data = {
                'username': 'integration_test_user',
                'enable_ai': 'false',  # 关闭AI减少复杂性
                'enable_visualization': 'false'
            }
            
            resp = requests.post(
                "http://localhost:5000/api/v2/analysis/single",
                files=files,
                data=data,
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ 文件上传成功")
                print(f"   📁 作业ID: {result.get('job_id', 'N/A')}")
                print(f"   ⚙️  配置: AI={result.get('config', {}).get('enable_ai_analysis', False)}")
                return True
            else:
                print(f"   ❌ 文件上传失败: HTTP {resp.status_code}")
                print(f"   📝 响应: {resp.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ 文件上传测试异常: {e}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 实际测试结果报告")
    print("="*60)
    
    test_names = [
        "Claude封装程序直接调用",
        "主系统健康状态", 
        "集成适配器功能",
        "系统统计功能",
        "文件上传功能"
    ]
    
    passed_tests = sum(1 for result in results if result)
    total_tests = len(results)
    
    print(f"🏆 测试总结: {passed_tests}/{total_tests} 通过")
    print(f"📈 成功率: {passed_tests/total_tests*100:.1f}%")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 详细结果:")
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {i+1}. {name}: {status}")
    
    # 结论
    if passed_tests == total_tests:
        print("\n🎉 所有核心功能测试通过，系统运行正常！")
        overall_status = "优秀"
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ 大部分功能正常，系统基本可用")
        overall_status = "良好"
    elif passed_tests >= total_tests * 0.6:
        print("\n⚠️  部分功能存在问题，需要修复")
        overall_status = "一般"
    else:
        print("\n❌ 系统存在严重问题，需要全面检查")
        overall_status = "差"
    
    print(f"🏅 系统评级: {overall_status}")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": passed_tests/total_tests*100,
        "overall_status": overall_status,
        "test_results": dict(zip(test_names, results)),
        "timestamp": datetime.now().isoformat()
    }

def main():
    print("🚀 开始Claude封装程序实际功能测试")
    print("基于真实运行环境的功能验证测试")
    print("="*60)
    
    # 执行所有测试
    results = []
    results.append(test_claude_wrapper_direct())
    results.append(test_main_system_health()) 
    results.append(test_integration_adapter())
    results.append(test_system_stats())
    results.append(test_file_upload_basic())
    
    # 生成测试报告
    report = generate_test_report(results)
    
    # 保存测试报告
    with open(f"actual_test_report_{int(time.time())}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

if __name__ == "__main__":
    main()