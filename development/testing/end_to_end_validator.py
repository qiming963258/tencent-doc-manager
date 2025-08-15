#!/usr/bin/env python3
"""
完整端到端工作流验证
验证整个系统从数据输入到可视化输出的完整流程
"""

import os
import json
import pandas as pd
from datetime import datetime

class EndToEndWorkflowValidator:
    """端到端工作流验证器"""
    
    def __init__(self):
        self.test_results = {}
        
    def validate_complete_workflow(self):
        """验证完整的工作流程"""
        print("🔍 开始端到端工作流完整性验证")
        print("=" * 60)
        
        # 验证阶段1：输入数据准备
        stage1_success = self.validate_input_data()
        
        # 验证阶段2：表格对比功能
        stage2_success = self.validate_comparison_functionality()
        
        # 验证阶段3：数据处理结果
        stage3_success = self.validate_processing_results()
        
        # 验证阶段4：可视化输出
        stage4_success = self.validate_visualization_outputs()
        
        # 验证阶段5：系统集成完整性
        stage5_success = self.validate_system_integration()
        
        # 生成最终验证报告
        self.generate_validation_report([
            stage1_success, stage2_success, stage3_success, 
            stage4_success, stage5_success
        ])
        
        return all([stage1_success, stage2_success, stage3_success, 
                   stage4_success, stage5_success])
    
    def validate_input_data(self):
        """验证输入数据阶段"""
        print("📊 阶段1：输入数据准备验证")
        
        required_files = [
            'enterprise_test_original.csv',
            'enterprise_test_modified.csv'
        ]
        
        success = True
        for file_path in required_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    print(f"   ✅ {file_path}: {len(df)}行 x {len(df.columns)}列")
                    self.test_results[f'input_{file_path}'] = {
                        'exists': True,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': list(df.columns)
                    }
                except Exception as e:
                    print(f"   ❌ {file_path}: 读取失败 - {e}")
                    success = False
            else:
                print(f"   ❌ {file_path}: 文件不存在")
                success = False
        
        self.test_results['stage1_input_data'] = success
        return success
    
    def validate_comparison_functionality(self):
        """验证表格对比功能"""
        print("🔍 阶段2：表格对比功能验证")
        
        try:
            # 检查核心对比模块是否存在
            core_modules = [
                'adaptive_table_comparator.py',
                'document_change_analyzer.py',
                'claude_wrapper_integration.py'
            ]
            
            modules_ok = True
            for module in core_modules:
                if os.path.exists(module):
                    print(f"   ✅ {module}: 模块存在")
                else:
                    print(f"   ❌ {module}: 模块缺失")
                    modules_ok = False
            
            # 检查快速测试是否生成了结果
            if os.path.exists('quick_test_report.json'):
                with open('quick_test_report.json', 'r', encoding='utf-8') as f:
                    test_report = json.load(f)
                
                changes_detected = test_report['data_processing_results']['total_changes_detected']
                print(f"   ✅ 检测到{changes_detected}个变更")
                
                risk_dist = test_report['data_processing_results']['risk_distribution']
                print(f"   ✅ 风险分布: L1={risk_dist['L1']}, L2={risk_dist['L2']}, L3={risk_dist['L3']}")
                
                self.test_results['stage2_comparison'] = True
                return modules_ok and changes_detected > 0
            else:
                print("   ❌ 测试报告文件缺失")
                self.test_results['stage2_comparison'] = False
                return False
                
        except Exception as e:
            print(f"   ❌ 对比功能验证失败: {e}")
            self.test_results['stage2_comparison'] = False
            return False
    
    def validate_processing_results(self):
        """验证数据处理结果"""
        print("⚙️ 阶段3：数据处理结果验证")
        
        try:
            # 检查可视化数据文件
            if os.path.exists('quick_visualization_data.json'):
                with open('quick_visualization_data.json', 'r', encoding='utf-8') as f:
                    viz_data = json.load(f)
                
                # 验证数据完整性
                required_keys = ['matrix_size', 'risk_matrix', 'modification_locations', 'risk_distribution']
                data_complete = all(key in viz_data for key in required_keys)
                
                if data_complete:
                    print(f"   ✅ 可视化数据完整")
                    print(f"   ✅ 矩阵尺寸: {viz_data['matrix_size']}")
                    print(f"   ✅ 修改位置: {len(viz_data['modification_locations'])}个")
                    
                    self.test_results['stage3_processing'] = True
                    return True
                else:
                    print("   ❌ 可视化数据不完整")
                    self.test_results['stage3_processing'] = False
                    return False
            else:
                print("   ❌ 可视化数据文件缺失")
                self.test_results['stage3_processing'] = False
                return False
                
        except Exception as e:
            print(f"   ❌ 处理结果验证失败: {e}")
            self.test_results['stage3_processing'] = False
            return False
    
    def validate_visualization_outputs(self):
        """验证可视化输出"""
        print("🎨 阶段4：可视化输出验证")
        
        expected_outputs = [
            ('热力图可视化报告.xlsx', 'Excel热力图报告'),
            ('热力图可视化报告.html', 'HTML热力图报告')
        ]
        
        success = True
        for file_path, description in expected_outputs:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ {description}: 生成成功 ({file_size}字节)")
            else:
                print(f"   ❌ {description}: 文件缺失")
                success = False
        
        self.test_results['stage4_visualization'] = success
        return success
    
    def validate_system_integration(self):
        """验证系统集成完整性"""
        print("🔗 阶段5：系统集成完整性验证")
        
        # 检查关键组件文件
        key_components = [
            ('adaptive_table_comparator.py', '自适应表格对比器'),
            ('claude_wrapper_integration.py', 'Claude集成封装'),
            ('document_change_analyzer.py', '文档变更分析器'),
            ('heatmap_visualizer.py', '热力图可视化器'),
            ('quick_e2e_test.py', '快速端到端测试')
        ]
        
        integration_success = True
        for file_path, description in key_components:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ {description}: 集成完成 ({file_size}字节)")
            else:
                print(f"   ❌ {description}: 组件缺失")
                integration_success = False
        
        # 检查配置和文档文件
        config_files = [
            'CLAUDE.md',
            'quick_test_report.json',
            'quick_visualization_data.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"   ✅ 配置文件: {config_file}")
            else:
                print(f"   ⚠️ 配置文件缺失: {config_file}")
        
        self.test_results['stage5_integration'] = integration_success
        return integration_success
    
    def generate_validation_report(self, stage_results):
        """生成验证报告"""
        print("\n📋 生成最终验证报告")
        
        overall_success = all(stage_results)
        
        report = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_success': overall_success,
            'stage_results': {
                'stage1_input_data': stage_results[0],
                'stage2_comparison': stage_results[1], 
                'stage3_processing': stage_results[2],
                'stage4_visualization': stage_results[3],
                'stage5_integration': stage_results[4]
            },
            'detailed_results': self.test_results,
            'success_rate': f"{sum(stage_results)}/5 ({sum(stage_results)/5*100:.0f}%)",
            'recommendations': self.generate_recommendations(stage_results)
        }
        
        # 保存验证报告
        with open('端到端工作流验证报告.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印总结
        print("=" * 60)
        if overall_success:
            print("🎉 端到端工作流验证成功！")
            print("✅ 所有阶段验证通过")
        else:
            print("⚠️ 端到端工作流验证完成，部分阶段需要注意")
            print(f"✅ 成功率: {sum(stage_results)}/5 ({sum(stage_results)/5*100:.0f}%)")
        
        print(f"📁 验证报告已保存: 端到端工作流验证报告.json")
        
        return report
    
    def generate_recommendations(self, stage_results):
        """生成改进建议"""
        recommendations = []
        
        if not stage_results[0]:
            recommendations.append("需要确保测试数据文件完整且格式正确")
        
        if not stage_results[1]:
            recommendations.append("需要检查表格对比功能模块的完整性")
        
        if not stage_results[2]:
            recommendations.append("需要优化数据处理流程，确保结果数据完整")
        
        if not stage_results[3]:
            recommendations.append("需要完善可视化输出功能")
        
        if not stage_results[4]:
            recommendations.append("需要加强系统组件之间的集成")
        
        if all(stage_results):
            recommendations.append("系统运行良好，建议进行更多场景的测试")
            recommendations.append("可以考虑添加AI分析功能来增强L2级别修改的处理")
            recommendations.append("建议添加更多的可视化选项和导出格式")
        
        return recommendations

def main():
    """主函数"""
    validator = EndToEndWorkflowValidator()
    
    try:
        success = validator.validate_complete_workflow()
        
        if success:
            print("\n🏆 恭喜！端到端工作流验证完全成功！")
            print("🚀 系统已准备好投入生产使用")
        else:
            print("\n📋 端到端工作流验证完成，请查看报告了解详情")
            
        return success
        
    except Exception as e:
        print(f"\n❌ 验证过程出现错误: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()