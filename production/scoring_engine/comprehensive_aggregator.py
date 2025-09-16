#!/usr/bin/env python3
"""
综合集成打分引擎 - 综合汇总模块
将详细打分文件汇总为列级综合报告
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import glob

# 添加上级目录到路径以导入PathManager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_modules.path_manager import path_manager
from core_modules.all_tables_discoverer import AllTablesDiscoverer


class ComprehensiveAggregator:
    """综合打分汇总器"""
    
    def __init__(self):
        """初始化汇总器"""
        self.table_scores = []
        self.all_column_data = defaultdict(list)
        self.cross_table_patterns = []
        self.tables_discoverer = AllTablesDiscoverer()
    
    def load_detailed_score(self, file_path: str) -> Dict:
        """加载详细打分文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_table_url(self, table_name: str) -> str:
        """根据表名获取腾讯文档URL（实际项目中应从配置读取）"""
        # 这里使用实际的映射关系
        url_mapping = {
            "副本-测试版本-出国销售计划表": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
            "副本-测试版本-回国销售计划表": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
            "测试版本-小红书部门": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
        }
        
        # 模糊匹配
        for key, url in url_mapping.items():
            if key in table_name or table_name in key:
                return url
        
        return ""  # 未找到映射
    
    def create_empty_table_score(self, table_info: Dict) -> Dict:
        """
        为未修改的表格创建空的打分结构
        
        Args:
            table_info: 表格信息（包含table_name, table_url等）
            
        Returns:
            空的表格打分结构
        """
        # 获取CSV文件的真实总行数（即使没有修改）
        table_name = table_info['table_name']
        total_rows = self.get_csv_total_rows(table_name)
        
        return {
            'table_name': table_name,
            'table_url': table_info.get('table_url', ''),
            'total_rows': total_rows,  # 添加总行数
            'modifications_count': 0,
            'column_scores': {},  # 空的列打分
            'table_summary': {
                'overall_risk_score': 0.0,
                'risk_level': 'UNMODIFIED',
                'high_risk_columns': 0,
                'total_columns_modified': 0,
                'ai_intervention_rate': '0%',
                'confidence_score': 1.0
            }
        }
    
    def calculate_column_aggregates(self, scores: List[Dict]) -> Dict:
        """
        计算列级汇总数据
        
        Args:
            scores: 详细打分列表
            
        Returns:
            列级汇总字典
        """
        column_data = defaultdict(lambda: {
            'scores': [],
            'modifications': 0,
            'ai_decisions': defaultdict(int),
            'column_level': ''
        })
        
        # 收集每列数据
        for score in scores:
            col_name = score['column_name']
            col_level = score['column_level']
            final_score = score['scoring_details']['final_score']
            
            column_data[col_name]['scores'].append(final_score)
            column_data[col_name]['modifications'] += 1
            column_data[col_name]['column_level'] = col_level
            
            # 统计AI决策
            if score['ai_analysis'].get('ai_used'):
                decision = score['ai_analysis'].get('ai_decision', 'UNKNOWN')
                column_data[col_name]['ai_decisions'][decision] += 1
        
        # 计算汇总指标
        result = {}
        for col_name, data in column_data.items():
            scores_list = data['scores']
            
            # 加权平均（最新修改权重更高）
            if scores_list:
                weights = [1.0 + 0.1 * i for i in range(len(scores_list))]
                weighted_sum = sum(s * w for s, w in zip(scores_list, weights))
                weighted_avg = weighted_sum / sum(weights)
            else:
                weighted_avg = 0
            
            # 风险趋势分析
            trend = self.analyze_risk_trend(scores_list)
            
            # 构建结果
            result[col_name] = {
                'column_level': data['column_level'],
                'modifications': data['modifications'],
                'scores': [round(s, 3) for s in scores_list],
                'aggregated_score': round(weighted_avg, 3),
                'max_score': round(max(scores_list), 3) if scores_list else 0,
                'min_score': round(min(scores_list), 3) if scores_list else 0,
                'risk_trend': trend,
                'ai_decisions': dict(data['ai_decisions']) if data['ai_decisions'] else None
            }
        
        return result
    
    def analyze_risk_trend(self, scores: List[float]) -> str:
        """
        分析风险趋势
        
        Args:
            scores: 分数列表（按时间顺序）
            
        Returns:
            趋势: increasing/decreasing/stable
        """
        if len(scores) < 3:
            return 'stable'
        
        # 比较最近的和之前的平均值
        recent_avg = sum(scores[-3:]) / min(3, len(scores[-3:]))
        earlier_scores = scores[:-3]
        
        if earlier_scores:
            earlier_avg = sum(earlier_scores) / len(earlier_scores)
        else:
            return 'stable'
        
        # 判断趋势
        if recent_avg > earlier_avg * 1.1:
            return 'increasing'
        elif recent_avg < earlier_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def calculate_table_summary(self, column_scores: Dict) -> Dict:
        """
        计算表格汇总信息
        
        Args:
            column_scores: 列级打分数据
            
        Returns:
            表格汇总
        """
        # 计算总体风险分
        all_scores = []
        for col_data in column_scores.values():
            all_scores.append(col_data['aggregated_score'])
        
        if all_scores:
            overall_risk = sum(all_scores) / len(all_scores)
        else:
            overall_risk = 0
        
        # 风险等级判定
        if overall_risk >= 0.8:
            risk_level = "EXTREME_HIGH"
            action = "immediate_review"
        elif overall_risk >= 0.6:
            risk_level = "HIGH"
            action = "priority_review"
        elif overall_risk >= 0.4:
            risk_level = "MEDIUM"
            action = "standard_review"
        elif overall_risk >= 0.2:
            risk_level = "LOW"
            action = "periodic_check"
        else:
            risk_level = "EXTREME_LOW"
            action = "monitoring_only"
        
        # 找出高风险列
        top_risks = []
        for col_name, col_data in column_scores.items():
            if col_data['aggregated_score'] >= 0.4:  # 中等风险以上
                top_risks.append({
                    'column': col_name,
                    'score': col_data['aggregated_score']
                })
        
        # 按分数排序
        top_risks.sort(key=lambda x: x['score'], reverse=True)
        top_risks = top_risks[:5]  # 只保留前5个
        
        return {
            'overall_risk_score': round(overall_risk, 3),
            'risk_level': risk_level,
            'top_risks': top_risks,
            'recommended_action': action
        }
    
    def detect_cross_table_patterns(self) -> Dict:
        """
        检测跨表模式
        
        Returns:
            跨表分析结果
        """
        # 列级风险排名
        column_risk_data = defaultdict(lambda: {
            'scores': [],
            'tables': set()
        })
        
        for table_score in self.table_scores:
            table_name = table_score['table_name']
            for col_name, col_data in table_score['column_scores'].items():
                column_risk_data[col_name]['scores'].append(col_data['aggregated_score'])
                column_risk_data[col_name]['tables'].add(table_name)
        
        # 计算列级平均风险
        column_risk_ranking = []
        for col_name, data in column_risk_data.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                column_risk_ranking.append({
                    'column': col_name,
                    'avg_score': round(avg_score, 3),
                    'tables_affected': len(data['tables'])
                })
        
        # 排序
        column_risk_ranking.sort(key=lambda x: x['avg_score'], reverse=True)
        
        # 检测系统性变化
        systematic_changes = []
        
        # 检查是否有多个表的同一列都有高风险
        for col_name, data in column_risk_data.items():
            high_risk_tables = []
            tables_list = list(data['tables'])
            for i, score in enumerate(data['scores']):
                if score >= 0.6 and i < len(tables_list):  # 高风险阈值且索引有效
                    high_risk_tables.append(tables_list[i])
            
            if len(high_risk_tables) >= 2:
                systematic_changes.append({
                    'pattern': f"{col_name}批量变更",
                    'affected_columns': [col_name],
                    'tables': high_risk_tables,
                    'risk_boost': 1.3
                })
        
        # 检测异常
        anomalies = []
        for table_score in self.table_scores:
            # 检查是否有表格的多个列都是高风险
            high_risk_cols = []
            for col_name, col_data in table_score['column_scores'].items():
                if col_data['aggregated_score'] >= 0.6:
                    high_risk_cols.append(col_name)
            
            if len(high_risk_cols) >= 3:
                anomalies.append({
                    'type': '多列高风险',
                    'columns': high_risk_cols,
                    'table': table_score['table_name'],
                    'severity': 'HIGH'
                })
        
        return {
            'column_risk_ranking': column_risk_ranking[:10],  # 前10个
            'pattern_detection': {
                'systematic_changes': systematic_changes,
                'anomalies': anomalies
            }
        }
    
    def calculate_overall_metrics(self) -> Dict:
        """计算系统总体指标"""
        total_modifications = 0
        total_high_risks = 0
        total_critical_changes = 0
        total_ai_calls = 0
        total_l2_columns = 0
        
        for table_score in self.table_scores:
            total_modifications += table_score['modifications_count']
            
            # 统计高风险
            for col_data in table_score['column_scores'].values():
                if col_data['aggregated_score'] >= 0.6:
                    total_high_risks += col_data['modifications']
                if col_data['aggregated_score'] >= 0.8:
                    total_critical_changes += col_data['modifications']
                
                # 统计AI使用
                if col_data['column_level'] == 'L2':
                    total_l2_columns += col_data['modifications']
                if col_data['ai_decisions']:
                    total_ai_calls += col_data['modifications']
        
        # 计算系统总体风险
        all_table_risks = [t['table_summary']['overall_risk_score'] 
                          for t in self.table_scores]
        system_risk = sum(all_table_risks) / len(all_table_risks) if all_table_risks else 0
        
        # 风险等级
        if system_risk >= 0.6:
            risk_level = "HIGH"
        elif system_risk >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # AI介入率
        ai_intervention_rate = f"{(total_ai_calls / total_l2_columns * 100):.1f}%" \
                               if total_l2_columns > 0 else "0%"
        
        # Token效率（基于两层架构的理论值）
        token_efficiency = "98.6%"  # 根据规范文档的实测值
        
        return {
            'system_risk_score': round(system_risk, 3),
            'risk_level': risk_level,
            'total_high_risks': total_high_risks,
            'total_critical_changes': total_critical_changes,
            'ai_intervention_rate': ai_intervention_rate,
            'token_efficiency': token_efficiency
        }
    
    def get_csv_total_rows(self, table_name: str) -> int:
        """
        获取CSV文件的真实总行数
        
        Args:
            table_name: 表格名称
            
        Returns:
            总行数
        """
        import glob
        import csv
        
        # 查找对应的CSV文件
        csv_patterns = [
            f"/root/projects/tencent-doc-manager/csv_versions/**/*{table_name}*.csv",
            f"/root/projects/tencent-doc-manager/csv_versions/**/*{table_name.replace('-', '_')}*.csv"
        ]
        
        for pattern in csv_patterns:
            files = glob.glob(pattern, recursive=True)
            if files:
                # 使用最新的文件
                latest_file = sorted(files)[-1]
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        row_count = sum(1 for line in f) - 1  # 减去标题行
                    print(f"表格 {table_name} 的总行数: {row_count} (来自 {latest_file})")
                    return row_count
                except Exception as e:
                    print(f"读取CSV文件失败 {latest_file}: {e}")
        
        # 如果找不到文件，返回默认值
        print(f"警告: 未找到表格 {table_name} 的CSV文件，使用默认值270")
        return 270
    
    def extract_modified_rows(self, scores: List[Dict]) -> Dict[str, List[int]]:
        """
        从详细打分中提取每列的修改行号
        
        Args:
            scores: 详细打分数据
            
        Returns:
            按列名分组的修改行号字典
        """
        import re
        column_modified_rows = {}
        
        for score in scores:
            cell = score.get('cell', '')
            column_name = score.get('column_name', '')
            
            if cell and column_name:
                # 提取行号（如C4中的4）
                match = re.match(r'([A-Z]+)(\d+)', cell)
                if match:
                    row_num = int(match.group(2))
                    
                    if column_name not in column_modified_rows:
                        column_modified_rows[column_name] = []
                    
                    column_modified_rows[column_name].append(row_num)
        
        # 对每列的行号排序
        for col in column_modified_rows:
            column_modified_rows[col] = sorted(list(set(column_modified_rows[col])))
        
        return column_modified_rows

    def aggregate_files(self, detailed_files: List[str], week: str = None) -> Dict:
        """
        汇总多个详细打分文件
        
        Args:
            detailed_files: 详细打分文件路径列表
            week: 周数标识（可选）
            
        Returns:
            综合打分报告
        """
        if not week:
            week = datetime.now().strftime('W%V')
        
        # 处理每个详细文件
        for file_path in detailed_files:
            if not os.path.exists(file_path):
                print(f"警告: 文件不存在 {file_path}")
                continue
            
            # 加载详细打分
            detailed = self.load_detailed_score(file_path)
            
            # 提取表名
            table_name = detailed['metadata'].get('table_name', 
                                                  os.path.basename(file_path))
            
            # 获取CSV文件的真实总行数
            total_rows = self.get_csv_total_rows(table_name)
            
            # 提取每列的修改行号
            column_modified_rows = self.extract_modified_rows(detailed['scores'])
            
            # 计算列级汇总（增强版，包含修改行号）
            column_scores = self.calculate_column_aggregates(detailed['scores'])
            
            # 为每列添加修改行号信息
            for col_name in column_scores:
                if col_name in column_modified_rows:
                    column_scores[col_name]['modified_rows'] = column_modified_rows[col_name]
                else:
                    column_scores[col_name]['modified_rows'] = []
            
            # 计算表格汇总
            table_summary = self.calculate_table_summary(column_scores)
            
            # 添加到结果
            self.table_scores.append({
                'table_name': table_name,
                'table_url': self.extract_table_url(table_name),
                'total_rows': total_rows,  # 新增：总行数
                'modifications_count': detailed['metadata']['total_modifications'],
                'column_scores': column_scores,
                'table_summary': table_summary
            })
        
        # 获取所有配置的表格（包括未修改的）
        all_tables_discovery = self.tables_discoverer.discover_all_tables_with_status()
        processed_table_names = {t['table_name'] for t in self.table_scores}
        
        # 为未修改的表格添加空的打分记录
        for table_info in all_tables_discovery['tables']:
            if table_info['table_name'] not in processed_table_names:
                # 创建未修改表格的空打分
                empty_score = self.create_empty_table_score(table_info)
                self.table_scores.append(empty_score)
                print(f"添加未修改表格: {table_info['table_name']}")
        
        # 跨表分析
        cross_table_analysis = self.detect_cross_table_patterns()
        
        # 总体指标
        overall_metrics = self.calculate_overall_metrics()
        cross_table_analysis['overall_metrics'] = overall_metrics
        
        # 构建最终报告
        report = {
            'metadata': {
                'week': week,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_tables': len(self.table_scores),
                'total_modifications': sum(t['modifications_count'] 
                                         for t in self.table_scores),
                'scoring_version': 'v1.0'
            },
            'table_scores': self.table_scores,
            'cross_table_analysis': cross_table_analysis
        }
        
        return report
    
    def save_report(self, report: Dict, output_dir: str = None) -> str:
        """
        保存综合报告
        
        Args:
            report: 综合报告数据
            output_dir: 输出目录
            
        Returns:
            输出文件路径
        """
        if not output_dir:
            # 使用统一路径管理器获取正确路径
            output_dir = str(path_manager.get_scoring_results_path(detailed=False))
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        week = report['metadata']['week']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            output_dir,
            f"comprehensive_score_{week}_{timestamp}.json"
        )
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"综合报告已保存: {output_file}")
        return output_file


def main():
    """主函数（测试用）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='综合打分引擎 - 汇总模块')
    parser.add_argument('--input-dir', help='详细打分文件目录')
    parser.add_argument('--files', nargs='+', help='详细打分文件列表')
    parser.add_argument('--week', help='周数标识（如W36）')
    parser.add_argument('--output-dir', help='输出目录')
    
    args = parser.parse_args()
    
    # 获取输入文件
    if args.files:
        detailed_files = args.files
    elif args.input_dir:
        # 从目录读取所有详细打分文件
        pattern = os.path.join(args.input_dir, 'detailed_score_*.json')
        detailed_files = glob.glob(pattern)
    else:
        print("错误: 请指定输入文件或目录")
        sys.exit(1)
    
    if not detailed_files:
        print("错误: 没有找到详细打分文件")
        sys.exit(1)
    
    # 创建汇总器
    aggregator = ComprehensiveAggregator()
    
    # 处理文件
    try:
        report = aggregator.aggregate_files(detailed_files, args.week)
        output_file = aggregator.save_report(report, args.output_dir)
        print(f"成功生成综合报告: {output_file}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()