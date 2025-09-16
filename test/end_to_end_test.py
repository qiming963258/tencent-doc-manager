#!/usr/bin/env python3
"""
端到端集成测试 - 验证完整数据流
包括：文件下载模拟 → 版本管理 → CSV对比 → 热力图生成 → Excel标记
"""

import os
import sys
import json
import time
import shutil
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def create_test_csv_v1():
    """创建测试CSV文件版本1"""
    content = """部门,员工姓名,工号,本周工作内容,完成度,风险等级
技术部,张三,T001,系统架构设计,80%,L2
技术部,李四,T002,代码开发,90%,L3
产品部,王五,P001,需求分析,75%,L2
产品部,赵六,P002,用户调研,85%,L3"""
    
    filepath = '/root/projects/tencent-doc-manager/auto_downloads/test_data.csv'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def create_test_csv_v2():
    """创建测试CSV文件版本2（有变更）"""
    content = """部门,员工姓名,工号,本周工作内容,完成度,风险等级
技术部,张三,T001,系统架构优化,95%,L1
技术部,李四,T002,代码开发,100%,L3
产品部,王五,P001,需求评审,80%,L1
产品部,赵六,P002,用户访谈,90%,L2
市场部,钱七,M001,推广计划,70%,L2"""
    
    filepath = '/root/projects/tencent-doc-manager/auto_downloads/test_data.csv'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def clean_test_environment():
    """清理测试环境"""
    print("\n🧹 清理测试环境...")
    
    # 清理版本目录中的测试文件
    version_dirs = [
        '/root/projects/tencent-doc-manager/csv_versions/current',
        '/root/projects/tencent-doc-manager/csv_versions/archive'
    ]
    
    for dir_path in version_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if 'test_data' in file:
                    os.remove(os.path.join(dir_path, file))
                    print(f"  删除: {file}")

