#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级CSV对比和安全评分优化系统 - Stage 3
整合智能列匹配、L2语义分析、风险评分和安全加固
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import csv
import json
import asyncio
import logging

# 引入Claude AI集成模块
try:
    from claude_wrapper_integration import ClaudeWrapperClient, ClaudeWrapperConfig
    CLAUDE_AI_AVAILABLE = True
    print("✅ Claude AI模块已加载")
except ImportError as e:
    CLAUDE_AI_AVAILABLE = False
    print(f"⚠️ Claude AI模块导入失败: {e}")
    print("  将使用基础风险评分算法")
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import hashlib
from cookie_manager import get_cookie_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """安全配置类"""
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_rows: int = 100000
    max_columns: int = 500
    allowed_extensions: List[str] = None
    require_checksum: bool = True
    enable_audit_log: bool = True
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.csv', '.xlsx', '.xls']


@dataclass
class ComparisonResult:
    """对比结果类"""
    success: bool
    total_differences: int
    differences: List[Dict]
    security_score: float
    risk_level: str
    processing_time: float
    file_checksums: Dict[str, str]
    metadata: Dict[str, Any]


class ProductionCSVComparator:
    """
    生产级CSV对比器
    提供安全加固、智能匹配、风险评分
    """
    
    def __init__(self, security_config: SecurityConfig = None):
        """初始化对比器"""
        self.security_config = security_config or SecurityConfig()
        self.cookie_manager = get_cookie_manager()
        
        # 审计日志
        self.audit_log = []
        
        # Claude AI客户端初始化
        if CLAUDE_AI_AVAILABLE:
            self.claude_config = ClaudeWrapperConfig(
                base_url="http://localhost:8081",
                timeout=30,
                max_retries=3
            )
            self.claude_client = None  # 将在需要时异步初始化
            print("🤖 Claude AI集成已准备就绪")
        else:
            self.claude_client = None
            print("📝 使用基础风险评分模式")
        
        # 风险等级配置
        self.risk_levels = {
            'L1': {'score': 1.0, 'name': '绝对不能修改', 'color': 'red'},
            'L2': {'score': 0.6, 'name': '需要语义审核', 'color': 'orange'}, 
            'L3': {'score': 0.2, 'name': '可自由编辑', 'color': 'green'}
        }
        
        # 标准列配置
        self.standard_columns = {
            "序号": "L3",
            "项目类型": "L2", 
            "来源": "L1",
            "任务发起时间": "L1",
            "目标对齐": "L1",
            "关键KR对齐": "L1",
            "具体计划内容": "L2",
            "邓总指导登记": "L2",
            "负责人": "L2",
            "协助人": "L2",
            "监督人": "L2",
            "重要程度": "L1",
            "预计完成时间": "L1",
            "完成进度": "L1",
            "形成计划清单": "L2",
            "复盘时间": "L3",
            "对上汇报": "L3",
            "应用情况": "L3",
            "进度分析总结": "L3"
        }
        
        logger.info("✅ 生产级CSV对比器初始化完成")
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"计算校验和失败: {e}")
            return "unknown"
    
    def _security_validate_file(self, file_path: str) -> Tuple[bool, str]:
        """安全验证文件"""
        try:
            path = Path(file_path)
            
            # 检查文件存在
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            # 检查文件扩展名
            if path.suffix.lower() not in self.security_config.allowed_extensions:
                return False, f"不支持的文件格式: {path.suffix}"
            
            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > self.security_config.max_file_size:
                return False, f"文件过大: {file_size} bytes (最大: {self.security_config.max_file_size})"
            
            # 检查文件名安全性
            if re.search(r'[<>:"|?*]', path.name):
                return False, "文件名包含不安全字符"
            
            return True, "文件验证通过"
            
        except Exception as e:
            return False, f"文件验证异常: {e}"
    
    def _load_csv_secure(self, file_path: str) -> Tuple[List[List[str]], Dict]:
        """安全加载CSV文件"""
        try:
            # 安全验证
            valid, message = self._security_validate_file(file_path)
            if not valid:
                raise ValueError(message)
            
            # 尝试不同编码
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin1']
            data = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        reader = csv.reader(f)
                        data = list(reader)
                        used_encoding = encoding
                        break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if data is None:
                raise ValueError("无法使用任何编码读取文件")
            
            # 安全检查
            if len(data) > self.security_config.max_rows:
                raise ValueError(f"文件行数过多: {len(data)} (最大: {self.security_config.max_rows})")
            
            if data and len(data[0]) > self.security_config.max_columns:
                raise ValueError(f"文件列数过多: {len(data[0])} (最大: {self.security_config.max_columns})")
            
            metadata = {
                'encoding': used_encoding,
                'rows': len(data),
                'columns': len(data[0]) if data else 0,
                'file_size': os.path.getsize(file_path),
                'checksum': self._calculate_file_checksum(file_path) if self.security_config.require_checksum else None
            }
            
            return data, metadata
            
        except Exception as e:
            logger.error(f"安全加载CSV失败: {e}")
            raise
    
    def _intelligent_column_mapping(self, columns1: List[str], columns2: List[str]) -> Dict[str, Dict]:
        """智能列名映射"""
        try:
            mapping = {}
            confidence_scores = {}
            
            for col1 in columns1:
                if not col1.strip():
                    continue
                
                # 精确匹配
                if col1 in columns2:
                    mapping[col1] = col1
                    confidence_scores[col1] = 1.0
                    continue
                
                # 模糊匹配
                best_match = None
                best_score = 0.0
                
                for col2 in columns2:
                    if not col2.strip():
                        continue
                    
                    # 相似度计算（简化版）
                    similarity = self._calculate_column_similarity(col1, col2)
                    if similarity > best_score and similarity > 0.6:
                        best_match = col2
                        best_score = similarity
                
                if best_match:
                    mapping[col1] = best_match
                    confidence_scores[col1] = best_score
                else:
                    # 检查标准列名
                    standard_match = self._find_standard_column_match(col1)
                    if standard_match:
                        mapping[col1] = standard_match
                        confidence_scores[col1] = 0.8
            
            return {
                'mapping': mapping,
                'confidence_scores': confidence_scores,
                'mapping_rate': len(mapping) / max(len(columns1), 1) * 100
            }
            
        except Exception as e:
            logger.error(f"智能列映射失败: {e}")
            return {'mapping': {}, 'confidence_scores': {}, 'mapping_rate': 0.0}
    
    def _calculate_column_similarity(self, col1: str, col2: str) -> float:
        """计算列名相似度"""
        try:
            # 清理和标准化
            c1 = re.sub(r'[^\w\u4e00-\u9fff]', '', col1.lower().strip())
            c2 = re.sub(r'[^\w\u4e00-\u9fff]', '', col2.lower().strip())
            
            if c1 == c2:
                return 1.0
            
            # 包含关系
            if c1 in c2 or c2 in c1:
                return 0.8
            
            # 编辑距离相似度（简化版）
            max_len = max(len(c1), len(c2))
            if max_len == 0:
                return 0.0
            
            # 简单的字符重叠率
            common_chars = set(c1) & set(c2)
            similarity = len(common_chars) / max_len
            
            return min(similarity, 0.7)  # 最高0.7，为精确匹配保留空间
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def _find_standard_column_match(self, column_name: str) -> Optional[str]:
        """查找标准列名匹配"""
        try:
            clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '', column_name.strip())
            
            for standard_col in self.standard_columns.keys():
                clean_standard = re.sub(r'[^\w\u4e00-\u9fff]', '', standard_col)
                if clean_name in clean_standard or clean_standard in clean_name:
                    return standard_col
            
            return None
            
        except Exception as e:
            logger.error(f"标准列匹配失败: {e}")
            return None
    
    def _enhanced_risk_scoring(self, differences: List[Dict], column_mapping: Dict) -> Dict:
        """增强风险评分"""
        try:
            risk_scores = []
            risk_distribution = {'L1': 0, 'L2': 0, 'L3': 0}
            security_violations = []
            
            for diff in differences:
                column_name = diff.get('列名', '')
                original_value = str(diff.get('原值', '')).strip()
                new_value = str(diff.get('新值', '')).strip()
                
                # 获取风险等级
                risk_level = self.standard_columns.get(column_name, 'L3')
                base_score = self.risk_levels[risk_level]['score']
                
                # 安全增强评分
                security_multiplier = 1.0
                
                # 检查敏感内容变更
                if self._contains_sensitive_info(original_value) or self._contains_sensitive_info(new_value):
                    security_multiplier *= 1.5
                    security_violations.append(f"敏感信息变更: {column_name}")
                
                # 检查大量文本变更
                text_change_ratio = self._calculate_text_change_ratio(original_value, new_value)
                if text_change_ratio > 0.5:
                    security_multiplier *= 1.2
                
                # 检查关键字段空值
                if not new_value and column_name in ['负责人', '监督人', '重要程度']:
                    security_multiplier *= 1.8
                    security_violations.append(f"关键字段空值: {column_name}")
                
                # 计算最终评分
                final_score = min(base_score * security_multiplier, 1.0)
                risk_scores.append(final_score)
                risk_distribution[risk_level] += 1
                
                # 更新差异记录
                diff.update({
                    'risk_level': risk_level,
                    'risk_score': round(final_score, 3),
                    'security_multiplier': round(security_multiplier, 2),
                    'text_change_ratio': round(text_change_ratio, 2)
                })
            
            # 计算综合安全评分
            if risk_scores:
                avg_risk_score = sum(risk_scores) / len(risk_scores)
                max_risk_score = max(risk_scores)
            else:
                avg_risk_score = 0.0
                max_risk_score = 0.0
            
            # 综合安全评分（0-100分）
            security_score = max(0, 100 - (avg_risk_score * 60 + max_risk_score * 40))
            
            return {
                'security_score': round(security_score, 2),
                'average_risk_score': round(avg_risk_score, 3),
                'max_risk_score': round(max_risk_score, 3),
                'risk_distribution': risk_distribution,
                'security_violations': security_violations,
                'total_risks': len(risk_scores)
            }
            
        except Exception as e:
            logger.error(f"风险评分失败: {e}")
            return {
                'security_score': 0.0,
                'average_risk_score': 1.0,
                'max_risk_score': 1.0,
                'risk_distribution': {'L1': 0, 'L2': 0, 'L3': 0},
                'security_violations': [f"评分计算失败: {str(e)}"],
                'total_risks': 0
            }
    
    async def _ai_enhanced_risk_scoring(self, differences: List[Dict], column_mapping: Dict) -> Dict:
        """AI增强风险评分 - 集成Claude语义分析"""
        try:
            # 首先执行基础风险评分
            base_analysis = self._enhanced_risk_scoring(differences, column_mapping)
            
            # 如果Claude AI不可用，返回基础分析
            if not CLAUDE_AI_AVAILABLE or not differences:
                return base_analysis
            
            # 准备AI分析数据
            ai_analysis_data = []
            for diff in differences[:10]:  # 限制前10个差异进行AI分析
                ai_analysis_data.append({
                    '列名': diff.get('列名', ''),
                    '原值': str(diff.get('原值', ''))[:100],  # 限制长度
                    '新值': str(diff.get('新值', ''))[:100],
                    '位置': diff.get('位置', ''),
                    '基础风险等级': diff.get('risk_level', 'L3')
                })
            
            # 调用Claude进行语义分析
            ai_insights = await self._get_claude_semantic_analysis(ai_analysis_data)
            
            # 融合AI分析结果
            if ai_insights:
                # 更新安全评分（AI建议权重：30%）
                ai_security_score = ai_insights.get('ai_security_score', base_analysis['security_score'])
                base_analysis['security_score'] = round(
                    base_analysis['security_score'] * 0.7 + ai_security_score * 0.3, 2
                )
                
                # 添加AI分析标记
                base_analysis['ai_analysis'] = {
                    'enabled': True,
                    'analyzed_count': len(ai_analysis_data),
                    'ai_insights': ai_insights.get('insights', []),
                    'recommendation': ai_insights.get('recommendation', ''),
                    'confidence': ai_insights.get('confidence', 0.0)
                }
                
                logger.info(f"🤖 AI分析完成: {len(ai_analysis_data)}个变更, 置信度: {ai_insights.get('confidence', 0):.2f}")
            else:
                # AI分析失败，使用基础分析
                base_analysis['ai_analysis'] = {
                    'enabled': False,
                    'error': 'AI分析调用失败',
                    'fallback_to_basic': True
                }
            
            return base_analysis
            
        except Exception as e:
            logger.error(f"AI增强风险评分失败: {e}")
            # 失败时回退到基础评分
            basic_result = self._enhanced_risk_scoring(differences, column_mapping)
            basic_result['ai_analysis'] = {
                'enabled': False,
                'error': str(e),
                'fallback_to_basic': True
            }
            return basic_result
    
    async def _get_claude_semantic_analysis(self, differences_data: List[Dict]) -> Optional[Dict]:
        """调用Claude进行语义分析"""
        try:
            # 初始化Claude客户端
            if not self.claude_client and CLAUDE_AI_AVAILABLE:
                self.claude_client = ClaudeWrapperClient(self.claude_config)
            
            if not self.claude_client:
                return None
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下{len(differences_data)}个数据变更，评估其业务风险和合理性：

