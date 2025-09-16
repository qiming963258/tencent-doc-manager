#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的真实测试执行脚本
自动执行7阶段系统的端到端测试工作流
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import logging
from datetime import datetime
from ui_connectivity_manager import UIConnectivityManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """执行完整的真实测试工作流"""
    print("🎯 启动完整的7阶段系统真实测试...")
    print("=" * 70)
    
    try:
        # 初始化UI连接性管理器
        ui_manager = UIConnectivityManager()
        
        # 执行真实测试工作流
        print("🚀 开始执行端到端自动化测试工作流...")
        print("   包括: 下载→对比→涂色→上传→热力图更新")
        
        # 模拟测试链接（在实际环境中这些会是真实的腾讯文档链接）
        baseline_link = "https://docs.qq.com/sheet/baseline_test"
        current_link = "https://docs.qq.com/sheet/current_test"
        
        # 执行完整工作流
        result = await ui_manager.execute_real_test_workflow(
            test_link=current_link,
            baseline_link=baseline_link
        )
        
        # 显示结果
        if result['success']:
            print("\n🎉 完整测试工作流执行成功！")
            print("=" * 50)
            
            workflow = result['workflow_results']
            verification = result['final_verification']
            
            print("📋 各阶段执行状态:")
            print(f"  ✅ Step 1 - 文件下载: 基准版和当前版已获取")
            print(f"  ✅ Step 2 - CSV分析: {verification['changes_detected']}个变更检测")
            print(f"  ✅ Step 3 - MCP涂色: Excel文件自动着色完成")
            print(f"  ✅ Step 4 - 自动上传: {verification['uploaded_doc_link']}")
            print(f"  ✅ Step 5 - 热力图生成: 30x19矩阵数据生成")
            print(f"  ✅ Step 6 - UI实时刷新: {'成功' if verification['ui_update_success'] else '失败'}")
            
            print(f"\n🌡️ 最终验证结果:")
            print(f"   热力图URL: {verification['heatmap_url']}")
            print(f"   检测变更: {verification['changes_detected']}个")
            print(f"   UI更新状态: {'✅ 成功' if verification['ui_update_success'] else '❌ 失败'}")
            
            # 验证热力图是否确实更新了
            await verify_heatmap_update()
            
        else:
            print(f"\n❌ 测试工作流执行失败: {result.get('error')}")
            
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        import traceback
        traceback.print_exc()


async def verify_heatmap_update():
    """验证热力图是否真实更新"""
    try:
        import aiohttp
        
        print("\n🔍 验证热力图服务器更新状态...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8089/api/data', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    data_source = data.get('data', {}).get('data_source', 'unknown')
                    changes_applied = data.get('data', {}).get('processing_info', {}).get('changes_applied', 0)
                    algorithm = data.get('data', {}).get('processing_info', {}).get('matrix_generation_algorithm', 'unknown')
                    
                    print(f"🎯 热力图服务器验证结果:")
                    print(f"   数据源: {data_source}")
                    print(f"   应用变更: {changes_applied}个")
                    print(f"   算法版本: {algorithm}")
                    
                    # 检查是否使用了真实测试数据
                    if 'real' in data_source.lower():
                        print("   ✅ 确认使用真实测试数据!")
                        
                        # 显示热力图矩阵的关键区域
                        matrix = data.get('data', {}).get('heatmap_data', [])
                        if matrix and len(matrix) >= 6:
                            print(f"\n🔥 当前热力图状态 (前6行):")
                            for i in range(6):
                                if i < len(matrix) and len(matrix[i]) >= 10:
                                    row_data = [f'{x:.2f}' for x in matrix[i][:10]]
                                    heat_indicator = '🔴' if max(matrix[i][:10]) > 0.8 else '🟡' if max(matrix[i][:10]) > 0.5 else '🟢'
                                    print(f"     第{i+1}行: [{' '.join(row_data)}...] {heat_indicator}")
                        
                        return True
                    else:
                        print("   ⚠️  仍在使用默认数据，测试数据未生效")
                        return False
                else:
                    print(f"   ❌ 热力图服务器响应失败: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ 热力图验证失败: {e}")
        return False


if __name__ == "__main__":
    print("🎯 7阶段系统完整测试执行器")
    print(f"   执行时间: {datetime.now().isoformat()}")
    print(f"   测试目标: 完整端到端自动化工作流")
    print()
    
    # 执行测试
    asyncio.run(main())
    
    print("\n" + "=" * 70)
    print("🏁 测试执行完毕")
    print("   访问 http://localhost:8089 查看热力图结果")
    print("=" * 70)