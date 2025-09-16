#!/usr/bin/env python3
"""
DeepSeek Excel 简化版测试脚本
不依赖pandas，使用标准库和requests处理Excel修改
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# 配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
API_BASE_URL = "https://api.siliconflow.cn/v1"

# 目录配置
BASE_DIR = Path('/root/projects/tencent-doc-manager')
DOWNLOAD_DIR = BASE_DIR / 'downloads'
OUTPUT_DIR = BASE_DIR / 'excel_outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

def call_deepseek_api(content: str, prompt: str = None) -> dict:
    """调用DeepSeek V3 API进行分析"""
    
    if not DEEPSEEK_API_KEY:
        print("⚠️ 未设置DEEPSEEK_API_KEY，使用模拟数据")
        return {
            "risk_level": "medium",
            "confidence": 0.85,
            "approval_status": "review",
            "analysis": "模拟分析结果：检测到中等风险的数据变更",
            "recommendations": "建议人工审核后批准"
        }
    
    if not prompt:
        prompt = """分析这个数据的风险等级。返回JSON格式包含：
- risk_level: high/medium/low
- confidence: 0-1的置信度
- approval_status: approve/review/reject
- analysis: 分析说明
- recommendations: 处理建议"""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🤖 调用DeepSeek V3 API...")
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-v3",
                "messages": [
                    {"role": "system", "content": "你是数据分析专家，返回JSON格式的分析结果。"},
                    {"role": "user", "content": f"{prompt}\n\n数据：\n{content[:1000]}"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 尝试解析JSON
            try:
                # 提取JSON部分（如果包含其他文本）
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # 返回默认结构
            return {
                "risk_level": "medium",
                "confidence": 0.7,
                "approval_status": "review",
                "analysis": content,
                "recommendations": "需要人工审核"
            }
        else:
            print(f"❌ API返回错误: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ API调用异常: {e}")
    
    # 返回默认分析
    return {
        "risk_level": "medium",
        "confidence": 0.5,
        "approval_status": "review",
        "analysis": "API调用失败，使用默认分析",
        "recommendations": "建议人工审核"
    }

def process_csv_with_deepseek(input_file: Path) -> Path:
    """处理CSV文件，添加DeepSeek分析结果"""
    
    print(f"\n📄 处理文件: {input_file}")
    
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f"deepseek_analyzed_{timestamp}_{input_file.name}"
    
    try:
        # 读取CSV内容
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ 文件为空")
            return None
        
        # 获取前50行用于分析
        sample_data = "".join(lines[:50])
        
        # 调用DeepSeek分析
        analysis = call_deepseek_api(sample_data)
        
        print(f"📊 分析结果:")
        print(f"  - 风险等级: {analysis['risk_level']}")
        print(f"  - 置信度: {analysis['confidence']:.0%}")
        print(f"  - 审批建议: {analysis['approval_status']}")
        
        # 修改CSV，添加分析结果
        modified_lines = []
        
        # 处理标题行
        if lines:
            header = lines[0].rstrip()
            header += ",风险等级,AI置信度,审批建议\n"
            modified_lines.append(header)
            
            # 处理数据行
            for line in lines[1:]:
                if line.strip():
                    line = line.rstrip()
                    line += f",{analysis['risk_level']},{analysis['confidence']:.0%},{analysis['approval_status']}\n"
                    modified_lines.append(line)
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        
        print(f"✅ 处理完成: {output_file}")
        
        # 创建分析报告
        report_file = OUTPUT_DIR / f"deepseek_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "input_file": str(input_file),
                "output_file": str(output_file),
                "analysis": analysis,
                "api_model": "deepseek-v3",
                "api_provider": "siliconflow"
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📝 分析报告: {report_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return None

def create_test_csv():
    """创建测试CSV文件"""
    test_file = DOWNLOAD_DIR / "test_deepseek.csv"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("产品名称,销售数量,单价,部门\n")
        f.write("产品A,100,50.5,销售部\n")
        f.write("产品B,200,75.8,市场部\n")
        f.write("产品C,150,60.0,技术部\n")
        f.write("产品D,300,45.2,运营部\n")
    
    print(f"✅ 创建测试文件: {test_file}")
    return test_file

def main():
    """主函数"""
    
    print("=" * 60)
    print("🚀 DeepSeek Excel/CSV 智能分析系统")
    print("=" * 60)
    print(f"📁 工作目录: {BASE_DIR}")
    print(f"📥 下载目录: {DOWNLOAD_DIR}")
    print(f"📤 输出目录: {OUTPUT_DIR}")
    print(f"🔑 API密钥: {'已设置' if DEEPSEEK_API_KEY else '未设置(使用模拟模式)'}")
    print("=" * 60)
    
    # 查找CSV文件
    csv_files = list(DOWNLOAD_DIR.glob("*.csv"))
    
    if not csv_files:
        print("\n⚠️ 未找到CSV文件，创建测试文件...")
        test_file = create_test_csv()
        csv_files = [test_file]
    
    # 处理找到的第一个CSV文件
    if csv_files:
        input_file = csv_files[0]
        output_file = process_csv_with_deepseek(input_file)
        
        if output_file:
            print("\n" + "=" * 60)
            print("✅ DeepSeek处理完成！")
            print(f"📊 已将AI分析结果添加到文件中")
            print(f"🎯 可以通过8093端口上传到腾讯文档")
            print("=" * 60)
    else:
        print("❌ 没有找到可处理的文件")

if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if input_file.exists():
            process_csv_with_deepseek(input_file)
        else:
            print(f"❌ 文件不存在: {input_file}")
    else:
        main()