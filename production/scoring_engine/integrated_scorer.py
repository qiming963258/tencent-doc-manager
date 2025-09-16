#!/usr/bin/env python3
"""
综合集成打分引擎 - 详细打分模块
实现L1/L2/L3差异化打分策略
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib
import time

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入L2语义分析模块
from core_modules.l2_semantic_analysis_two_layer import L2SemanticAnalyzer
# 导入路径管理器
from core_modules.path_manager import path_manager
from core_modules.deepseek_client import get_deepseek_client

# L1/L2/L3列定义
L1_COLUMNS = [
    "来源",
    "任务发起时间", 
    "目标对齐",
    "关键KR对齐",
    "重要程度",
    "预计完成时间",
    "完成进度"
]

L2_COLUMNS = [
    "项目类型",
    "具体计划内容",
    "邓总指导登记（日更新）",
    "负责人",
    "协助人",
    "监督人",
    "形成计划清单"
]

L3_COLUMNS = [
    "序号",
    "复盘时间",
    "对上汇报",
    "应用情况",
    "进度分析总结"
]

# 列权重配置
COLUMN_WEIGHTS = {
    "重要程度": 1.4,
    "任务发起时间": 1.3,
    "负责人": 1.2,
    "预计完成时间": 1.2,
    "邓总指导登记（日更新）": 1.15,
    "完成进度": 1.1
}

# AI决策到调整系数的映射
AI_DECISION_FACTORS = {
    'APPROVE': 0.6,
    'CONDITIONAL': 0.8,
    'REVIEW': 1.2,
    'REJECT': 1.5,
    'UNSURE': 1.0
}


class IntegratedScorer:
    """综合打分引擎"""
    
    def __init__(self, use_ai=True, cache_enabled=True):
        """
        初始化打分引擎
        
        Args:
            use_ai: 是否使用AI分析（L2列）
            cache_enabled: 是否启用缓存
        """
        self.use_ai = use_ai
        self.cache_enabled = cache_enabled
        self.cache = {} if cache_enabled else None
        self.l2_analyzer = None
        
        if self.use_ai:
            # 初始化L2分析器（使用真实API）
            try:
                # 获取DeepSeek客户端
                deepseek_client = get_deepseek_client()
                self.l2_analyzer = L2SemanticAnalyzer(api_client=deepseek_client)
                print("L2语义分析器初始化成功（真实API模式）")
            except Exception as e:
                # 不允许降级，L2必须使用AI
                raise Exception(f"L2语义分析器初始化失败，无法继续: {e}")
    
    def get_column_level(self, column_name: str) -> str:
        """获取列的风险等级"""
        if column_name in L1_COLUMNS:
            return "L1"
        elif column_name in L2_COLUMNS:
            return "L2"
        elif column_name in L3_COLUMNS:
            return "L3"
        else:
            # 未分类的列默认为L3
            return "L3"
    
    def get_base_score(self, column_level: str) -> float:
        """获取基础风险分
        
        注意：L1和L2的实际最低分数在process_l1_modification和
        process_l2_modification中有特殊保障机制
        """
        scores = {
            "L1": 0.8,  # L1任何变更最低0.8（红色警告）
            "L2": 0.5,  # L2任何变更最低0.6（橙色警告）
            "L3": 0.2   # L3保持原有逻辑
        }
        return scores.get(column_level, 0.2)
    
    def calculate_change_factor(self, old_value: str, new_value: str) -> float:
        """
        计算变更系数
        
        Returns:
            0.0-1.3之间的系数
        """
        # 处理空值
        old_value = str(old_value).strip() if old_value else ""
        new_value = str(new_value).strip() if new_value else ""
        
        # 无变化
        if old_value == new_value:
            return 0.0
        
        # 从空到有
        if not old_value and new_value:
            return 1.0
        
        # 从有到空（风险更高）
        if old_value and not new_value:
            return 1.3
        
        # 计算文本相似度（简化版）
        if len(old_value) < 10 and len(new_value) < 10:
            # 短文本完全不同
            return 1.0
        else:
            # 长文本，根据长度变化估算
            len_change = abs(len(new_value) - len(old_value)) / max(len(old_value), 1)
            if len_change > 0.5:
                return 1.1  # 大幅变化
            elif len_change > 0.2:
                return 0.8  # 中等变化
            else:
                return 0.5  # 小幅变化
    
    def get_column_weight(self, column_name: str) -> float:
        """获取列的重要性权重"""
        return COLUMN_WEIGHTS.get(column_name, 1.0)
    
    def apply_confidence_weight(self, score: float, confidence: int) -> float:
        """根据AI置信度调整分数"""
        if confidence >= 90:
            return score
        elif confidence >= 70:
            return score * 0.9 + 0.1
        elif confidence >= 50:
            return score * 0.7 + 0.15
        else:
            return 0.5  # 低置信度使用中间值
    
    def process_l1_modification(self, mod: Dict) -> Dict:
        """处理L1列修改（纯规则）"""
        base_score = 0.8
        change_factor = self.calculate_change_factor(
            mod.get('old_value', ''),
            mod.get('new_value', '')
        )
        importance_weight = self.get_column_weight(mod['column_name'])
        
        # L1不使用AI
        ai_adjustment = 1.0
        confidence_weight = 1.0
        
        # L1列特殊处理：确保任何变更都触发红色警告
        # 如果有变更（change_factor > 0），最低分数为0.8
        if change_factor > 0:
            # 基础分0.8，确保始终>=0.8以触发红色警告
            final_score = max(0.8, min(base_score * change_factor * importance_weight, 1.0))
        else:
            # 无变更时分数为0
            final_score = 0.0
        
        return {
            'base_score': base_score,
            'change_factor': change_factor,
            'importance_weight': importance_weight,
            'ai_adjustment': ai_adjustment,
            'confidence_weight': confidence_weight,
            'final_score': final_score,
            'ai_used': False,
            'ai_reason': 'L1_column_rule_based'
        }
    
    def process_l2_modification(self, mod: Dict) -> Dict:
        """
        处理L2列修改（AI+规则混合）
        
        重要：不允许降级，L2必须使用AI分析
        """
        base_score = 0.5
        change_factor = self.calculate_change_factor(
            mod.get('old_value', ''),
            mod.get('new_value', '')
        )
        importance_weight = self.get_column_weight(mod['column_name'])
        
        # L2必须使用AI分析，不允许降级
        if not self.use_ai or not self.l2_analyzer:
            raise Exception("L2列必须使用AI分析，但AI服务未初始化")
        
        # 调用L2分析器（必须成功）
        try:
            analysis_result = self.l2_analyzer.analyze_single_modification(mod)
        except Exception as e:
            # 不允许降级，必须报错
            raise Exception(f"L2 AI语义分析调用失败: {e}")
        
        if not analysis_result:
            raise Exception("L2 AI分析返回空结果")
        
        # 检查是否有错误
        if analysis_result.get('error'):
            raise Exception(f"L2 AI分析错误: {analysis_result['error']}")
        
        # 提取AI决策
        final_decision = analysis_result.get('final_decision', 'UNSURE')
        
        # 获取置信度
        if analysis_result.get('layer2_result'):
            confidence = analysis_result['layer2_result'].get('confidence', 70)
        elif analysis_result.get('layer1_result'):
            confidence = analysis_result['layer1_result'].get('confidence', 50)
        else:
            confidence = 50
        
        # AI决策映射到调整系数
        ai_adjustment = AI_DECISION_FACTORS.get(final_decision, 1.0)
        
        # 置信度加权
        if confidence >= 90:
            confidence_weight = 1.0
        elif confidence >= 70:
            confidence_weight = 0.9
        elif confidence >= 50:
            confidence_weight = 0.8
        else:
            confidence_weight = 0.7
        
        # 计算最终分数
        # L2列特殊处理：确保任何变更最低橙色警告（>=0.6）
        if change_factor > 0:
            # 有变更时，最低分数为0.6以确保橙色警告
            raw_score = base_score * change_factor * importance_weight * ai_adjustment * confidence_weight
            final_score = max(0.6, min(raw_score, 1.0))
        else:
            # 无变更时分数为0
            final_score = 0.0
        
        return {
            'base_score': base_score,
            'change_factor': change_factor,
            'importance_weight': importance_weight,
            'ai_adjustment': ai_adjustment,
            'confidence_weight': confidence_weight,
            'final_score': final_score,
            'ai_used': True,
            'ai_analysis': analysis_result,
            'ai_decision': final_decision,
            'ai_confidence': confidence,
            'layer1_result': analysis_result.get('layer1_result'),
            'layer2_result': analysis_result.get('layer2_result')
        }
    
    def process_l3_modification(self, mod: Dict) -> Dict:
        """处理L3列修改（纯规则）"""
        base_score = 0.2
        change_factor = self.calculate_change_factor(
            mod.get('old_value', ''),
            mod.get('new_value', '')
        )
        importance_weight = self.get_column_weight(mod['column_name'])
        
        # L3不使用AI
        ai_adjustment = 1.0
        confidence_weight = 1.0
        
        final_score = min(base_score * change_factor * importance_weight, 1.0)
        
        return {
            'base_score': base_score,
            'change_factor': change_factor,
            'importance_weight': importance_weight,
            'ai_adjustment': ai_adjustment,
            'confidence_weight': confidence_weight,
            'final_score': final_score,
            'ai_used': False,
            'ai_reason': 'L3_column_rule_based'
        }
    
    def get_risk_level(self, score: float) -> Tuple[str, str, str]:
        """
        获取风险等级
        
        Returns:
            (risk_level, color, icon)
        """
        if score >= 0.8:
            return ("EXTREME_HIGH", "red", "🔴")
        elif score >= 0.6:
            return ("HIGH", "orange", "🟠")
        elif score >= 0.4:
            return ("MEDIUM", "yellow", "🟡")
        elif score >= 0.2:
            return ("LOW", "green", "🟢")
        else:
            return ("EXTREME_LOW", "blue", "🔵")
    
    def get_action_required(self, risk_level: str) -> Tuple[str, int]:
        """
        获取所需操作和优先级
        
        Returns:
            (action, priority)
        """
        actions = {
            "EXTREME_HIGH": ("immediate_review", 1),
            "HIGH": ("manual_review", 2),
            "MEDIUM": ("periodic_check", 3),
            "LOW": ("log_only", 4),
            "EXTREME_LOW": ("none", 5)
        }
        return actions.get(risk_level, ("none", 5))
    
    def score_modification(self, mod: Dict, mod_id: str) -> Dict:
        """
        对单个修改进行打分
        
        Args:
            mod: 修改数据
            mod_id: 修改ID
            
        Returns:
            完整的打分结果
        """
        # 获取列级别
        column_name = mod.get('column_name', '')
        column_level = self.get_column_level(column_name)
        
        # 根据列级别选择处理方法
        if column_level == "L1":
            scoring_details = self.process_l1_modification(mod)
        elif column_level == "L2":
            scoring_details = self.process_l2_modification(mod)
        else:  # L3
            scoring_details = self.process_l3_modification(mod)
        
        # 获取风险评估
        final_score = scoring_details['final_score']
        risk_level, risk_color, risk_icon = self.get_risk_level(final_score)
        action_required, priority = self.get_action_required(risk_level)
        
        # 构建完整结果
        result = {
            'modification_id': mod_id,
            'cell': mod.get('cell', ''),
            'column_name': column_name,
            'column_level': column_level,
            'old_value': mod.get('old_value', ''),
            'new_value': mod.get('new_value', ''),
            'scoring_details': {
                'base_score': scoring_details['base_score'],
                'change_factor': scoring_details['change_factor'],
                'importance_weight': scoring_details['importance_weight'],
                'ai_adjustment': scoring_details['ai_adjustment'],
                'confidence_weight': scoring_details['confidence_weight'],
                'final_score': final_score
            },
            'ai_analysis': {
                'ai_used': scoring_details.get('ai_used', False)
            },
            'risk_assessment': {
                'risk_level': risk_level,
                'risk_color': risk_color,
                'risk_icon': risk_icon,
                'action_required': action_required,
                'priority': priority
            }
        }
        
        # 添加AI分析详情（如果有）
        if scoring_details.get('ai_used'):
            result['ai_analysis'].update({
                'ai_decision': scoring_details.get('ai_decision'),
                'ai_confidence': scoring_details.get('ai_confidence'),
                'layer1_result': scoring_details.get('ai_analysis', {}).get('layer1_result'),
                'layer2_result': scoring_details.get('ai_analysis', {}).get('layer2_result')
            })
        else:
            result['ai_analysis']['reason'] = scoring_details.get('ai_reason', 'N/A')
        
        return result
    
    def process_file(self, input_file: str, output_dir: str = None) -> str:
        """
        处理简化对比文件，生成详细打分
        
        Args:
            input_file: 输入的简化对比JSON文件路径
            output_dir: 输出目录（可选）
            
        Returns:
            输出文件路径
        """
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取修改列表
        modifications = data.get('modifications', [])
        if not modifications:
            raise ValueError("输入文件中没有找到modifications数据")
        
        # 获取表名
        table_name = data.get('table_name', 
                              os.path.basename(input_file).replace('.json', ''))
        
        # 打分结果
        scores = []
        risk_distribution = defaultdict(int)
        ai_usage = {
            'total_ai_calls': 0,
            'layer1_passes': 0,
            'layer2_analyses': 0
        }
        
        # 处理每个修改
        for i, mod in enumerate(modifications):
            mod_id = f"M{i+1:03d}"
            
            # 数据格式兼容性处理：将'old'/'new'转换为'old_value'/'new_value'
            if 'old' in mod and 'old_value' not in mod:
                mod['old_value'] = mod['old']
            if 'new' in mod and 'new_value' not in mod:
                mod['new_value'] = mod['new']
            
            # 处理'column'到'column_name'的兼容性
            if 'column' in mod and 'column_name' not in mod:
                mod['column_name'] = mod['column']
            
            # 处理'cell'字段 - 如果没有cell，基于row生成一个默认值
            if 'cell' not in mod:
                row = mod.get('row', i+1)
                mod['cell'] = f"A{row}"
            
            # 确保必需字段存在
            if 'old_value' not in mod:
                mod['old_value'] = ''
            if 'new_value' not in mod:
                mod['new_value'] = ''
            if 'column_name' not in mod:
                mod['column_name'] = 'unknown'
            
            # 打分
            score_result = self.score_modification(mod, mod_id)
            scores.append(score_result)
            
            # 统计
            risk_distribution[score_result['risk_assessment']['risk_level']] += 1
            if score_result['ai_analysis']['ai_used']:
                ai_usage['total_ai_calls'] += 1
                if score_result['ai_analysis'].get('layer2_result'):
                    ai_usage['layer2_analyses'] += 1
                else:
                    ai_usage['layer1_passes'] += 1
        
        # 计算汇总
        total_score = sum(s['scoring_details']['final_score'] for s in scores)
        avg_score = total_score / len(scores) if scores else 0
        
        # 构建输出
        output = {
            'metadata': {
                'table_name': table_name,
                'source_file': input_file,
                'scoring_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_modifications': len(modifications),
                'scoring_version': 'v1.0'
            },
            'scores': scores,
            'summary': {
                'total_score': round(total_score, 3),
                'average_score': round(avg_score, 3),
                'risk_distribution': dict(risk_distribution),
                'ai_usage': ai_usage
            }
        }
        
        # 保存结果
        if not output_dir:
            # 使用统一路径管理器获取正确路径
            output_dir = str(path_manager.get_scoring_results_path(detailed=True))
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            output_dir,
            f"detailed_score_{table_name}_{timestamp}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"详细打分完成: {output_file}")
        return output_file


def main():
    """主函数（测试用）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='综合打分引擎 - 详细打分')
    parser.add_argument('--input', required=True, help='输入的简化对比JSON文件')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--no-ai', action='store_true', help='禁用AI分析')
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    
    args = parser.parse_args()
    
    # 创建打分器
    scorer = IntegratedScorer(
        use_ai=not args.no_ai,
        cache_enabled=not args.no_cache
    )
    
    # 处理文件
    try:
        output_file = scorer.process_file(args.input, args.output_dir)
        print(f"成功生成详细打分文件: {output_file}")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()