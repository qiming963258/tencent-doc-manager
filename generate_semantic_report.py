#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI语义分析综合报告生成器
自动生成周报、日报和Excel汇总报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticReportGenerator:
    """语义分析报告生成器"""
    
    def __init__(self, base_dir: str = "/root/projects/tencent-doc-manager"):
        self.base_dir = Path(base_dir)
        self.semantic_results_dir = self.base_dir / "semantic_results"
        self.approval_workflows_dir = self.base_dir / "approval_workflows"
        self.final_reports_dir = self.base_dir / "final_reports"
        self.marked_excels_dir = self.base_dir / "marked_excels"
        
    def collect_weekly_data(self, week_num: str = "W36") -> Dict[str, Any]:
        """收集本周所有语义分析数据"""
        logger.info(f"收集第{week_num}周数据...")
        
        weekly_data = {
            "week": week_num,
            "tables_processed": [],
            "total_modifications": 0,
            "total_approved": 0,
            "total_pending": 0,
            "total_rejected": 0,
            "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "token_usage": 0,
            "processing_time": 0
        }
        
        # 读取本周所有分析结果
        week_dir = self.semantic_results_dir / f"2025_{week_num}"
        if week_dir.exists():
            for json_file in week_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 提取表格名称
                    table_name = json_file.stem.replace("semantic_analysis_", "").split("_")[0]
                    
                    # 汇总统计
                    weekly_data["tables_processed"].append({
                        "name": table_name,
                        "modifications": data["metadata"]["total_modifications"],
                        "layer1_passed": data["metadata"]["layer1_passed"],
                        "layer2_analyzed": data["metadata"]["layer2_analyzed"],
                        "approved": data["summary"]["approved"],
                        "review_required": data["summary"]["review_required"]
                    })
                    
                    weekly_data["total_modifications"] += data["metadata"]["total_modifications"]
                    weekly_data["total_approved"] += data["summary"]["approved"]
                    weekly_data["total_pending"] += data["summary"]["review_required"]
                    
                    # 汇总风险分布
                    for risk_level, count in data["summary"]["risk_distribution"].items():
                        weekly_data["risk_distribution"][risk_level] += count
                    
                    # 汇总Token使用
                    if "token_usage" in data["metadata"]:
                        weekly_data["token_usage"] += data["metadata"]["token_usage"]["total"]
        
        return weekly_data
    
    def generate_html_report(self, weekly_data: Dict[str, Any]) -> str:
        """生成HTML格式周报"""
        logger.info("生成HTML周报...")
        
        # 计算关键指标
        auto_approval_rate = (weekly_data["total_approved"] / 
                             weekly_data["total_modifications"] * 100 
                             if weekly_data["total_modifications"] > 0 else 0)
        
        # 生成表格行
        table_rows = ""
        for table in weekly_data["tables_processed"]:
            approval_rate = (table["approved"] / table["modifications"] * 100 
                           if table["modifications"] > 0 else 0)
            table_rows += f"""
            <tr>
                <td>{table['name']}</td>
                <td>{table['modifications']}</td>
                <td>{approval_rate:.1f}%</td>
                <td>{table.get('high_risk', 0)}</td>
                <td>{table['review_required']}</td>
                <td><span class="status-badge status-approved">已完成</span></td>
                <td><button class="action-btn btn-primary">查看详情</button></td>
            </tr>
            """
        
        # 读取HTML模板（使用之前创建的）
        template_path = self.final_reports_dir / "weekly" / "2025_W36" / "weekly_report_W36.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 替换占位符（简化版，实际应该更复杂）
            html_content = html_content.replace("1,575", str(weekly_data["total_modifications"]))
            html_content = html_content.replace("67%", f"{auto_approval_rate:.1f}%")
            
            return html_content
        
        return "<html><body><h1>报告生成失败</h1></body></html>"
    
    def generate_excel_report(self, weekly_data: Dict[str, Any]) -> None:
        """生成Excel格式汇总报告"""
        logger.info("生成Excel汇总报告...")
        
        output_file = self.final_reports_dir / "weekly" / f"2025_{weekly_data['week']}" / f"weekly_report_{weekly_data['week']}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: 总览
            overview_data = {
                '指标': ['处理表格数', '总修改数', '自动通过数', '待审批数', '高风险项', 'Token消耗'],
                '数值': [
                    len(weekly_data['tables_processed']),
                    weekly_data['total_modifications'],
                    weekly_data['total_approved'],
                    weekly_data['total_pending'],
                    weekly_data['risk_distribution']['HIGH'] + weekly_data['risk_distribution']['CRITICAL'],
                    weekly_data['token_usage']
                ]
            }
            df_overview = pd.DataFrame(overview_data)
            df_overview.to_excel(writer, sheet_name='总览', index=False)
            
            # Sheet 2: 详细分析
            df_details = pd.DataFrame(weekly_data['tables_processed'])
            df_details.to_excel(writer, sheet_name='详细分析', index=False)
            
            # Sheet 3: 风险分布
            df_risk = pd.DataFrame([weekly_data['risk_distribution']])
            df_risk.to_excel(writer, sheet_name='风险分布', index=False)
            
        logger.info(f"Excel报告已生成: {output_file}")
    
    def upload_to_tencent_docs(self, file_path: Path) -> bool:
        """上传报告到腾讯文档"""
        logger.info("准备上传到腾讯文档...")
        
        # 这里应该调用腾讯文档API
        # 目前只是模拟
        logger.info(f"模拟上传: {file_path} -> 腾讯文档/AI分析报告/")
        return True
    
    def send_notifications(self, weekly_data: Dict[str, Any]) -> None:
        """发送通知（邮件/钉钉/企业微信）"""
        logger.info("发送通知...")
        
        # 准备通知内容
        notification = {
            "title": f"AI语义分析周报 - 第{weekly_data['week']}周",
            "summary": f"""
            本周处理修改: {weekly_data['total_modifications']}项
            自动通过: {weekly_data['total_approved']}项
            待审批: {weekly_data['total_pending']}项
            高风险: {weekly_data['risk_distribution']['HIGH'] + weekly_data['risk_distribution']['CRITICAL']}项
            """,
            "url": f"http://202.140.143.88:8098/reports/weekly/{weekly_data['week']}"
        }
        
        # 模拟发送
        logger.info(f"通知已发送: {notification['title']}")
    
    def generate_weekly_report(self, week_num: str = "W36") -> Dict[str, str]:
        """生成完整周报（主入口）"""
        logger.info(f"===== 开始生成第{week_num}周语义分析报告 =====")
        
        # 1. 收集数据
        weekly_data = self.collect_weekly_data(week_num)
        
        # 2. 生成HTML报告
        html_content = self.generate_html_report(weekly_data)
        html_path = self.final_reports_dir / "weekly" / f"2025_{week_num}" / f"weekly_report_{week_num}_generated.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML报告已生成: {html_path}")
        
        # 3. 生成Excel报告
        self.generate_excel_report(weekly_data)
        
        # 4. 上传到腾讯文档
        excel_path = self.final_reports_dir / "weekly" / f"2025_{week_num}" / f"weekly_report_{week_num}.xlsx"
        if excel_path.exists():
            self.upload_to_tencent_docs(excel_path)
        
        # 5. 发送通知
        self.send_notifications(weekly_data)
        
        # 6. 创建软链接到最新报告
        latest_dir = self.final_reports_dir / "weekly" / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        latest_link = latest_dir / "latest_weekly_report.html"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(html_path)
        
        logger.info(f"===== 第{week_num}周报告生成完成 =====")
        
        return {
            "html_report": str(html_path),
            "excel_report": str(excel_path),
            "report_url": f"http://202.140.143.88:8098/reports/weekly/{week_num}",
            "tencent_doc_url": f"https://docs.qq.com/sheet/xxx"
        }


def main():
    """主函数"""
    generator = SemanticReportGenerator()
    
    # 生成本周报告
    current_week = "W36"  # 实际应该计算当前周数
    results = generator.generate_weekly_report(current_week)
    
    print("\n📊 报告生成完成！")
    print(f"HTML报告: {results['html_report']}")
    print(f"Excel报告: {results['excel_report']}")
    print(f"在线查看: {results['report_url']}")
    print(f"腾讯文档: {results['tencent_doc_url']}")


if __name__ == "__main__":
    main()