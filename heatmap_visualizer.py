#!/usr/bin/env python3
"""
热力图可视化生成器
基于端到端测试结果生成Excel热力图报告
"""

import pandas as pd
import json
import sys
from datetime import datetime
import numpy as np

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

class HeatmapVisualizer:
    """热力图可视化器"""
    
    def __init__(self):
        self.visualization_data = None
        self.original_df = None
        self.modified_df = None
        
    def load_test_data(self):
        """加载测试数据"""
        try:
            # 加载可视化数据
            with open('quick_visualization_data.json', 'r', encoding='utf-8') as f:
                self.visualization_data = json.load(f)
            
            # 加载原始表格数据
            self.original_df = pd.read_csv('enterprise_test_original.csv', encoding='utf-8-sig')
            self.modified_df = pd.read_csv('enterprise_test_modified.csv', encoding='utf-8-sig')
            
            print("✅ 测试数据加载成功")
            return True
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
    
    def generate_excel_heatmap(self):
        """生成Excel热力图报告"""
        if not self.visualization_data:
            print("❌ 没有可视化数据")
            return
        
        # 获取基本信息
        matrix_size = self.visualization_data["matrix_size"]
        risk_matrix = self.visualization_data["risk_matrix"]
        modifications = self.visualization_data["modification_locations"]
        risk_distribution = self.visualization_data["risk_distribution"]
        
        # 创建Excel writer
        with pd.ExcelWriter('热力图可视化报告.xlsx', engine='openpyxl') as writer:
            
            # 工作表1：原始数据对比
            self.create_data_comparison_sheet(writer)
            
            # 工作表2：风险热力图
            self.create_risk_heatmap_sheet(writer, risk_matrix)
            
            # 工作表3：变更详情
            self.create_change_details_sheet(writer, modifications)
            
            # 工作表4：统计分析
            self.create_statistics_sheet(writer, risk_distribution)
        
        print("✅ Excel热力图报告生成完成: 热力图可视化报告.xlsx")
    
    def create_data_comparison_sheet(self, writer):
        """创建数据对比工作表"""
        # 合并原始数据和修改数据进行对比显示
        comparison_data = []
        
        # 添加表头
        comparison_data.append(['数据版本'] + list(self.original_df.columns))
        
        # 添加原始数据
        for idx, row in self.original_df.iterrows():
            comparison_data.append(['原始版'] + row.tolist())
        
        # 添加修改数据
        for idx, row in self.modified_df.iterrows():
            comparison_data.append(['修改版'] + row.tolist())
        
        # 创建DataFrame
        comparison_df = pd.DataFrame(comparison_data[1:], columns=comparison_data[0])
        
        # 写入Excel
        comparison_df.to_excel(writer, sheet_name='数据对比', index=False)
        print("✅ 数据对比工作表创建完成")
    
    def create_risk_heatmap_sheet(self, writer, risk_matrix):
        """创建风险热力图工作表"""
        # 创建风险等级映射
        risk_labels = {0: '无变更', 1: 'L3-低风险', 2: 'L2-中风险', 3: 'L1-高风险'}
        
        # 转换风险矩阵为DataFrame
        columns = list(self.original_df.columns)
        risk_df = pd.DataFrame(risk_matrix, columns=columns)
        
        # 添加行标签
        risk_df.insert(0, '数据行', [f'第{i+1}行' for i in range(len(risk_matrix))])
        
        # 写入Excel
        risk_df.to_excel(writer, sheet_name='风险热力图', index=False)
        print("✅ 风险热力图工作表创建完成")
    
    def create_change_details_sheet(self, writer, modifications):
        """创建变更详情工作表"""
        change_details = []
        
        for mod in modifications:
            change_details.append({
                '行号': mod['row'] + 1,
                '列号': mod['col'] + 1,
                '列名': mod['column_name'],
                '风险等级': mod['risk_level'],
                '变更类型': mod['change_type'],
                '风险描述': self.get_risk_description(mod['risk_level'])
            })
        
        change_df = pd.DataFrame(change_details)
        
        # 添加原值和新值对比
        if len(self.original_df) > 0 and len(self.modified_df) > 0:
            original_values = []
            new_values = []
            
            for mod in modifications:
                row_idx = mod['row']
                col_name = mod['column_name']
                
                # 获取原值
                if row_idx < len(self.original_df) and col_name in self.original_df.columns:
                    original_val = self.original_df.iloc[row_idx][col_name]
                else:
                    original_val = '无数据'
                
                # 获取新值
                if row_idx < len(self.modified_df) and col_name in self.modified_df.columns:
                    new_val = self.modified_df.iloc[row_idx][col_name]
                else:
                    new_val = '新增行'
                
                original_values.append(str(original_val))
                new_values.append(str(new_val))
            
            change_df['原值'] = original_values
            change_df['新值'] = new_values
        
        change_df.to_excel(writer, sheet_name='变更详情', index=False)
        print("✅ 变更详情工作表创建完成")
    
    def create_statistics_sheet(self, writer, risk_distribution):
        """创建统计分析工作表"""
        stats_data = []
        
        # 基本统计信息
        stats_data.append(['统计项目', '数值'])
        stats_data.append(['原始数据行数', len(self.original_df)])
        stats_data.append(['修改数据行数', len(self.modified_df)])
        stats_data.append(['分析列数', len(self.original_df.columns)])
        stats_data.append(['总变更数', sum(risk_distribution.values())])
        stats_data.append(['', ''])
        
        # 风险分布统计
        stats_data.append(['风险等级分布', ''])
        stats_data.append(['L1级别(高风险)', risk_distribution.get('L1', 0)])
        stats_data.append(['L2级别(中风险)', risk_distribution.get('L2', 0)])
        stats_data.append(['L3级别(低风险)', risk_distribution.get('L3', 0)])
        stats_data.append(['', ''])
        
        # 风险占比
        total_changes = sum(risk_distribution.values())
        if total_changes > 0:
            stats_data.append(['风险占比', ''])
            stats_data.append(['L1占比', f"{risk_distribution.get('L1', 0)/total_changes*100:.1f}%"])
            stats_data.append(['L2占比', f"{risk_distribution.get('L2', 0)/total_changes*100:.1f}%"])
            stats_data.append(['L3占比', f"{risk_distribution.get('L3', 0)/total_changes*100:.1f}%"])
            stats_data.append(['', ''])
        
        # 生成时间
        stats_data.append(['报告生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        stats_df = pd.DataFrame(stats_data[1:], columns=stats_data[0])
        stats_df.to_excel(writer, sheet_name='统计分析', index=False)
        print("✅ 统计分析工作表创建完成")
    
    def get_risk_description(self, risk_level):
        """获取风险描述"""
        descriptions = {
            'L1': '绝对禁止修改，需要管理员权限',
            'L2': '需要AI分析和人工审核',
            'L3': '可以自由编辑，低风险'
        }
        return descriptions.get(risk_level, '未知风险等级')
    
    def generate_html_heatmap(self):
        """生成HTML热力图可视化"""
        if not self.visualization_data:
            print("❌ 没有可视化数据")
            return
        
        risk_matrix = self.visualization_data["risk_matrix"]
        columns = list(self.original_df.columns)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>表格变更风险热力图</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .heatmap-container {{
            overflow-x: auto;
            border: 1px solid #ddd;
        }}
        .heatmap {{
            border-collapse: collapse;
            width: 100%;
            min-width: 800px;
        }}
        .heatmap th, .heatmap td {{
            border: 1px solid #ddd;
            padding: 5px;
            text-align: center;
            min-width: 40px;
            height: 30px;
        }}
        .heatmap th {{
            background-color: #f2f2f2;
            font-weight: bold;
            font-size: 10px;
        }}
        .risk-0 {{ background-color: #ffffff; }}
        .risk-1 {{ background-color: #ffeb3b; color: #333; }}
        .risk-2 {{ background-color: #ff9800; color: white; }}
        .risk-3 {{ background-color: #f44336; color: white; }}
        .legend {{
            margin: 20px 0;
        }}
        .legend-item {{
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            border-radius: 3px;
        }}
        .stats {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>📊 表格变更风险热力图</h1>
    
    <div class="stats">
        <h3>📈 变更统计</h3>
        <p><strong>总变更数:</strong> {sum(self.visualization_data['risk_distribution'].values())}</p>
        <p><strong>L1级别(高风险):</strong> {self.visualization_data['risk_distribution'].get('L1', 0)}个</p>
        <p><strong>L2级别(中风险):</strong> {self.visualization_data['risk_distribution'].get('L2', 0)}个</p>
        <p><strong>L3级别(低风险):</strong> {self.visualization_data['risk_distribution'].get('L3', 0)}个</p>
        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="legend">
        <h3>🎨 风险等级图例</h3>
        <span class="legend-item risk-0">无变更</span>
        <span class="legend-item risk-1">L3-低风险</span>
        <span class="legend-item risk-2">L2-中风险</span>
        <span class="legend-item risk-3">L1-高风险</span>
    </div>
    
    <div class="heatmap-container">
        <table class="heatmap">
            <thead>
                <tr>
                    <th>行号</th>
"""
        
        # 添加列标题
        for col in columns:
            html_content += f'<th style="transform: rotate(-45deg); transform-origin: center;">{col[:10]}...</th>'
        
        html_content += """
                </tr>
            </thead>
            <tbody>
"""
        
        # 添加数据行
        for i, row in enumerate(risk_matrix):
            html_content += f"<tr><td>第{i+1}行</td>"
            for risk_val in row:
                html_content += f'<td class="risk-{risk_val}">{risk_val if risk_val > 0 else ""}</td>'
            html_content += "</tr>"
        
        html_content += """
            </tbody>
        </table>
    </div>
    
    <div style="margin-top: 20px;">
        <h3>📝 说明</h3>
        <ul>
            <li><strong>L1级别(红色):</strong> 绝对禁止修改的关键字段，如重要程度、目标对齐等</li>
            <li><strong>L2级别(橙色):</strong> 需要AI分析和人工审核的字段，如具体计划内容、负责人等</li>
            <li><strong>L3级别(黄色):</strong> 可以自由编辑的低风险字段，如进度、时间等</li>
        </ul>
    </div>
    
</body>
</html>
"""
        
        # 保存HTML文件
        with open('热力图可视化报告.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ HTML热力图报告生成完成: 热力图可视化报告.html")
    
    def run_visualization_pipeline(self):
        """运行完整的可视化流程"""
        print("🎨 开始生成热力图和可视化报告")
        print("=" * 50)
        
        # 加载测试数据
        if not self.load_test_data():
            return False
        
        # 生成Excel报告
        try:
            self.generate_excel_heatmap()
        except Exception as e:
            print(f"❌ Excel报告生成失败: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 生成HTML报告
        try:
            self.generate_html_heatmap()
        except Exception as e:
            print(f"❌ HTML报告生成失败: {e}")
            import traceback
            print(traceback.format_exc())
        
        print("\n✅ 可视化报告生成完成!")
        print("📁 生成的文件:")
        print("   📊 Excel报告: 热力图可视化报告.xlsx")
        print("   🌐 HTML报告: 热力图可视化报告.html")
        
        return True

def main():
    """主函数"""
    visualizer = HeatmapVisualizer()
    result = visualizer.run_visualization_pipeline()
    
    if result:
        print("\n🎉 热力图可视化生成成功!")
    else:
        print("\n❌ 热力图可视化生成失败")

if __name__ == "__main__":
    main()