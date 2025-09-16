#!/usr/bin/env python3
"""
测试下载内容检查功能
验证真实文档和演示文档的区分能力
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from download_content_checker import DownloadContentChecker

def create_test_files():
    """创建测试文件"""
    test_dir = Path('/root/projects/tencent-doc-manager/test_downloads')
    test_dir.mkdir(exist_ok=True)
    
    files = []
    
    # 1. 创建演示数据文件
    demo_file = test_dir / 'demo_data.csv'
    with open(demo_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['姓名', '部门', '职位', '风险等级'])
        writer.writerow(['张三', '技术部', '工程师', 'L1'])
        writer.writerow(['李四', '市场部', '经理', 'L2'])
        writer.writerow(['王五', '财务部', '主管', 'L3'])
        writer.writerow(['赵六', '测试部', '测试员', 'L2'])
    files.append(str(demo_file))
    print(f"✅ 创建演示数据文件: {demo_file}")
    
    # 2. 创建真实风格数据文件
    real_file = test_dir / 'real_data.csv'
    with open(real_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['产品名称', '销售额', '销售日期', '负责人', '完成率'])
        writer.writerow(['智能音箱Pro', '156780.50', '2025-08-15', '陈经理', '98.5%'])
        writer.writerow(['无线耳机X5', '89234.00', '2025-08-16', '刘主管', '102.3%'])
        writer.writerow(['蓝牙键盘K3', '45670.25', '2025-08-17', '王总监', '87.6%'])
        writer.writerow(['便携显示器M2', '234567.80', '2025-08-18', '周经理', '110.2%'])
        writer.writerow(['智能手表S8', '178900.00', '2025-08-19', '吴主管', '95.8%'])
        # 添加更多数据使其更真实
        for i in range(20):
            writer.writerow([
                f'产品{i+6}', 
                f'{50000 + i * 10000:.2f}',
                f'2025-08-{20+i:02d}',
                f'负责人{i+6}',
                f'{85 + i * 0.5:.1f}%'
            ])
    files.append(str(real_file))
    print(f"✅ 创建真实风格数据文件: {real_file}")
    
    # 3. 创建混合数据文件
    mixed_file = test_dir / 'mixed_data.csv'
    with open(mixed_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['项目名称', '状态', '负责人', '预算', '备注'])
        writer.writerow(['测试项目A', '进行中', '张三', '100000', 'demo测试'])
        writer.writerow(['实际项目B', '已完成', '陈建国', '850000', '2025Q3交付'])
        writer.writerow(['示例项目C', '计划中', '李四', '50000', 'example'])
        writer.writerow(['生产项目D', '进行中', '王晓明', '1200000', '重点项目'])
    files.append(str(mixed_file))
    print(f"✅ 创建混合数据文件: {mixed_file}")
    
    # 4. 创建小文件（可能是假数据）
    small_file = test_dir / 'small_data.csv'
    with open(small_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['A', 'B'])
        writer.writerow(['1', '2'])
    files.append(str(small_file))
    print(f"✅ 创建小文件: {small_file}")
    
    return files

def test_individual_files(files):
    """测试单个文件检查"""
    print("\n" + "="*60)
    print("📊 单个文件检查测试")
    print("="*60)
    
    checker = DownloadContentChecker()
    
    for file_path in files:
        print(f"\n检查文件: {Path(file_path).name}")
        print("-"*40)
        
        result = checker.check_file(file_path)
        
        print(f"文件大小: {result['file_size_readable']}")
        print(f"真实性评分: {result['authenticity_score']:.1f}/100")
        
        if result['is_demo_data']:
            print("判定: ⚠️ 疑似演示数据")
        else:
            print("判定: ✅ 可能是真实数据")
        
        if 'row_count' in result:
            print(f"数据规模: {result['row_count']}行 × {result['column_count']}列")
        
        if 'demo_indicators_found' in result:
            print(f"演示标识数: {result['demo_indicators_found']}")
            
        if 'real_indicators_found' in result:
            print(f"真实标识数: {result['real_indicators_found']}")
        
        print(f"总结: {result['summary']}")

def test_batch_check(files):
    """测试批量检查"""
    print("\n" + "="*60)
    print("📊 批量文件检查测试")
    print("="*60)
    
    checker = DownloadContentChecker()
    batch_result = checker.check_download_batch(files)
    
    print(f"文件数量: {batch_result['file_count']}")
    print(f"总大小: {batch_result['total_size']}")
    print(f"平均真实性评分: {batch_result['average_authenticity_score']:.1f}/100")
    print(f"全部是演示数据: {batch_result['all_demo_data']}")
    print(f"全部是真实数据: {batch_result['all_real_data']}")
    print(f"混合数据: {batch_result['mixed_data']}")
    print(f"\n整体评估: {batch_result['overall_assessment']}")

def test_with_actual_download():
    """测试实际下载的文件"""
    print("\n" + "="*60)
    print("📊 检查实际下载目录")
    print("="*60)
    
    download_dir = Path('/root/projects/tencent-doc-manager/downloads')
    if not download_dir.exists():
        print("下载目录不存在")
        return
    
    # 查找最近的CSV文件
    csv_files = list(download_dir.glob('*.csv'))
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    # 按修改时间排序，取最新的
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = csv_files[0]
    
    print(f"检查最新文件: {latest_file.name}")
    print(f"修改时间: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*40)
    
    checker = DownloadContentChecker()
    result = checker.check_file(str(latest_file))
    
    # 显示详细结果
    print(f"真实性评分: {result['authenticity_score']:.1f}/100")
    
    if result['is_demo_data']:
        print("⚠️ 判定: 疑似演示数据")
        print("原因:")
        if result.get('demo_indicators_found', 0) > 0:
            print(f"  - 发现{result['demo_indicators_found']}个演示数据标识")
        if result.get('file_size', 0) < 1024:
            print(f"  - 文件太小 ({result['file_size_readable']})")
        if result.get('row_count', 0) < 10:
            print(f"  - 数据行数太少 ({result.get('row_count', 0)}行)")
    else:
        print("✅ 判定: 可能是真实数据")
        print("原因:")
        if result.get('real_indicators_found', 0) > 0:
            print(f"  - 发现{result['real_indicators_found']}个真实数据标识")
        if result.get('file_size', 0) > 10240:
            print(f"  - 文件大小合理 ({result['file_size_readable']})")
        if result.get('row_count', 0) > 100:
            print(f"  - 数据量充足 ({result.get('row_count', 0)}行)")
    
    # 显示数据预览
    if 'data_preview' in result and result['data_preview']:
        print("\n数据预览 (前5行):")
        for i, row in enumerate(result['data_preview'][:5], 1):
            print(f"  第{i}行: {row}")

def main():
    """主测试函数"""
    print("🔍 下载内容检查功能测试")
    print("="*60)
    
    # 1. 创建测试文件
    test_files = create_test_files()
    
    # 2. 测试单个文件
    test_individual_files(test_files)
    
    # 3. 测试批量检查
    test_batch_check(test_files)
    
    # 4. 测试实际下载的文件
    test_with_actual_download()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    main()