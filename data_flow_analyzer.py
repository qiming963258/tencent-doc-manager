#!/usr/bin/env python3
"""
数据流程分析器
追踪CSV对比 → 热力图矩阵的完整转换过程
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class DataFlowAnalyzer:
    """数据流程分析器"""
    
    def __init__(self):
        self.base_dir = "/root/projects/tencent-doc-manager"
        
    def analyze_complete_flow(self) -> Dict[str, Any]:
        """分析完整的数据流程"""
        
        analysis_report = {
            'timestamp': '2025-08-20T19:45:00',
            'analysis_type': 'complete_data_flow_tracking',
            'stages': {}
        }
        
        # 阶段1: CSV对比结果分析
        comparison_analysis = self._analyze_csv_comparison_results()
        analysis_report['stages']['csv_comparison'] = comparison_analysis
        
        # 阶段2: 映射转换分析
        mapping_analysis = self._analyze_mapping_process(comparison_analysis)
        analysis_report['stages']['mapping_transformation'] = mapping_analysis
        
        # 阶段3: 热力图矩阵分析
        heatmap_analysis = self._analyze_heatmap_generation()
        analysis_report['stages']['heatmap_generation'] = heatmap_analysis
        
        # 阶段4: 数据一致性验证
        consistency_check = self._verify_data_consistency(
            comparison_analysis, heatmap_analysis
        )
        analysis_report['stages']['consistency_verification'] = consistency_check
        
        # 生成问题诊断
        analysis_report['diagnosis'] = self._generate_diagnosis(analysis_report)
        
        return analysis_report
    
    def _analyze_csv_comparison_results(self) -> Dict[str, Any]:
        """分析CSV对比结果"""
        
        results_dir = os.path.join(self.base_dir, "csv_security_results")
        comparison_files = [f for f in os.listdir(results_dir) if f.endswith('_comparison.json')]
        
        analysis = {
            'total_comparison_files': len(comparison_files),
            'files_analyzed': {},
            'data_structures': {},
            'mapping_patterns': {}
        }
        
        for file_name in comparison_files:
            file_path = os.path.join(results_dir, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 分析数据结构
                differences = data.get('differences', [])
                file_info = data.get('file_info', {}).get('metadata', {})
                
                analysis['files_analyzed'][file_name] = {
                    'differences_count': len(differences),
                    'source_columns': file_info.get('file1_info', {}).get('columns', 0),
                    'source_rows': file_info.get('file1_info', {}).get('rows', 0),
                    'column_mapping': data.get('file_info', {}).get('metadata', {}).get('column_mapping', {})
                }
                
                # 分析位置分布
                if differences:
                    analysis['files_analyzed'][file_name]['position_distribution'] = {
                        'row_range': [
                            min(d.get('行号', 0) for d in differences),
                            max(d.get('行号', 0) for d in differences)
                        ],
                        'column_range': [
                            min(d.get('列索引', 0) for d in differences), 
                            max(d.get('列索引', 0) for d in differences)
                        ],
                        'risk_score_range': [
                            min(d.get('risk_score', 0) for d in differences),
                            max(d.get('risk_score', 0) for d in differences)
                        ]
                    }
                    
            except Exception as e:
                analysis['files_analyzed'][file_name] = {'error': str(e)}
        
        return analysis
    
    def _analyze_mapping_process(self, csv_analysis: Dict) -> Dict[str, Any]:
        """分析映射转换过程"""
        
        mapping_analysis = {
            'current_mapping_logic': {},
            'problems_identified': [],
            'proposed_solutions': []
        }
        
        # 分析当前映射逻辑（从ui_connectivity_manager.py中提取）
        mapping_analysis['current_mapping_logic'] = {
            'row_mapping': 'row = min(diff.get(\'行号\', 1) - 1, 29)',
            'col_mapping': 'col = min(diff.get(\'列索引\', 1) - 1, 18)',
            'intensity_mapping': 'heatmap_matrix[row][col] = max(current_value, risk_score)',
            'target_matrix_size': '30x19'
        }
        
        # 识别问题
        for file_name, file_data in csv_analysis['files_analyzed'].items():
            if 'error' not in file_data:
                source_cols = file_data['source_columns']
                source_rows = file_data['source_rows']
                
                if source_cols > 19:
                    mapping_analysis['problems_identified'].append(
                        f"{file_name}: 源数据{source_cols}列 > 目标19列，存在数据丢失风险"
                    )
                
                if source_rows > 30:
                    mapping_analysis['problems_identified'].append(
                        f"{file_name}: 源数据{source_rows}行 > 目标30行，存在数据截断"
                    )
                
                # 检查列映射问题
                column_mapping = file_data.get('column_mapping', {}).get('mapping', {})
                if len(column_mapping) != source_cols:
                    mapping_analysis['problems_identified'].append(
                        f"{file_name}: 列映射不完整，{len(column_mapping)}映射 vs {source_cols}实际列"
                    )
        
        return mapping_analysis
    
    def _analyze_heatmap_generation(self) -> Dict[str, Any]:
        """分析热力图生成过程"""
        
        heatmap_files = [
            'real_time_heatmap.json',
            'ui_params_real_test_20250819_224427.json'
        ]
        
        analysis = {
            'heatmap_files_found': {},
            'matrix_analysis': {},
            'generation_algorithms': []
        }
        
        for file_name in heatmap_files:
            file_path = os.path.join(self.base_dir, file_name)
            if not os.path.exists(file_path):
                file_path = os.path.join(self.base_dir, "production/servers", file_name)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    heatmap_data = data.get('heatmap_data', [])
                    if heatmap_data:
                        analysis['heatmap_files_found'][file_name] = {
                            'matrix_dimensions': [len(heatmap_data), len(heatmap_data[0]) if heatmap_data else 0],
                            'value_range': [
                                min(min(row) for row in heatmap_data if row),
                                max(max(row) for row in heatmap_data if row)
                            ],
                            'algorithm': data.get('algorithm', 'unknown'),
                            'data_source': data.get('data_source', 'unknown'),
                            'generation_time': data.get('generation_time', 'unknown'),
                            'changes_applied': data.get('changes_applied', 0)
                        }
                        
                        # 分析热力图模式
                        hot_spots = self._find_hotspots(heatmap_data)
                        analysis['heatmap_files_found'][file_name]['hotspots'] = hot_spots
                    
                except Exception as e:
                    analysis['heatmap_files_found'][file_name] = {'error': str(e)}
        
        return analysis
    
    def _find_hotspots(self, matrix: List[List[float]]) -> Dict[str, Any]:
        """找到热力图中的热点"""
        
        hotspots = []
        threshold = 0.5  # 热点阈值
        
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                if value > threshold:
                    hotspots.append({
                        'position': [i, j],
                        'intensity': value
                    })
        
        return {
            'total_hotspots': len(hotspots),
            'max_intensity': max((h['intensity'] for h in hotspots), default=0),
            'hotspot_positions': hotspots[:10]  # 前10个热点
        }
    
    def _verify_data_consistency(self, csv_analysis: Dict, heatmap_analysis: Dict) -> Dict[str, Any]:
        """验证数据一致性"""
        
        consistency_report = {
            'issues_found': [],
            'data_flow_integrity': 'unknown',
            'recommendations': []
        }
        
        # 检查CSV differences数量 vs 热力图变更数量
        for file_name, file_data in csv_analysis['files_analyzed'].items():
            if 'differences_count' in file_data:
                csv_changes = file_data['differences_count']
                
                for heatmap_file, heatmap_data in heatmap_analysis['heatmap_files_found'].items():
                    if 'changes_applied' in heatmap_data:
                        heatmap_changes = heatmap_data['changes_applied']
                        
                        if csv_changes != heatmap_changes:
                            consistency_report['issues_found'].append(
                                f"变更数量不一致: {file_name}({csv_changes}) vs {heatmap_file}({heatmap_changes})"
                            )
        
        # 评估数据流完整性
        if not consistency_report['issues_found']:
            consistency_report['data_flow_integrity'] = 'good'
        elif len(consistency_report['issues_found']) < 3:
            consistency_report['data_flow_integrity'] = 'partial'
        else:
            consistency_report['data_flow_integrity'] = 'broken'
        
        return consistency_report
    
    def _generate_diagnosis(self, analysis_report: Dict) -> Dict[str, Any]:
        """生成问题诊断"""
        
        diagnosis = {
            'critical_issues': [],
            'data_flow_status': 'unknown',
            'root_cause_analysis': [],
            'action_items': []
        }
        
        # 分析数据流状态
        consistency = analysis_report['stages']['consistency_verification']['data_flow_integrity']
        mapping_problems = len(analysis_report['stages']['mapping_transformation']['problems_identified'])
        
        if consistency == 'broken' or mapping_problems > 5:
            diagnosis['data_flow_status'] = 'critical'
            diagnosis['critical_issues'].append('数据流程存在严重断裂')
        elif consistency == 'partial' or mapping_problems > 2:
            diagnosis['data_flow_status'] = 'needs_attention'
            diagnosis['critical_issues'].append('数据流程存在部分问题')
        else:
            diagnosis['data_flow_status'] = 'stable'
        
        # 根因分析
        diagnosis['root_cause_analysis'] = [
            '实际CSV列数与标准19列不匹配',
            '行数动态变化但矩阵固定为30行',
            '映射算法过于简化，未考虑数据语义',
            '缺少中间转换层处理数据差异'
        ]
        
        # 行动项
        diagnosis['action_items'] = [
            '重新设计自适应映射算法',
            '建立语义列映射系统',
            '实现动态矩阵维度调整',
            '添加数据一致性验证机制'
        ]
        
        return diagnosis

def main():
    """主函数"""
    analyzer = DataFlowAnalyzer()
    
    print("🔍 开始分析数据流程...")
    analysis_report = analyzer.analyze_complete_flow()
    
    # 保存分析报告
    report_file = "/root/projects/tencent-doc-manager/data_flow_analysis_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 数据流程分析完成，报告已保存至: {report_file}")
    
    # 显示关键发现
    print("\n🎯 关键发现:")
    diagnosis = analysis_report['diagnosis']
    print(f"   数据流状态: {diagnosis['data_flow_status']}")
    print(f"   关键问题: {len(diagnosis['critical_issues'])}个")
    
    for issue in diagnosis['critical_issues']:
        print(f"   - {issue}")
    
    print("\n🔧 建议行动:")
    for action in diagnosis['action_items']:
        print(f"   - {action}")

if __name__ == "__main__":
    main()