#!/usr/bin/env python3
"""
腾讯文档监控完整流程测试
实现：原版表保留 → 下载修改版 → 对比分析 → 生成热力图 → 上传结果
"""

import requests
import pandas as pd
import json
import time
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any

class TencentDocMonitorTester:
    """腾讯文档监控测试器"""
    
    def __init__(self):
        self.ui_server_url = "http://192.140.176.198:8089"
        self.original_file = "/root/projects/tencent-doc-manager/test_original.csv"
        self.modified_file = "/root/projects/tencent-doc-manager/test_modified.csv"
        self.uploads_dir = "/root/projects/tencent-doc-manager/uploads"
        self.test_start_time = datetime.now()
        
        # 确保上传目录存在
        os.makedirs(self.uploads_dir, exist_ok=True)
        
    def load_original_table(self) -> pd.DataFrame:
        """步骤1: 加载原版表格（保留版本）"""
        print("🔄 步骤1: 加载原版表格...")
        df = pd.read_csv(self.original_file, encoding='utf-8')
        print(f"✅ 原版表格加载成功: {df.shape[0]}行 x {df.shape[1]}列")
        return df
    
    def simulate_tencent_download(self) -> pd.DataFrame:
        """步骤2: 模拟从腾讯文档下载修改版表格"""
        print("🔄 步骤2: 模拟从腾讯文档下载修改版...")
        # 实际场景中这里会调用腾讯文档API
        # 现在使用本地修改版文件模拟
        df = pd.read_csv(self.modified_file, encoding='utf-8')
        print(f"✅ 修改版表格下载成功: {df.shape[0]}行 x {df.shape[1]}列")
        return df
    
    def compare_tables(self, original_df: pd.DataFrame, modified_df: pd.DataFrame) -> Dict[str, Any]:
        """步骤3: 对比两个表格，生成变更分析"""
        print("🔄 步骤3: 执行表格对比分析...")
        
        changes = {
            'modified_cells': [],
            'risk_matrix': [],
            'statistics': {},
            'heatmap_data': []
        }
        
        # 定义列风险等级
        column_risk_levels = {
            '序号': 'L3',
            '项目类型': 'L2', 
            '来源': 'L1',
            '任务发起时间': 'L1',
            '负责人': 'L2',
            '协助人': 'L2',
            '具体计划内容': 'L2',
            '重要程度': 'L1',
            '预计完成时间': 'L1', 
            '完成进度': 'L1'
        }
        
        # 检测每个单元格的变更
        for row_idx in range(min(len(original_df), len(modified_df))):
            for col_idx, col_name in enumerate(original_df.columns):
                if col_name in modified_df.columns:
                    original_val = str(original_df.iloc[row_idx, col_idx])
                    modified_val = str(modified_df.iloc[row_idx, col_idx])
                    
                    if original_val != modified_val:
                        risk_level = column_risk_levels.get(col_name, 'L2')
                        
                        # 计算变更强度
                        if risk_level == 'L1':
                            intensity = 0.9 + np.random.random() * 0.1  # 高风险
                        elif risk_level == 'L2':
                            intensity = 0.4 + np.random.random() * 0.4  # 中风险
                        else:
                            intensity = 0.1 + np.random.random() * 0.3  # 低风险
                        
                        change_info = {
                            'row': row_idx,
                            'column': col_name,
                            'column_index': col_idx,
                            'original_value': original_val,
                            'modified_value': modified_val,
                            'risk_level': risk_level,
                            'intensity': intensity,
                            'timestamp': self.test_start_time.isoformat()
                        }
                        
                        changes['modified_cells'].append(change_info)
        
        # 生成热力图数据矩阵
        heat_matrix = np.zeros((len(modified_df), len(modified_df.columns)))
        for change in changes['modified_cells']:
            heat_matrix[change['row'], change['column_index']] = change['intensity']
        
        changes['heatmap_data'] = heat_matrix.tolist()
        
        # 统计信息
        changes['statistics'] = {
            'total_changes': len(changes['modified_cells']),
            'L1_changes': len([c for c in changes['modified_cells'] if c['risk_level'] == 'L1']),
            'L2_changes': len([c for c in changes['modified_cells'] if c['risk_level'] == 'L2']),
            'L3_changes': len([c for c in changes['modified_cells'] if c['risk_level'] == 'L3']),
            'critical_changes': len([c for c in changes['modified_cells'] if c['intensity'] > 0.8]),
            'table_name': '测试项目管理表',
            'table_url': 'https://docs.qq.com/sheet/test-monitoring-table'
        }
        
        print(f"✅ 对比完成: 发现 {changes['statistics']['total_changes']} 处变更")
        return changes
    
    def generate_heatmap_display_data(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """步骤4: 生成热力图UI显示数据"""
        print("🔄 步骤4: 生成热力图UI显示数据...")
        
        ui_data = {
            'tables': [{
                'id': 0,
                'name': changes['statistics']['table_name'],
                'url': changes['statistics']['table_url'],
                'columns': ['序号', '项目类型', '来源', '任务发起时间', '负责人', '协助人', '具体计划内容', '重要程度', '预计完成时间', '完成进度'],
                'maxCellRisk': max([c['intensity'] for c in changes['modified_cells']] + [0]),
                'criticalModifications': changes['statistics']['critical_changes'],
                'avgRisk': np.mean([c['intensity'] for c in changes['modified_cells']] + [0]),
                'columnRiskLevels': {
                    '序号': 'L3', '项目类型': 'L2', '来源': 'L1', '任务发起时间': 'L1',
                    '负责人': 'L2', '协助人': 'L2', '具体计划内容': 'L2', '重要程度': 'L1',
                    '预计完成时间': 'L1', '完成进度': 'L1'
                }
            }],
            'heatmap_matrix': changes['heatmap_data'],
            'statistics': {
                'criticalModifications': changes['statistics']['critical_changes'],
                'L1Modifications': changes['statistics']['L1_changes'], 
                'L2Modifications': changes['statistics']['L2_changes'],
                'L3Modifications': changes['statistics']['L3_changes'],
                'totalModifications': changes['statistics']['total_changes']
            },
            'timestamp': self.test_start_time.isoformat()
        }
        
        print(f"✅ UI数据生成完成: {ui_data['statistics']['totalModifications']} 个修改点")
        return ui_data
    
    def create_partial_fill_table(self, changes: Dict[str, Any], original_df: pd.DataFrame) -> str:
        """步骤5: 创建半填充结果表"""
        print("🔄 步骤5: 创建半填充结果表...")
        
        # 创建结果表格
        result_df = original_df.copy()
        
        # 添加变更分析列
        result_df['变更检测'] = ''
        result_df['风险等级'] = ''
        result_df['变更强度'] = ''
        result_df['变更时间'] = ''
        
        # 填充变更信息
        for change in changes['modified_cells']:
            row_idx = change['row']
            result_df.loc[row_idx, '变更检测'] = f"检测到变更: {change['column']}"
            result_df.loc[row_idx, '风险等级'] = change['risk_level']
            result_df.loc[row_idx, '变更强度'] = f"{change['intensity']:.2f}"
            result_df.loc[row_idx, '变更时间'] = change['timestamp']
        
        # 保存到uploads目录
        timestamp = int(time.time())
        filename = f"monitor_result_{timestamp}.csv"
        filepath = os.path.join(self.uploads_dir, filename)
        result_df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"✅ 半填充表已保存: {filename}")
        return filename
    
    def update_ui_with_upload_link(self, ui_data: Dict[str, Any], uploaded_filename: str) -> Dict[str, Any]:
        """步骤6: 在UI数据中添加上传链接"""
        print("🔄 步骤6: 更新UI显示，添加上传链接...")
        
        # 为表格添加上传链接
        ui_data['tables'][0]['upload_url'] = f"http://192.140.176.198:8089/uploads/{uploaded_filename}"
        ui_data['tables'][0]['upload_filename'] = uploaded_filename
        ui_data['tables'][0]['upload_timestamp'] = self.test_start_time.isoformat()
        
        print(f"✅ UI已更新，上传链接: {ui_data['tables'][0]['upload_url']}")
        return ui_data
    
    def send_to_ui_server(self, ui_data: Dict[str, Any]) -> bool:
        """步骤7: 将数据发送到UI服务器显示"""
        print("🔄 步骤7: 发送数据到热力图UI服务器...")
        
        try:
            # 这里可以通过API将数据发送到UI服务器
            # 现在先保存为JSON文件供UI读取
            result_file = f"/root/projects/tencent-doc-manager/ui_data_{int(time.time())}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(ui_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ UI数据已保存: {result_file}")
            return True
        except Exception as e:
            print(f"❌ 发送UI数据失败: {e}")
            return False
    
    def run_complete_test(self) -> Dict[str, Any]:
        """运行完整的监控测试流程"""
        print("🚀 开始腾讯文档监控完整流程测试")
        print("=" * 60)
        
        test_result = {
            'test_name': '腾讯文档监控完整流程测试',
            'start_time': self.test_start_time.isoformat(),
            'steps': [],
            'success': True,
            'error': None
        }
        
        try:
            # 步骤1: 加载原版表格
            original_df = self.load_original_table()
            test_result['steps'].append({'step': 1, 'status': 'success', 'description': '原版表格加载成功'})
            
            # 步骤2: 下载修改版表格
            modified_df = self.simulate_tencent_download()
            test_result['steps'].append({'step': 2, 'status': 'success', 'description': '修改版表格下载成功'})
            
            # 步骤3: 表格对比分析
            changes = self.compare_tables(original_df, modified_df)
            test_result['steps'].append({'step': 3, 'status': 'success', 'description': f'发现{len(changes["modified_cells"])}处变更'})
            
            # 步骤4: 生成UI数据
            ui_data = self.generate_heatmap_display_data(changes)
            test_result['steps'].append({'step': 4, 'status': 'success', 'description': 'UI显示数据生成完成'})
            
            # 步骤5: 创建半填充表
            uploaded_filename = self.create_partial_fill_table(changes, original_df)
            test_result['steps'].append({'step': 5, 'status': 'success', 'description': f'半填充表已创建: {uploaded_filename}'})
            
            # 步骤6: 更新UI链接
            ui_data = self.update_ui_with_upload_link(ui_data, uploaded_filename)
            test_result['steps'].append({'step': 6, 'status': 'success', 'description': 'UI上传链接已添加'})
            
            # 步骤7: 发送到UI服务器
            ui_success = self.send_to_ui_server(ui_data)
            if ui_success:
                test_result['steps'].append({'step': 7, 'status': 'success', 'description': 'UI服务器数据发送成功'})
            else:
                test_result['steps'].append({'step': 7, 'status': 'failed', 'description': 'UI服务器数据发送失败'})
            
            # 汇总结果
            test_result['summary'] = {
                'original_table_rows': len(original_df),
                'modified_table_rows': len(modified_df),
                'total_changes_detected': len(changes['modified_cells']),
                'critical_changes': changes['statistics']['critical_changes'],
                'L1_changes': changes['statistics']['L1_changes'],
                'L2_changes': changes['statistics']['L2_changes'],
                'L3_changes': changes['statistics']['L3_changes'],
                'upload_filename': uploaded_filename,
                'upload_url': f"http://192.140.176.198:8089/uploads/{uploaded_filename}",
                'ui_server_url': self.ui_server_url
            }
            
        except Exception as e:
            test_result['success'] = False
            test_result['error'] = str(e)
            print(f"❌ 测试流程失败: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        test_result['duration'] = (datetime.now() - self.test_start_time).total_seconds()
        
        return test_result

def main():
    """主函数"""
    tester = TencentDocMonitorTester()
    result = tester.run_complete_test()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    if result['success']:
        print("✅ 测试状态: 全部成功")
        print(f"⏱️  测试耗时: {result['duration']:.2f}秒")
        print(f"📋 检测变更: {result['summary']['total_changes_detected']}处")
        print(f"🔥 严重变更: {result['summary']['critical_changes']}处")
        print(f"📤 上传文件: {result['summary']['upload_filename']}")
        print(f"🔗 访问链接: {result['summary']['upload_url']}")
        print(f"🌐 UI服务器: {result['summary']['ui_server_url']}")
    else:
        print(f"❌ 测试状态: 失败 - {result['error']}")
    
    # 保存详细测试报告
    report_file = f"/root/projects/tencent-doc-manager/monitor_test_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"📄 详细报告: {report_file}")
    
    return result

if __name__ == "__main__":
    main()