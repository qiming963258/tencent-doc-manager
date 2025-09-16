#!/usr/bin/env python3
"""
完整数据流测试脚本
验证：下载 → 版本管理 → 对比 → 热力图 → Excel标记
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_phase1_version_management():
    """测试阶段1：版本管理"""
    print("\n=== 测试阶段1：版本管理 ===")
    
    # 模拟下载的文件
    test_files = [
        {'filename': 'test.csv', 'filepath': '/root/projects/tencent-doc-manager/auto_downloads/test.csv'},
        {'filename': 'realtest.csv', 'filepath': '/root/projects/tencent-doc-manager/auto_downloads/realtest.csv'}
    ]
    
    try:
        from post_download_processor import PostDownloadProcessor
        processor = PostDownloadProcessor()
        
        # 测试版本管理器初始化
        if processor.initialize_version_manager():
            print("✅ 版本管理器初始化成功")
        else:
            print("❌ 版本管理器初始化失败")
            return False
            
        # 处理下载的文件
        result = processor.process_downloaded_files(test_files)
        
        print(f"处理结果摘要：")
        print(f"  - 版本管理: {result.get('version_management', {}).get('status')}")
        print(f"  - 处理文件数: {len(result.get('version_management', {}).get('processed_files', []))}")
        
        # 检查版本文件是否创建
        version_dir = '/root/projects/tencent-doc-manager/csv_versions/current'
        if os.path.exists(version_dir):
            files = os.listdir(version_dir)
            print(f"  - 版本目录文件: {len(files)} 个")
            for f in files[:3]:
                print(f"    • {f}")
        
        return result.get('version_management', {}).get('status') == 'success'
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase2_comparison():
    """测试阶段2：CSV对比分析"""
    print("\n=== 测试阶段2：CSV对比分析 ===")
    
    try:
        # 检查对比结果目录
        comparison_dir = '/root/projects/tencent-doc-manager/csv_versions/comparison'
        if os.path.exists(comparison_dir):
            files = os.listdir(comparison_dir)
            print(f"✅ 对比结果目录存在，包含 {len(files)} 个文件")
            
            # 读取最新的对比结果
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                latest = sorted(json_files)[-1]
                filepath = os.path.join(comparison_dir, latest)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  - 最新对比结果: {latest}")
                print(f"  - 风险等级分布: L1={data.get('risk_summary', {}).get('L1', 0)}, "
                      f"L2={data.get('risk_summary', {}).get('L2', 0)}, "
                      f"L3={data.get('risk_summary', {}).get('L3', 0)}")
                return True
            else:
                print("⚠️ 没有找到对比结果JSON文件")
                return False
        else:
            print("❌ 对比结果目录不存在")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_phase3_heatmap():
    """测试阶段3：热力图生成"""
    print("\n=== 测试阶段3：热力图生成 ===")
    
    try:
        from matrix_transformer import MatrixTransformer
        transformer = MatrixTransformer()
        
        # 模拟对比结果
        test_comparison = {
            'changes': [
                {'row': 5, 'column': 3, 'risk_level': 'L1'},
                {'row': 10, 'column': 8, 'risk_level': 'L2'},
                {'row': 15, 'column': 12, 'risk_level': 'L3'}
            ]
        }
        
        # 生成热力图矩阵
        # 使用正确的方法名
        heatmap_data = transformer.generate_heatmap_data(test_comparison)
        matrix = heatmap_data.get('matrix', [])
        
        if matrix and len(matrix) == 30 and len(matrix[0]) == 19:
            print(f"✅ 热力图矩阵生成成功: {len(matrix)}×{len(matrix[0])}")
            
            # 统计非零值
            non_zero = sum(1 for row in matrix for val in row if val > 0)
            print(f"  - 非零单元格: {non_zero}")
            print(f"  - 最大值: {max(max(row) for row in matrix):.2f}")
            return True
        else:
            print("❌ 热力图矩阵尺寸不正确")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_phase4_excel():
    """测试阶段4：Excel标记"""
    print("\n=== 测试阶段4：Excel标记 ===")
    
    try:
        # 检查Excel输出目录
        excel_dir = '/root/projects/tencent-doc-manager/excel_outputs'
        if os.path.exists(excel_dir):
            files = os.listdir(excel_dir)
            excel_files = [f for f in files if f.endswith('.xlsx')]
            print(f"✅ Excel输出目录存在，包含 {len(excel_files)} 个Excel文件")
            
            if excel_files:
                latest = sorted(excel_files)[-1]
                print(f"  - 最新Excel文件: {latest}")
                filepath = os.path.join(excel_dir, latest)
                file_size = os.path.getsize(filepath)
                print(f"  - 文件大小: {file_size:,} 字节")
                return True
            else:
                print("⚠️ 没有找到Excel文件")
                return False
        else:
            print("⚠️ Excel输出目录不存在，创建目录")
            os.makedirs(excel_dir, exist_ok=True)
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_data_flow_integrity():
    """测试数据流完整性"""
    print("\n=== 测试数据流完整性 ===")
    
    issues = []
    
    # 检查配置文件
    config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("配置状态：")
    print(f"  - 版本管理: {'✅' if config.get('enable_version_management') else '❌'}")
    print(f"  - CSV对比: {'✅' if config.get('enable_comparison') else '❌'}")
    print(f"  - 热力图: {'✅' if config.get('enable_heatmap') else '❌'}")
    print(f"  - Excel标记: {'✅' if config.get('enable_excel') else '❌'}")
    
    # 检查关键模块
    modules = [
        'post_download_processor',
        'matrix_transformer',
        'excel_marker',
        'production.core_modules.production_csv_comparator'
    ]
    
    print("\n模块导入测试：")
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            issues.append(f"模块导入失败: {module}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\n✅ 数据流完整性检查通过")
    
    return len(issues) == 0

def main():
    """主测试函数"""
    print("=" * 60)
    print("腾讯文档监控系统 - 完整数据流测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        '阶段1-版本管理': test_phase1_version_management(),
        '阶段2-CSV对比': test_phase2_comparison(), 
        '阶段3-热力图': test_phase3_heatmap(),
        '阶段4-Excel标记': test_phase4_excel(),
        '数据流完整性': test_data_flow_integrity()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总：")
    print("=" * 60)
    
    for name, status in results.items():
        status_str = "✅ 通过" if status else "❌ 失败"
        print(f"{name}: {status_str}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！数据流完整可用。")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，需要修复。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)