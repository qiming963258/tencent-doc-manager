#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档智能监控系统全面测试验证脚本
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TencentDocSystemTester:
    def __init__(self, base_url="http://202.140.143.88:8089"):
        self.base_url = base_url
        self.test_results = {
            "十步处理链路": {},
            "API端点测试": {},
            "配置驱动架构": {},
            "数据流完整性": {},
            "集成测试": {},
            "系统基础": {},
            "性能指标": {},
            "发现问题": [],
            "系统评分": 0,
            "改进建议": []
        }
        self.start_time = datetime.now()
        
    def log_result(self, category, test_name, result, details=None):
        """记录测试结果"""
        self.test_results[category][test_name] = {
            "status": result,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        status_icon = "✅" if result == "通过" else "❌" if result == "失败" else "⚠️"
        logger.info(f"{status_icon} {category} - {test_name}: {result}")
        if details:
            logger.info(f"    详情: {details}")
    
    def test_system_accessibility(self):
        """测试系统可访问性"""
        try:
            response = requests.get(f"{self.base_url}/test", timeout=10)
            if response.status_code == 200:
                self.log_result("系统基础", "服务可访问性", "通过", 
                              {"状态码": response.status_code, "响应时间": f"{response.elapsed.total_seconds():.2f}s"})
                return True
            else:
                self.log_result("系统基础", "服务可访问性", "失败", 
                              {"状态码": response.status_code})
                return False
        except Exception as e:
            self.log_result("系统基础", "服务可访问性", "失败", {"错误": str(e)})
            return False
    
    def test_ten_step_pipeline(self):
        """验证十步处理链路的实现状态"""
        logger.info("📋 开始验证十步处理链路...")
        
        # 步骤1-3: CSV数据采集与初步对比
        self._test_csv_data_collection()
        
        # 步骤4: AI列名标准化处理
        self._test_ai_column_standardization()
        
        # 步骤5: 数据清洗与重新打分
        self._test_data_cleaning_scoring()
        
        # 步骤6: 5200+参数UI数据生成
        self._test_ui_parameters_generation()
        
        # 步骤7: 复杂热力图UI显示
        self._test_heatmap_ui_display()
        
        # 步骤8: Excel MCP专业半填充
        self._test_excel_mcp_integration()
        
        # 步骤9: 自动上传腾讯文档
        self._test_tencent_upload()
        
        # 步骤10: UI链接绑定与交互
        self._test_ui_link_binding()
    
    def _test_csv_data_collection(self):
        """测试CSV数据采集与初步对比"""
        try:
            # 检查CSV文件是否存在
            csv_path = Path("/root/projects/tencent-doc-manager/csv_versions/comparison")
            csv_files = list(csv_path.glob("*.csv"))
            
            if len(csv_files) >= 6:  # 至少需要3对文件
                self.log_result("十步处理链路", "步骤1-3: CSV数据采集", "通过", 
                              {"文件数量": len(csv_files), "最新文件": str(csv_files[-1])})
            else:
                self.log_result("十步处理链路", "步骤1-3: CSV数据采集", "部分实现", 
                              {"文件数量": len(csv_files), "需要": "至少6个文件(3对)"})
        except Exception as e:
            self.log_result("十步处理链路", "步骤1-3: CSV数据采集", "失败", {"错误": str(e)})
    
    def _test_ai_column_standardization(self):
        """测试AI列名标准化处理"""
        try:
            response = requests.get(f"{self.base_url}/api/real_csv_data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "column_reorder_info" in data.get("data", {}):
                    self.log_result("十步处理链路", "步骤4: AI列名标准化", "通过", 
                                  {"列重排序": True, "列数": len(data["data"].get("column_names", []))})
                else:
                    self.log_result("十步处理链路", "步骤4: AI列名标准化", "部分实现", 
                                  {"缺少": "column_reorder_info"})
            else:
                self.log_result("十步处理链路", "步骤4: AI列名标准化", "失败", 
                              {"状态码": response.status_code})
        except Exception as e:
            self.log_result("十步处理链路", "步骤4: AI列名标准化", "失败", {"错误": str(e)})
    
    def _test_data_cleaning_scoring(self):
        """测试数据清洗与重新打分"""
        try:
            response = requests.get(f"{self.base_url}/api/real_csv_data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                statistics = data.get("data", {}).get("statistics", {})
                if "risk_distribution" in statistics and "total_changes_detected" in statistics:
                    self.log_result("十步处理链路", "步骤5: 数据清洗打分", "通过", 
                                  {"风险分布": statistics["risk_distribution"], 
                                   "总变更": statistics["total_changes_detected"]})
                else:
                    self.log_result("十步处理链路", "步骤5: 数据清洗打分", "部分实现", 
                                  {"缺少统计信息": True})
            else:
                self.log_result("十步处理链路", "步骤5: 数据清洗打分", "失败", 
                              {"状态码": response.status_code})
        except Exception as e:
            self.log_result("十步处理链路", "步骤5: 数据清洗打分", "失败", {"错误": str(e)})
    
    def _test_ui_parameters_generation(self):
        """测试UI参数生成"""
        try:
            response = requests.get(f"{self.base_url}/api/ui-parameters", timeout=10)
            if response.status_code == 200:
                data = response.json()
                param_count = len(str(data))  # 估算参数量
                if param_count > 5000:  # 大于5KB的参数数据
                    self.log_result("十步处理链路", "步骤6: UI参数生成", "通过", 
                                  {"参数数据大小": f"{param_count} 字符", "超过5K": True})
                else:
                    self.log_result("十步处理链路", "步骤6: UI参数生成", "部分实现", 
                                  {"参数数据大小": f"{param_count} 字符", "不足5K": True})
            else:
                self.log_result("十步处理链路", "步骤6: UI参数生成", "失败", 
                              {"状态码": response.status_code})
        except Exception as e:
            self.log_result("十步处理链路", "步骤6: UI参数生成", "失败", {"错误": str(e)})
    
    def _test_heatmap_ui_display(self):
        """测试热力图UI显示"""
        try:
            response = requests.get(f"{self.base_url}/api/real_csv_data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                matrix_data = data.get("data", {}).get("heatmap_data", [])
                matrix_size = data.get("data", {}).get("matrix_size", {})
                
                if matrix_data and matrix_size:
                    rows = matrix_size.get("rows", 0)
                    cols = matrix_size.get("cols", 0)
                    if rows >= 3 and cols >= 19:  # 支持动态行数的3×19矩阵
                        self.log_result("十步处理链路", "步骤7: 热力图UI显示", "通过", 
                                      {"矩阵规模": f"{rows}×{cols}", "动态行数": True})
                    else:
                        self.log_result("十步处理链路", "步骤7: 热力图UI显示", "部分实现", 
                                      {"矩阵规模": f"{rows}×{cols}", "规模不足": True})
                else:
                    self.log_result("十步处理链路", "步骤7: 热力图UI显示", "失败", 
                                  {"缺少": "热力图数据"})
            else:
                self.log_result("十步处理链路", "步骤7: 热力图UI显示", "失败", 
                              {"状态码": response.status_code})
        except Exception as e:
            self.log_result("十步处理链路", "步骤7: 热力图UI显示", "失败", {"错误": str(e)})
    
    def _test_excel_mcp_integration(self):
        """测试Excel MCP专业半填充"""
        try:
            # 检查Excel文件生成
            uploads_path = Path("/root/projects/tencent-doc-manager/uploads")
            excel_files = list(uploads_path.glob("*.xlsx"))
            
            if excel_files:
                latest_file = sorted(excel_files, key=os.path.getmtime)[-1]
                file_size = latest_file.stat().st_size
                self.log_result("十步处理链路", "步骤8: Excel MCP半填充", "通过", 
                              {"最新文件": latest_file.name, "文件大小": f"{file_size} bytes"})
            else:
                self.log_result("十步处理链路", "步骤8: Excel MCP半填充", "部分实现", 
                              {"问题": "未找到Excel输出文件"})
        except Exception as e:
            self.log_result("十步处理链路", "步骤8: Excel MCP半填充", "失败", {"错误": str(e)})
    
    def _test_tencent_upload(self):
        """测试腾讯文档上传"""
        try:
            # 检查上传记录
            upload_records = Path("/root/projects/tencent-doc-manager/upload_records")
            if upload_records.exists():
                upload_files = list(upload_records.glob("*.json"))
                if upload_files:
                    self.log_result("十步处理链路", "步骤9: 腾讯文档上传", "通过", 
                                  {"上传记录": len(upload_files)})
                else:
                    self.log_result("十步处理链路", "步骤9: 腾讯文档上传", "部分实现", 
                                  {"问题": "无上传记录文件"})
            else:
                self.log_result("十步处理链路", "步骤9: 腾讯文档上传", "部分实现", 
                              {"问题": "上传记录目录不存在"})
        except Exception as e:
            self.log_result("十步处理链路", "步骤9: 腾讯文档上传", "失败", {"错误": str(e)})
    
    def _test_ui_link_binding(self):
        """测试UI链接绑定与交互"""
        try:
            response = requests.get(f"{self.base_url}/api/document-links", timeout=10)
            if response.status_code == 200:
                data = response.json()
                document_links = data.get("document_links", {})
                if len(document_links) >= 3:  # 3个真实文档的链接
                    all_have_urls = all("tencent_link" in doc for doc in document_links.values())
                    if all_have_urls:
                        self.log_result("十步处理链路", "步骤10: UI链接绑定", "通过", 
                                      {"文档链接数": len(document_links), "链接完整": True})
                    else:
                        self.log_result("十步处理链路", "步骤10: UI链接绑定", "部分实现", 
                                      {"问题": "部分链接缺失"})
                else:
                    self.log_result("十步处理链路", "步骤10: UI链接绑定", "部分实现", 
                                  {"文档链接数": len(document_links), "期望": 3})
            else:
                self.log_result("十步处理链路", "步骤10: UI链接绑定", "失败", 
                              {"状态码": response.status_code})
        except Exception as e:
            self.log_result("十步处理链路", "步骤10: UI链接绑定", "失败", {"错误": str(e)})
    
    def test_core_api_endpoints(self):
        """测试核心API端点"""
        logger.info("🔌 开始测试核心API端点...")
        
        endpoints = [
            ("/api/real_csv_data", "GET", "热力图数据API"),
            ("/api/document-links", "GET", "文档链接映射API"),
            ("/api/generate-verification-table", "POST", "核验表生成API"),
            ("/api/ui-parameters", "GET", "UI参数API"),
            ("/api/data", "GET", "通用数据API")
        ]
        
        for endpoint, method, name in endpoints:
            self._test_single_endpoint(endpoint, method, name)
    
    def _test_single_endpoint(self, endpoint, method, name):
        """测试单个API端点"""
        try:
            start_time = time.time()
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            else:  # POST
                response = requests.post(f"{self.base_url}{endpoint}", 
                                       json={"test": "data"}, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    data_size = len(str(data))
                    self.log_result("API端点测试", name, "通过", 
                                  {"响应时间": f"{response_time:.2f}s", 
                                   "数据大小": f"{data_size} 字符",
                                   "状态码": 200})
                except:
                    self.log_result("API端点测试", name, "部分实现", 
                                  {"响应时间": f"{response_time:.2f}s", 
                                   "问题": "非JSON响应"})
            else:
                self.log_result("API端点测试", name, "失败", 
                              {"状态码": response.status_code, 
                               "响应时间": f"{response_time:.2f}s"})
        except Exception as e:
            self.log_result("API端点测试", name, "失败", {"错误": str(e)})
    
    def test_configuration_driven_architecture(self):
        """验证配置驱动架构"""
        logger.info("⚙️ 开始验证配置驱动架构...")
        
        # 检查配置文件
        config_file = "/root/projects/tencent-doc-manager/production/config/real_documents.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                documents = config.get("documents", [])
                
                if len(documents) == 3:
                    all_have_required_fields = all(
                        all(field in doc for field in ["name", "url", "doc_id", "csv_pattern"])
                        for doc in documents
                    )
                    
                    if all_have_required_fields:
                        self.log_result("配置驱动架构", "配置文件完整性", "通过", 
                                      {"文档数量": len(documents), "字段完整": True})
                    else:
                        self.log_result("配置驱动架构", "配置文件完整性", "部分实现", 
                                      {"问题": "部分文档缺少必需字段"})
                else:
                    self.log_result("配置驱动架构", "配置文件完整性", "部分实现", 
                                  {"文档数量": len(documents), "期望": 3})
        except Exception as e:
            self.log_result("配置驱动架构", "配置文件完整性", "失败", {"错误": str(e)})
        
        # 检查动态行数功能
        try:
            response = requests.get(f"{self.base_url}/api/real_csv_data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                tables = data.get("data", {}).get("tables", [])
                if len(tables) >= 3:
                    self.log_result("配置驱动架构", "动态行数功能", "通过", 
                                  {"表格数量": len(tables), "支持动态": True})
                else:
                    self.log_result("配置驱动架构", "动态行数功能", "部分实现", 
                                  {"表格数量": len(tables)})
        except Exception as e:
            self.log_result("配置驱动架构", "动态行数功能", "失败", {"错误": str(e)})
    
    def test_data_flow_integrity(self):
        """测试数据流完整性"""
        logger.info("🔄 开始测试数据流完整性...")
        
        # 测试数据路径追踪
        paths_to_check = [
            ("/root/projects/tencent-doc-manager/csv_versions/comparison/", "CSV对比文件"),
            ("/root/projects/tencent-doc-manager/uploads/", "Excel输出文件"),
            ("/root/projects/tencent-doc-manager/upload_records/", "上传记录"),
            ("/root/projects/tencent-doc-manager/verification_tables/", "核验表文件")
        ]
        
        for path, name in paths_to_check:
            if os.path.exists(path):
                files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                if files:
                    self.log_result("数据流完整性", name, "通过", 
                                  {"路径": path, "文件数": len(files)})
                else:
                    self.log_result("数据流完整性", name, "部分实现", 
                                  {"路径": path, "问题": "目录为空"})
            else:
                self.log_result("数据流完整性", name, "失败", 
                              {"路径": path, "问题": "路径不存在"})
    
    def test_integration(self):
        """执行集成测试"""
        logger.info("🔗 开始执行集成测试...")
        
        # 测试热力图与文档链接同步性
        try:
            heatmap_response = requests.get(f"{self.base_url}/api/real_csv_data", timeout=10)
            links_response = requests.get(f"{self.base_url}/api/document-links", timeout=10)
            
            if heatmap_response.status_code == 200 and links_response.status_code == 200:
                heatmap_data = heatmap_response.json()
                links_data = links_response.json()
                
                heatmap_tables = heatmap_data.get("data", {}).get("tables", [])
                document_links = links_data.get("document_links", {})
                
                # 检查数据一致性
                heatmap_names = {table["name"] for table in heatmap_tables}
                link_names = set(document_links.keys())
                
                if heatmap_names == link_names:
                    self.log_result("集成测试", "热力图与链接同步", "通过", 
                                  {"匹配数量": len(heatmap_names)})
                else:
                    self.log_result("集成测试", "热力图与链接同步", "部分实现", 
                                  {"热力图": len(heatmap_names), "链接": len(link_names)})
            else:
                self.log_result("集成测试", "热力图与链接同步", "失败", 
                              {"热力图状态": heatmap_response.status_code, 
                               "链接状态": links_response.status_code})
        except Exception as e:
            self.log_result("集成测试", "热力图与链接同步", "失败", {"错误": str(e)})
    
    def calculate_system_score(self):
        """计算系统集成性评分"""
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if isinstance(tests, dict) and tests:
                for test_name, result in tests.items():
                    total_tests += 1
                    if result.get("status") == "通过":
                        passed_tests += 1
                    elif result.get("status") == "部分实现":
                        passed_tests += 0.5
        
        if total_tests > 0:
            score = (passed_tests / total_tests) * 10
            self.test_results["系统评分"] = round(score, 1)
        else:
            self.test_results["系统评分"] = 0
    
    def generate_improvement_suggestions(self):
        """生成改进建议"""
        suggestions = []
        
        # 分析失败的测试
        for category, tests in self.test_results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if result.get("status") == "失败":
                        suggestions.append(f"修复 {category} - {test_name}")
                    elif result.get("status") == "部分实现":
                        suggestions.append(f"完善 {category} - {test_name}")
        
        # 通用建议
        if self.test_results["系统评分"] < 8:
            suggestions.extend([
                "加强系统监控和日志记录",
                "实现自动化测试覆盖",
                "优化API响应性能",
                "完善错误处理机制"
            ])
        
        self.test_results["改进建议"] = suggestions
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        logger.info("🚀 开始腾讯文档智能监控系统全面测试...")
        
        # 检查系统基本可用性
        if not self.test_system_accessibility():
            logger.error("❌ 系统不可访问，终止测试")
            return self.test_results
        
        # 执行各项测试
        self.test_ten_step_pipeline()
        self.test_core_api_endpoints()
        self.test_configuration_driven_architecture()
        self.test_data_flow_integrity()
        self.test_integration()
        
        # 计算评分和生成建议
        self.calculate_system_score()
        self.generate_improvement_suggestions()
        
        # 记录测试完成时间
        self.test_results["测试耗时"] = str(datetime.now() - self.start_time)
        
        logger.info(f"✅ 测试完成，系统评分: {self.test_results['系统评分']}/10")
        return self.test_results
    
    def save_report(self, filename=None):
        """保存测试报告"""
        if not filename:
            filename = f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_path = Path("/root/projects/tencent-doc-manager") / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 测试报告已保存至: {report_path}")
        return report_path

if __name__ == "__main__":
    tester = TencentDocSystemTester()
    results = tester.run_comprehensive_test()
    report_path = tester.save_report()
    
    # 打印摘要
    print("\n" + "="*80)
    print("📋 腾讯文档智能监控系统测试报告摘要")
    print("="*80)
    print(f"🎯 系统评分: {results['系统评分']}/10")
    print(f"⏱️ 测试耗时: {results['测试耗时']}")
    print(f"📂 详细报告: {report_path}")
    
    if results['改进建议']:
        print("\n💡 主要改进建议:")
        for i, suggestion in enumerate(results['改进建议'][:5], 1):
            print(f"   {i}. {suggestion}")
    
    print("="*80)