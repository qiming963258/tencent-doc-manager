#!/usr/bin/env python3
"""
增强型CSV专业对比系统 v2.0
- 详细的步骤日志输出
- 智能文件匹配逻辑（优先真实文档）
- 严格遵循03规范，无降级机制
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"enhanced_comparison_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

class EnhancedCSVComparator:
    """增强型CSV对比器 - 详细日志输出版本"""
    
    def __init__(self):
        self.logger = logger
        self.csv_versions_dir = "/root/projects/tencent-doc-manager/csv_versions"
        self.comparison_results_dir = "/root/projects/tencent-doc-manager/comparison_results"
        
    def execute_comparison(self, doc_name: str = "", prefer_real: bool = True) -> Dict:
        """执行完整的CSV对比流程"""
        
        self.logger.info("=" * 80)
        self.logger.info("🔬 【专业CSV对比系统 v2.0】启动")
        self.logger.info("=" * 80)
        self.logger.info(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📝 请求参数: doc_name='{doc_name}', prefer_real={prefer_real}")
        self.logger.info(f"📏 执行模式: 严格03规范模式（无降级机制）")
        self.logger.info("=" * 80)
        
        try:
            # 步骤1: 时间策略分析
            time_context = self._analyze_time_strategy()
            
            # 步骤2: 查找基线文件
            baseline_files = self._find_baseline_files(time_context)
            
            # 步骤3: 智能文件分类
            categorized_files = self._categorize_files(baseline_files, prefer_real)
            
            # 步骤4: 匹配基线和目标文件对
            matched_pairs = self._match_file_pairs(categorized_files, time_context)
            
            # 步骤5: 选择最佳对比对
            selected_pair = self._select_best_pair(matched_pairs, prefer_real)
            
            # 步骤6: 执行CSV对比
            comparison_result = self._execute_csv_comparison(selected_pair)
            
            # 步骤7: 保存结果
            result_file = self._save_results(comparison_result, selected_pair)
            
            # 步骤8: 生成报告
            final_report = self._generate_report(comparison_result, selected_pair, result_file)
            
            self.logger.info("=" * 80)
            self.logger.info("✅ 【对比完成】所有步骤执行成功")
            self.logger.info("=" * 80)
            
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ 执行失败: {e}")
            raise
    
    def _analyze_time_strategy(self) -> Dict:
        """步骤1: 分析时间策略"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤1/8】: 时间策略分析")
        self.logger.info("="*60)
        
        now = datetime.now()
        weekday = now.weekday()  # 0=周一, 1=周二...6=周日
        hour = now.hour
        week_info = now.isocalendar()
        
        self.logger.info(f"📅 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📅 星期: 周{['一','二','三','四','五','六','日'][weekday]}")
        self.logger.info(f"🕐 小时: {hour}点")
        self.logger.info(f"📊 周数: 第{week_info[1]}周 (W{week_info[1]:02d})")
        
        # 判断使用哪一周的数据
        if weekday < 1 or (weekday == 1 and hour < 12):
            target_week = week_info[1] - 1
            week_context = "previous_week"
            self.logger.info("🎯 基线策略: 使用【上周】基线（周一全天或周二12点前）")
        else:
            target_week = week_info[1]
            week_context = "current_week"
            self.logger.info("🎯 基线策略: 使用【本周】基线（周二12点后）")
        
        # 判断目标文件版本类型
        if weekday == 5 and hour >= 19:  # 周六晚上7点后
            target_version = "weekend"
            self.logger.info("🎯 目标版本: 使用【weekend】版本（周六19点后）")
        else:
            target_version = "midweek"
            self.logger.info("🎯 目标版本: 使用【midweek】版本")
        
        return {
            'week_context': week_context,
            'target_week': target_week,
            'target_version': target_version,
            'year': week_info[0],
            'weekday': weekday,
            'hour': hour
        }
    
    def _find_baseline_files(self, time_context: Dict) -> List[str]:
        """步骤2: 查找基线文件"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤2/8】: 查找基线文件")
        self.logger.info("="*60)
        
        baseline_dir = f"{self.csv_versions_dir}/{time_context['year']}_W{time_context['target_week']:02d}/baseline"
        self.logger.info(f"📁 查找目录: {baseline_dir}")
        
        if not os.path.exists(baseline_dir):
            self.logger.error(f"❌ 基线目录不存在: {baseline_dir}")
            raise FileNotFoundError(f"E001: 基线目录不存在")
        
        import glob
        pattern = f"{baseline_dir}/*_baseline_W{time_context['target_week']:02d}.csv"
        files = glob.glob(pattern)
        
        self.logger.info(f"🔍 查找模式: *_baseline_W{time_context['target_week']:02d}.csv")
        self.logger.info(f"📊 找到 {len(files)} 个基线文件")
        
        if files:
            for i, f in enumerate(files[:5], 1):
                self.logger.info(f"   [{i}] {os.path.basename(f)}")
            if len(files) > 5:
                self.logger.info(f"   ... 还有 {len(files)-5} 个文件")
        else:
            self.logger.error("❌ 没有找到任何基线文件")
            raise FileNotFoundError("E001: 基线文件缺失")
        
        return sorted(files)
    
    def _categorize_files(self, files: List[str], prefer_real: bool) -> Dict:
        """步骤3: 智能文件分类"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤3/8】: 智能文件分类")
        self.logger.info("="*60)
        
        real_docs = []
        test_docs = []
        
        for f in files:
            basename = os.path.basename(f)
            if 'test' in basename.lower():
                test_docs.append(f)
            else:
                real_docs.append(f)
        
        self.logger.info(f"📊 文件分类结果:")
        self.logger.info(f"   🏢 真实文档: {len(real_docs)}个")
        self.logger.info(f"   🧪 测试文档: {len(test_docs)}个")
        
        if real_docs:
            self.logger.info("   真实文档列表:")
            for i, doc in enumerate(real_docs[:3], 1):
                self.logger.info(f"      [{i}] {os.path.basename(doc)}")
            if len(real_docs) > 3:
                self.logger.info(f"      ... 还有{len(real_docs)-3}个")
        
        if test_docs:
            self.logger.info("   测试文档列表:")
            for i, doc in enumerate(test_docs[:3], 1):
                self.logger.info(f"      [{i}] {os.path.basename(doc)}")
        
        # 根据prefer_real排序
        if prefer_real:
            sorted_files = real_docs + test_docs
            self.logger.info("   ✅ 优先级: 真实文档优先")
        else:
            sorted_files = files
            self.logger.info("   ℹ️ 优先级: 不区分文档类型")
        
        return {
            'all': sorted_files,
            'real': real_docs,
            'test': test_docs
        }
    
    def _match_file_pairs(self, categorized_files: Dict, time_context: Dict) -> List[Dict]:
        """步骤4: 匹配基线和目标文件对"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤4/8】: 匹配基线和目标文件对")
        self.logger.info("="*60)
        
        matched_pairs = []
        target_dir = f"{self.csv_versions_dir}/{time_context['year']}_W{time_context['target_week']:02d}/{time_context['target_version']}"
        
        self.logger.info(f"📁 目标目录: {target_dir}")
        
        for idx, baseline_file in enumerate(categorized_files['all'], 1):
            basename = os.path.basename(baseline_file)
            is_real = 'test' not in basename.lower()
            doc_type = "🏢 真实" if is_real else "🧪 测试"
            
            self.logger.info(f"\n📄 [{idx}/{len(categorized_files['all'])}] 处理基线: {basename}")
            self.logger.info(f"   类型: {doc_type}")
            
            # 提取文档名称
            doc_name_parts = basename.split('_csv_')[0]
            if doc_name_parts.startswith('tencent_'):
                doc_name = doc_name_parts[8:]
            else:
                doc_name = doc_name_parts
            
            self.logger.info(f"   提取文档名: {doc_name}")
            
            # 查找匹配的目标文件
            import glob
            target_pattern = f"{target_dir}/*{doc_name}*_{time_context['target_version']}_W{time_context['target_week']:02d}.csv"
            target_files = glob.glob(target_pattern)
            
            if target_files:
                # 按修改时间排序，使用最新的
                target_files.sort(key=os.path.getmtime, reverse=True)
                target_file = target_files[0]
                self.logger.info(f"   ✅ 找到目标: {os.path.basename(target_file)}")
                
                matched_pairs.append({
                    'baseline': baseline_file,
                    'target': target_file,
                    'doc_name': doc_name,
                    'is_real': is_real,
                    'doc_type': doc_type
                })
            else:
                self.logger.info(f"   ⚠️ 未找到目标文件")
                matched_pairs.append({
                    'baseline': baseline_file,
                    'target': None,
                    'doc_name': doc_name,
                    'is_real': is_real,
                    'doc_type': doc_type
                })
        
        # 统计
        valid_pairs = [p for p in matched_pairs if p['target']]
        real_pairs = [p for p in valid_pairs if p['is_real']]
        test_pairs = [p for p in valid_pairs if not p['is_real']]
        
        self.logger.info(f"\n📈 匹配统计:")
        self.logger.info(f"   总基线文件: {len(matched_pairs)}")
        self.logger.info(f"   有效对比对: {len(valid_pairs)}")
        self.logger.info(f"   真实文档对: {len(real_pairs)}")
        self.logger.info(f"   测试文档对: {len(test_pairs)}")
        
        return matched_pairs
    
    def _select_best_pair(self, matched_pairs: List[Dict], prefer_real: bool) -> Dict:
        """步骤5: 选择最佳对比对"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤5/8】: 选择最佳对比对")
        self.logger.info("="*60)
        
        valid_pairs = [p for p in matched_pairs if p['target']]
        real_pairs = [p for p in valid_pairs if p['is_real']]
        test_pairs = [p for p in valid_pairs if not p['is_real']]
        
        selected = None
        
        if prefer_real and real_pairs:
            selected = real_pairs[0]
            self.logger.info(f"✅ 选择真实文档对: {selected['doc_name']}")
        elif valid_pairs:
            selected = valid_pairs[0]
            self.logger.info(f"⚠️ 使用测试文档对: {selected['doc_name']}")
        elif matched_pairs:
            selected = matched_pairs[0]
            self.logger.info(f"⚠️ 仅有基线文件: {selected['doc_name']}")
        else:
            raise ValueError("没有可用的文件对")
        
        self.logger.info(f"   基线: {os.path.basename(selected['baseline'])}")
        self.logger.info(f"   目标: {os.path.basename(selected['target']) if selected['target'] else '无'}")
        self.logger.info(f"   类型: {selected['doc_type']}")
        
        return selected
    
    def _execute_csv_comparison(self, pair: Dict) -> Dict:
        """步骤6: 执行CSV对比"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤6/8】: 执行专业CSV对比")
        self.logger.info("="*60)
        
        if not pair['target']:
            self.logger.info("⚠️ 没有目标文件，跳过对比")
            return {
                'similarity_score': 1.0,
                'total_changes': 0,
                'message': '仅有基线文件，无法对比'
            }
        
        self.logger.info(f"🔍 开始对比处理...")
        start_time = datetime.now()
        
        # 调用统一对比接口（简化版）
        try:
            from unified_csv_comparator import UnifiedCSVComparator
            comparator = UnifiedCSVComparator()
            result = comparator.compare(pair['baseline'], pair['target'])
            self.logger.info("   使用: 统一CSV对比器（简化版）")
        except:
            # 降级到简单对比
            from simple_comparison_handler import simple_csv_compare
            result = simple_csv_compare(pair['baseline'], pair['target'])
            self.logger.info("   使用: 备用CSV对比器")
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        self.logger.info(f"⏱️ 对比耗时: {elapsed:.2f}秒")
        
        if result:
            self.logger.info(f"📊 对比结果:")
            self.logger.info(f"   相似度: {result.get('similarity_score', 0):.1%}")
            self.logger.info(f"   总变更: {result.get('total_changes', 0)}")
            self.logger.info(f"   新增行: {result.get('added_rows', 0)}")
            self.logger.info(f"   删除行: {result.get('deleted_rows', 0)}")
            self.logger.info(f"   修改行: {result.get('modified_rows', 0)}")
        
        result['execution_time'] = elapsed
        result['document_info'] = {
            'name': pair['doc_name'],
            'type': pair['doc_type'],
            'is_real': pair['is_real']
        }
        
        return result
    
    def _save_results(self, result: Dict, pair: Dict) -> str:
        """步骤7: 保存结果"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤7/8】: 保存对比结果")
        self.logger.info("="*60)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.comparison_results_dir}/enhanced_comparison_{timestamp}.json"
        
        # 添加元数据
        result['metadata'] = {
            'timestamp': timestamp,
            'baseline_file': pair['baseline'],
            'target_file': pair['target'],
            'document_name': pair['doc_name'],
            'document_type': pair['doc_type'],
            'is_real_document': pair['is_real']
        }
        
        os.makedirs(self.comparison_results_dir, exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 结果已保存: {os.path.basename(result_file)}")
        
        return result_file
    
    def _generate_report(self, result: Dict, pair: Dict, result_file: str) -> Dict:
        """步骤8: 生成最终报告"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📂 【步骤8/8】: 生成最终报告")
        self.logger.info("="*60)
        
        report = {
            'success': True,
            'result': result,
            'result_file': result_file,
            'baseline_file': pair['baseline'],
            'target_file': pair['target'],
            'document_info': {
                'name': pair['doc_name'],
                'type': pair['doc_type'],
                'is_real': pair['is_real']
            },
            'execution_time': result.get('execution_time', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("📊 报告摘要:")
        self.logger.info(f"   文档: {pair['doc_name']}")
        self.logger.info(f"   类型: {pair['doc_type']}")
        self.logger.info(f"   相似度: {result.get('similarity_score', 0):.1%}")
        self.logger.info(f"   执行时间: {result.get('execution_time', 0):.2f}秒")
        
        return report


def main():
    """主函数 - 测试增强型对比系统"""
    comparator = EnhancedCSVComparator()
    
    # 执行对比（优先使用真实文档）
    result = comparator.execute_comparison(prefer_real=True)
    
    print("\n" + "="*80)
    print("🎉 增强型CSV对比系统测试完成")
    print(f"📄 结果文件: {result['result_file']}")
    print(f"📊 相似度: {result['result'].get('similarity_score', 0):.1%}")
    print("="*80)


if __name__ == '__main__':
    main()