{json.dumps(differences_data, ensure_ascii=False, indent=2)}

请提供：
1. 整体安全评分(0-100)
2. 主要风险点和建议
3. 置信度评估(0-1)
4. 是否存在异常变更

响应格式：JSON
"""
            
            async with self.claude_client as client:
                # 调用Claude分析API
                response = await client.analyze_risk(
                    content=analysis_prompt,
                    context={
                        "analysis_type": "csv_differences",
                        "difference_count": len(differences_data)
                    }
                )
                
                if response and not response.get('error'):
                    # 处理analyze_risk API的响应格式
                    ai_result = response.get('result', '')
                    confidence = float(response.get('confidence', 0.8))
                    risk_level = response.get('risk_level', 'L3')
                    
                    # 尝试解析结构化响应
                    try:
                        if isinstance(ai_result, str) and ai_result.startswith('{'):
                            parsed_result = json.loads(ai_result)
                            security_score = float(parsed_result.get('security_score', 80))
                            insights = parsed_result.get('insights', [])
                            recommendation = parsed_result.get('recommendation', ai_result[:200])
                        else:
                            # 处理文本响应
                            security_score = 85.0 if risk_level == 'L3' else 65.0 if risk_level == 'L2' else 40.0
                            insights = [ai_result[:100]] if ai_result else []
                            recommendation = ai_result if ai_result else '无特殊建议'
                        
                        return {
                            'ai_security_score': security_score,
                            'insights': insights,
                            'recommendation': recommendation,
                            'confidence': confidence,
                            'risk_level': risk_level,
                            'anomaly_detected': risk_level in ['L1', 'L2']
                        }
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.info(f"使用简化AI响应处理: {e}")
                        # 回退到简化处理
                        security_score = 85.0 if risk_level == 'L3' else 65.0 if risk_level == 'L2' else 40.0
                        return {
                            'ai_security_score': security_score,
                            'insights': [str(ai_result)[:100]] if ai_result else [],
                            'recommendation': str(ai_result)[:200] if ai_result else '无特殊建议',
                            'confidence': confidence,
                            'risk_level': risk_level,
                            'anomaly_detected': risk_level in ['L1', 'L2']
                        }
                        
                else:
                    logger.warning(f"Claude API调用失败: {response.get('error', 'Unknown error')}")
                    return None
                    
        except Exception as e:
            logger.error(f"Claude语义分析调用失败: {e}")
            return None
    
    def _contains_sensitive_info(self, text: str) -> bool:
        """检测敏感信息"""
        try:
            if not text:
                return False
            
            # 敏感信息模式
            sensitive_patterns = [
                r'\b\d{11,18}\b',  # 可能的身份证号
                r'\b1[3-9]\d{9}\b',  # 手机号
                r'\b\d{3,4}-?\d{8}\b',  # 电话号码
                r'[\w\.-]+@[\w\.-]+\.\w+',  # 邮箱
                r'\b[密码|password|pwd]\s*[:：=]\s*\S+',  # 密码
                r'\b\d{6,20}\s*[元|块|万|千]\b'  # 金额
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"敏感信息检测失败: {e}")
            return False
    
    def _calculate_text_change_ratio(self, text1: str, text2: str) -> float:
        """计算文本变化比率"""
        try:
            if not text1 and not text2:
                return 0.0
            if not text1 or not text2:
                return 1.0
            
            # 简单的字符差异比率
            len1, len2 = len(text1), len(text2)
            max_len = max(len1, len2)
            min_len = min(len1, len2)
            
            if max_len == 0:
                return 0.0
            
            # 长度变化比率
            length_ratio = abs(len1 - len2) / max_len
            
            # 内容相似性（简化）
            common_chars = len(set(text1.lower()) & set(text2.lower()))
            total_chars = len(set(text1.lower()) | set(text2.lower()))
            content_similarity = common_chars / max(total_chars, 1)
            
            # 综合变化比率
            change_ratio = (length_ratio + (1 - content_similarity)) / 2
            
            return min(change_ratio, 1.0)
            
        except Exception as e:
            logger.error(f"文本变化比率计算失败: {e}")
            return 0.5
    
    def _audit_log_operation(self, operation: str, details: Dict):
        """记录审计日志"""
        try:
            if self.security_config.enable_audit_log:
                audit_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation,
                    'details': details,
                    'user': 'system',  # 可以集成用户认证
                    'session_id': f"csv_comp_{int(datetime.now().timestamp())}"
                }
                self.audit_log.append(audit_entry)
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")
    
    async def compare_csv_files(self, file1_path: str, file2_path: str, 
                               output_file: str = None) -> ComparisonResult:
        """
        生产级CSV文件对比
        
        Args:
            file1_path: 基准文件路径
            file2_path: 当前文件路径 
            output_file: 输出文件路径
            
        Returns:
            ComparisonResult: 对比结果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 开始生产级CSV对比: {Path(file1_path).name} vs {Path(file2_path).name}")
            
            # 审计日志
            self._audit_log_operation("csv_comparison_start", {
                'file1': file1_path,
                'file2': file2_path,
                'output': output_file
            })
            
            # 安全加载文件
            data1, meta1 = self._load_csv_secure(file1_path)
            data2, meta2 = self._load_csv_secure(file2_path)
            
            # 预处理数据（处理多行标题等）
            processed_data1 = self._preprocess_csv_data(data1)
            processed_data2 = self._preprocess_csv_data(data2)
            
            if not processed_data1 or not processed_data2:
                raise ValueError("处理后的数据为空")
            
            # 获取列名
            columns1 = processed_data1[0]
            columns2 = processed_data2[0]
            
            # 智能列映射
            column_mapping = self._intelligent_column_mapping(columns1, columns2)
            
            # 执行对比
            differences = await self._perform_detailed_comparison(
                processed_data1, processed_data2, column_mapping
            )
            
            # AI增强风险评分
            risk_analysis = await self._ai_enhanced_risk_scoring(differences, column_mapping)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 确定整体风险等级
            if risk_analysis['max_risk_score'] >= 0.8:
                risk_level = "L1 - 高风险"
            elif risk_analysis['average_risk_score'] >= 0.4:
                risk_level = "L2 - 中风险"
            else:
                risk_level = "L3 - 低风险"
            
            # 构建结果
            result = ComparisonResult(
                success=True,
                total_differences=len(differences),
                differences=differences,
                security_score=risk_analysis['security_score'],
                risk_level=risk_level,
                processing_time=processing_time,
                file_checksums={
                    'file1': meta1.get('checksum', 'unknown'),
                    'file2': meta2.get('checksum', 'unknown')
                },
                metadata={
                    'file1_info': meta1,
                    'file2_info': meta2,
                    'column_mapping': column_mapping,
                    'risk_analysis': risk_analysis,
                    'audit_log_entries': len(self.audit_log)
                }
            )
            
            # 保存结果
            if output_file:
                await self._save_comparison_result(result, output_file)
            
            # 审计日志
            self._audit_log_operation("csv_comparison_complete", {
                'total_differences': result.total_differences,
                'security_score': result.security_score,
                'risk_level': result.risk_level,
                'processing_time': result.processing_time
            })
            
            logger.info(f"✅ CSV对比完成: {result.total_differences}个差异, 安全评分: {result.security_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ CSV对比失败: {e}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 审计日志
            self._audit_log_operation("csv_comparison_error", {
                'error': str(e),
                'processing_time': processing_time
            })
            
            return ComparisonResult(
                success=False,
                total_differences=0,
                differences=[],
                security_score=0.0,
                risk_level="错误",
                processing_time=processing_time,
                file_checksums={},
                metadata={'error': str(e)}
            )
    
    def _preprocess_csv_data(self, data: List[List[str]]) -> List[List[str]]:
        """预处理CSV数据"""
        try:
            if len(data) < 2:
                return data
            
            # 检查是否有多行标题
            if len(data) >= 3:
                first_row = data[0]
                # 如果第一行只有第一列有内容，可能是标题行
                if first_row[0] and not any(first_row[1:10] if len(first_row) > 10 else first_row[1:]):
                    if len(data) >= 4:
                        header1 = data[1]
                        header2 = data[2]
                        
                        # 合并列名
                        merged_header = []
                        max_cols = max(len(header1), len(header2))
                        for i in range(max_cols):
                            col1 = header1[i] if i < len(header1) else ""
                            col2 = header2[i] if i < len(header2) else ""
                            final_col = col1.strip() if col1.strip() else col2.strip()
                            merged_header.append(final_col)
                        
                        return [merged_header] + data[3:]
            
            return data
            
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return data
    
    async def _perform_detailed_comparison(self, data1: List[List[str]], data2: List[List[str]],
                                          column_mapping: Dict) -> List[Dict]:
        """执行详细对比 - 增强版：对比所有列，不限于标准列"""
        try:
            differences = []

            if not data1 or not data2:
                return differences

            headers1 = data1[0]
            headers2 = data2[0]

            # 🔥 关键改进：对比所有列，不只是映射的列
            # 使用索引对应方式，确保所有列都被对比
            max_cols = max(len(headers1), len(headers2))
            common_columns = []

            for i in range(max_cols):
                if i < len(headers1) and i < len(headers2):
                    # 两个文件都有这一列
                    common_columns.append((i, i,
                                         headers1[i] if headers1[i] else f"列{chr(65+i)}",
                                         headers2[i] if headers2[i] else f"列{chr(65+i)}"))
            
            # 逐行对比
            min_rows = min(len(data1) - 1, len(data2) - 1)
            diff_count = 0
            
            for row_idx in range(min_rows):
                row1 = data1[row_idx + 1]
                row2 = data2[row_idx + 1]
                
                for col1_idx, col2_idx, col1_name, col2_name in common_columns:
                    if col1_idx < len(row1) and col2_idx < len(row2):
                        old_val = str(row1[col1_idx]).strip()
                        new_val = str(row2[col2_idx]).strip()
                        
                        if old_val != new_val:
                            diff_count += 1
                            
                            difference = {
                                "序号": diff_count,
                                "行号": row_idx + 1,
                                "列名": col1_name,
                                "列索引": col1_idx + 1,
                                "原值": old_val,
                                "新值": new_val,
                                "位置": f"行{row_idx+1}列{col1_idx+1}({col1_name})",
                                "映射列名": col2_name if col2_name != col1_name else None,
                                "比较时间": datetime.now().isoformat()
                            }
                            
                            differences.append(difference)
            
            return differences
            
        except Exception as e:
            logger.error(f"详细对比失败: {e}")
            return []
    
    async def _save_comparison_result(self, result: ComparisonResult, output_file: str):
        """保存对比结果"""
        try:
            # 构建输出数据
            output_data = {
                "comparison_summary": {
                    "success": result.success,
                    "total_differences": result.total_differences,
                    "security_score": result.security_score,
                    "risk_level": result.risk_level,
                    "processing_time": result.processing_time,
                    "comparison_time": datetime.now().isoformat()
                },
                "file_info": {
                    "file_checksums": result.file_checksums,
                    "metadata": result.metadata
                },
                "differences": result.differences,
                "audit_log": self.audit_log if self.security_config.enable_audit_log else []
            }
            
            # 保存到文件
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 对比结果已保存: {output_file}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def get_security_report(self) -> Dict:
        """获取安全报告"""
        try:
            return {
                'security_config': {
                    'max_file_size': f"{self.security_config.max_file_size / 1024 / 1024:.1f}MB",
                    'max_rows': self.security_config.max_rows,
                    'max_columns': self.security_config.max_columns,
                    'allowed_extensions': self.security_config.allowed_extensions,
                    'security_features': ['checksum_validation', 'audit_logging', 'sensitive_content_detection']
                },
                'audit_log_entries': len(self.audit_log),
                'risk_levels_config': self.risk_levels,
                'standard_columns_count': len(self.standard_columns),
                'system_status': 'operational'
            }
        except Exception as e:
            logger.error(f"获取安全报告失败: {e}")
            return {'error': str(e)}


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生产级CSV对比和安全评分系统')
    parser.add_argument('file1', nargs='?', help='基准CSV文件')
    parser.add_argument('file2', nargs='?', help='当前CSV文件')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--security-report', action='store_true', help='显示安全报告')
    
    args = parser.parse_args()
    
    # 创建对比器
    comparator = ProductionCSVComparator()
    
    try:
        if args.security_report or (not args.file1 and not args.file2):
            print("🛡️ 安全配置报告:")
            report = comparator.get_security_report()
            for key, value in report.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for k, v in value.items():
                        print(f"     {k}: {v}")
                else:
                    print(f"   {key}: {value}")
            print()
        
        if args.file1 and args.file2:
            print(f"🔍 开始生产级CSV对比:")
            print(f"   基准文件: {Path(args.file1).name}")
            print(f"   当前文件: {Path(args.file2).name}")
            
            result = await comparator.compare_csv_files(args.file1, args.file2, args.output)
            
            if result.success:
                print(f"\n✅ 对比完成!")
                print(f"   总差异数: {result.total_differences}")
                print(f"   安全评分: {result.security_score:.1f}/100")
                print(f"   风险等级: {result.risk_level}")
                print(f"   处理时间: {result.processing_time:.2f}秒")
                
                if result.metadata.get('risk_analysis', {}).get('security_violations'):
                    print(f"   安全警告: {len(result.metadata['risk_analysis']['security_violations'])}项")
                    for violation in result.metadata['risk_analysis']['security_violations'][:3]:
                        print(f"     • {violation}")
                
                if args.output:
                    print(f"   结果文件: {args.output}")
            else:
                print(f"\n❌ 对比失败: {result.metadata.get('error')}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())