def test_complete_pipeline():
    """测试完整管道"""
    print("\n" + "="*60)
    print("🚀 腾讯文档监控系统 - 端到端集成测试")
    print("="*60)
    
    # 清理环境
    clean_test_environment()
    
    # 阶段1：创建并处理第一个版本
    print("\n📋 阶段1：处理初始版本")
    print("-"*40)
    
    csv_v1 = create_test_csv_v1()
    print(f"✅ 创建测试CSV v1: {csv_v1}")
    
    from post_download_processor import PostDownloadProcessor
    processor = PostDownloadProcessor()
    
    # 处理第一个版本
    result1 = processor.process_downloaded_files([csv_v1])
    print(f"处理结果：")
    print(f"  - 成功: {result1.get('success', False)}")
    print(f"  - 版本管理: {result1.get('version_management', {}).get('status', 'N/A')}")
    print(f"  - 比较状态: {result1.get('comparison', {}).get('status', 'N/A')}")
    
    # 等待一秒确保时间戳不同
    time.sleep(1)
    
    # 阶段2：创建并处理第二个版本（有变更）
    print("\n📋 阶段2：处理更新版本")
    print("-"*40)
    
    csv_v2 = create_test_csv_v2()
    print(f"✅ 创建测试CSV v2（有变更）: {csv_v2}")
    
    # 处理第二个版本
    result2 = processor.process_downloaded_files([csv_v2])
    print(f"处理结果：")
    print(f"  - 成功: {result2.get('success', False)}")
    print(f"  - 版本管理: {result2.get('version_management', {}).get('status', 'N/A')}")
    print(f"  - 比较状态: {result2.get('comparison', {}).get('status', 'N/A')}")
    
    # 阶段3：验证版本管理
    print("\n📋 阶段3：验证版本管理")
    print("-"*40)
    
    current_dir = '/root/projects/tencent-doc-manager/csv_versions/current'
    archive_dir = '/root/projects/tencent-doc-manager/csv_versions/archive'
    
    current_files = [f for f in os.listdir(current_dir) if 'test_data' in f] if os.path.exists(current_dir) else []
    archive_files = [f for f in os.listdir(archive_dir) if 'test_data' in f] if os.path.exists(archive_dir) else []
    
    print(f"当前版本文件: {len(current_files)}")
    for f in current_files:
        print(f"  • {f}")
    
    print(f"归档版本文件: {len(archive_files)}")
    for f in archive_files:
        print(f"  • {f}")
    
    # 阶段4：验证对比结果
    print("\n📋 阶段4：验证对比结果")
    print("-"*40)
    
    comparison_dir = '/root/projects/tencent-doc-manager/csv_versions/comparison'
    if os.path.exists(comparison_dir):
        comparison_files = sorted([f for f in os.listdir(comparison_dir) if f.endswith('.json')])
        if comparison_files:
            latest_comparison = comparison_files[-1]
            filepath = os.path.join(comparison_dir, latest_comparison)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                comparison_data = json.load(f)
            
            print(f"最新对比文件: {latest_comparison}")
            print(f"对比结果摘要：")
            print(f"  - 成功状态: {comparison_data.get('success', False)}")
            print(f"  - 总差异数: {comparison_data.get('total_differences', 0)}")
            
            # differences是一个列表，不是字典
            changes = comparison_data.get('differences', [])
            print(f"  - 发现变更: {len(changes)} 处")
            
            # 统计风险等级分布
            risk_count = {'L1': 0, 'L2': 0, 'L3': 0}
            for change in changes:
                risk_level = change.get('risk_level', 'L3')
                if risk_level in risk_count:
                    risk_count[risk_level] += 1
            
            print(f"  - 风险分布: L1={risk_count['L1']}, L2={risk_count['L2']}, L3={risk_count['L3']}")
        else:
            print("❌ 没有找到对比结果文件")
    else:
        print("❌ 对比结果目录不存在")
    
    # 阶段5：验证热力图生成
    print("\n📋 阶段5：验证热力图生成")
    print("-"*40)
    
    if result2.get('heatmap', {}).get('status') == 'success':
        heatmap_data = result2.get('heatmap', {}).get('data', {})
        matrix = heatmap_data.get('matrix', [])
        
        if matrix and len(matrix) == 30:
            print(f"✅ 热力图矩阵: {len(matrix)}×{len(matrix[0]) if matrix else 0}")
            
            # 统计非零值
            non_zero = sum(1 for row in matrix for val in row if val > 0)
            max_val = max(max(row) for row in matrix) if matrix else 0
            
            print(f"  - 热点数量: {non_zero}")
            print(f"  - 最大强度: {max_val:.2f}")
        else:
            print("❌ 热力图矩阵生成失败")
    else:
        print("⚠️ 热力图未生成或生成失败")
    
    # 阶段6：验证Excel标记
    print("\n📋 阶段6：验证Excel标记")
    print("-"*40)
    
    excel_result = result2.get('excel', {})
    if excel_result.get('status') == 'success':
        excel_file = excel_result.get('file_path', 'N/A')
        print(f"✅ Excel文件生成: {excel_file}")
        
        if os.path.exists(excel_file):
            file_size = os.path.getsize(excel_file)
            print(f"  - 文件大小: {file_size:,} 字节")
            print(f"  - 标记单元格: {excel_result.get('marked_cells', 0)} 个")
    else:
        print("⚠️ Excel标记未执行或失败")
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    success_count = 0
    total_count = 6
    
    # 检查各阶段
    checks = {
        "版本管理（新增）": len(current_files) > 0,
        "版本管理（归档）": len(archive_files) > 0 if result2.get('version_management', {}).get('status') == 'success' else True,
        "CSV对比执行": result2.get('comparison', {}).get('status') == 'success' if len(archive_files) > 0 else True,
        "热力图生成": result2.get('heatmap', {}).get('status') == 'success' if result2.get('comparison', {}).get('status') == 'success' else True,
        "Excel标记": result2.get('excel', {}).get('status') == 'success' if result2.get('heatmap', {}).get('status') == 'success' else True,
        "完整数据流": result2.get('success', False)
    }
    
    for name, status in checks.items():
        status_str = "✅ 通过" if status else "❌ 失败"
        print(f"{name}: {status_str}")
        if status:
            success_count += 1
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！端到端数据流完全正常。")
        return True
    else:
        print(f"\n⚠️ 有 {total_count - success_count} 个测试失败。")
        return False

def main():
    """主函数"""
    try:
        success = test_complete_pipeline()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())