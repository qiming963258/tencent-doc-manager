#!/usr/bin/env python3
"""
深度数据分析脚本 - 检查综合打分文件的数据传输和参数格式
"""
import json
import sys
import os

def analyze_comprehensive_score(file_path):
    """深度分析综合打分文件"""

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('🔬 深度数据结构分析')
    print('='*60)

    # 1. 数据大小分析
    file_size = os.path.getsize(file_path)
    print(f'\n📦 文件大小: {file_size:,} 字节 ({file_size/1024:.2f} KB)')

    # 2. 热力图矩阵详细分析
    print('\n🔥 热力图矩阵分析:')
    if 'heatmap_data' in data and 'matrix' in data['heatmap_data']:
        matrix = data['heatmap_data']['matrix']
        print(f'  维度: {len(matrix)}×{len(matrix[0]) if matrix else 0}')

        # 分析值分布
        all_values = []
        for row in matrix:
            all_values.extend(row)

        if all_values:
            print(f'  最小值: {min(all_values)}')
            print(f'  最大值: {max(all_values)}')
            print(f'  平均值: {sum(all_values)/len(all_values):.3f}')

            # 风险等级分布
            high_risk = sum(1 for v in all_values if v >= 0.7)
            med_risk = sum(1 for v in all_values if 0.3 <= v < 0.7)
            low_risk = sum(1 for v in all_values if 0.05 < v < 0.3)
            no_mod = sum(1 for v in all_values if v <= 0.05)

            print(f'  高风险格子(>=0.7): {high_risk} 个')
            print(f'  中风险格子(0.3-0.7): {med_risk} 个')
            print(f'  低风险格子(0.05-0.3): {low_risk} 个')
            print(f'  无修改格子(<=0.05): {no_mod} 个')

    # 3. 表格详情完整性检查
    print('\n📋 表格详情完整性:')
    if 'table_details' in data:
        for td in data['table_details']:
            print(f'\n  表格: {td.get("table_name", "N/A")}')
            print(f'    table_id: {"YES" if "table_id" in td else "NO"}')
            print(f'    table_index: {"YES" if "table_index" in td else "NO"}')
            print(f'    total_rows: {td.get("total_rows", 0)} ({"EXISTS" if "total_rows" in td else "MISSING"})')
            print(f'    total_modifications: {td.get("total_modifications", 0)} ({"EXISTS" if "total_modifications" in td else "MISSING"})')
            print(f'    excel_url: {"EXISTS" if td.get("excel_url") else "MISSING"}')

            # 列详情分析
            if 'column_details' in td:
                cd_list = td['column_details']
                print(f'    列详情数: {len(cd_list)}')

                # 检查每列是否有完整数据
                complete_cols = sum(1 for cd in cd_list if all(k in cd for k in ['column_name', 'column_index', 'modification_count', 'modified_rows', 'score']))
                print(f'    完整列数据: {complete_cols}/{len(cd_list)}')

                # 统计有修改的列
                modified_cols = sum(1 for cd in cd_list if cd.get('modification_count', 0) > 0)
                print(f'    有修改的列: {modified_cols}/{len(cd_list)}')

    # 4. UI数据传输参数检查
    print('\n🔌 UI数据传输参数:')
    ui_params = {
        'metadata.version': data.get('metadata', {}).get('version'),
        'metadata.total_params': data.get('metadata', {}).get('total_params'),
        'summary.total_tables': data.get('summary', {}).get('total_tables'),
        'summary.total_modifications': data.get('summary', {}).get('total_modifications'),
        'table_names长度': len(data.get('table_names', [])),
        'column_names长度': len(data.get('column_names', [])),
        'heatmap_matrix行数': len(data.get('heatmap_data', {}).get('matrix', [])),
        'table_details数量': len(data.get('table_details', []))
    }

    for key, value in ui_params.items():
        print(f'  {key}: {value}')

    # 5. 数据一致性验证
    print('\n✅ 数据一致性验证:')

    # 检查表格数量一致性
    table_count = data.get('summary', {}).get('total_tables', 0)
    table_names_count = len(data.get('table_names', []))
    table_details_count = len(data.get('table_details', []))
    matrix_rows = len(data.get('heatmap_data', {}).get('matrix', []))

    if table_count == table_names_count == table_details_count == matrix_rows:
        print(f'  [OK] 表格数量一致: {table_count}')
    else:
        print(f'  [ERROR] 表格数量不一致:')
        print(f'    summary: {table_count}')
        print(f'    table_names: {table_names_count}')
        print(f'    table_details: {table_details_count}')
        print(f'    matrix_rows: {matrix_rows}')

    # 检查列数量一致性
    column_count = data.get('summary', {}).get('total_columns', 0)
    column_names_count = len(data.get('column_names', []))
    if matrix_rows > 0:
        matrix_cols = len(data['heatmap_data']['matrix'][0])
        if column_count == column_names_count == matrix_cols == 19:
            print(f'  [OK] 列数量一致: {column_count}')
        else:
            print(f'  [ERROR] 列数量不一致: {column_count} vs {column_names_count} vs {matrix_cols}')
    else:
        print(f'  [WARNING] 无法验证列数量（无矩阵数据）')

    # 检查修改总数一致性
    summary_mods = data.get('summary', {}).get('total_modifications', 0)
    detail_mods = sum(td.get('total_modifications', 0) for td in data.get('table_details', []))
    if summary_mods == detail_mods:
        print(f'  [OK] 修改总数一致: {summary_mods}')
    else:
        print(f'  [ERROR] 修改总数不一致: summary={summary_mods}, details={detail_mods}')

    # 6. 数据传输验证
    print('\n🔄 数据传输链路验证:')

    # 验证热力图数据传输
    print('  热力图传输检查:')
    if 'heatmap_data' in data and 'matrix' in data['heatmap_data']:
        matrix = data['heatmap_data']['matrix']
        print(f'    - 矩阵数据: EXISTS')
        print(f'    - 矩阵格式: {type(matrix).__name__}')
        print(f'    - 第一行示例: {matrix[0][:5] if matrix else "N/A"}...')
    else:
        print(f'    - 矩阵数据: MISSING')

    # 验证表格详情传输
    print('  表格详情传输检查:')
    if 'table_details' in data and data['table_details']:
        td = data['table_details'][0]  # 检查第一个表格
        print(f'    - total_rows字段: {"EXISTS" if "total_rows" in td else "MISSING"}')
        print(f'    - excel_url字段: {"EXISTS" if "excel_url" in td else "MISSING"}')
        print(f'    - column_details字段: {"EXISTS" if "column_details" in td else "MISSING"}')

        if 'column_details' in td and td['column_details']:
            cd = td['column_details'][0]  # 检查第一列
            print(f'    - modified_rows字段: {"EXISTS" if "modified_rows" in cd else "MISSING"}')
            print(f'    - modification_count字段: {"EXISTS" if "modification_count" in cd else "MISSING"}')

    # 7. UI渲染必需参数验证
    print('\n🎨 UI渲染必需参数:')
    ui_required = {
        '1. 表名(Y轴)': 'table_names' in data and len(data['table_names']) > 0,
        '2. 列名(X轴)': 'column_names' in data and len(data['column_names']) == 19,
        '3. 热力图矩阵': 'heatmap_data' in data and 'matrix' in data['heatmap_data'],
        '4. 表格URL': all('excel_url' in td for td in data.get('table_details', [])),
        '5. 总行数(一维图)': all('total_rows' in td for td in data.get('table_details', [])),
        '6. 修改详情': all('column_details' in td for td in data.get('table_details', [])),
    }

    all_ok = True
    for param, exists in ui_required.items():
        status = 'PASS' if exists else 'FAIL'
        print(f'  {param}: {status}')
        if not exists:
            all_ok = False

    print('\n' + '='*60)
    print('📊 最终评估:')

    # 统计问题
    issues = []
    if table_count != table_names_count or table_count != table_details_count or table_count != matrix_rows:
        issues.append('表格数量不一致')
    if column_count != 19 or column_names_count != 19:
        issues.append('列数量不是19')
    if summary_mods != detail_mods:
        issues.append('修改总数不一致')
    if not all_ok:
        issues.append('UI必需参数缺失')

    if not issues:
        print('✅ 数据传输和参数格式: 完全符合规范，可正常传输到UI')
    else:
        print(f'⚠️ 发现 {len(issues)} 个问题:')
        for issue in issues:
            print(f'   - {issue}')

    return not bool(issues)

if __name__ == "__main__":
    # 分析最新的综合打分文件
    file_path = '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_20250918_195420.json'

    if os.path.exists(file_path):
        print(f'分析文件: {os.path.basename(file_path)}\n')
        result = analyze_comprehensive_score(file_path)
        sys.exit(0 if result else 1)
    else:
        print(f'文件不存在: {file_path}')
        sys.exit(1)