#!/usr/bin/env python3
"""
整合版热力图监控系统 - 8089端口
集成8093完整工作流与热力图可视化
支持多URL串行处理、实时日志显示、热力图生成与URL链接
"""

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import sys
import json
import time
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from queue import Queue
import traceback

# 添加系统路径
sys.path.append('/root/projects/tencent-doc-manager')
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
sys.path.append('/root/projects/tencent-doc-manager/production/servers')

# 导入8093的核心模块
from production.core_modules.tencent_export_automation import TencentDocAutoExporter
from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator  
from production.core_modules.week_time_manager import WeekTimeManager
from production.core_modules.baseline_manager import BaselineManager
from production.core_modules.auto_comparison_task import AutoComparisonTaskHandler
from production.core_modules.deepseek_client import DeepSeekClient
from intelligent_excel_marker import IntelligentExcelMarker

# 导入上传模块
try:
    from tencent_doc_uploader_ultimate import sync_upload_file
    print("✅ 使用 tencent_doc_uploader_ultimate")
except ImportError:
    try:
        from tencent_doc_uploader_fixed import sync_upload_file
        print("✅ 使用 tencent_doc_uploader_fixed")
    except ImportError:
        from tencent_doc_uploader import sync_upload_file
        print("✅ 使用 tencent_doc_uploader")

# 导入热力图映射模块
from production.core_modules.scoring_heatmap_mapper_simple import SimpleScoringHeatmapMapper

app = Flask(__name__)
app.secret_key = 'integrated_heatmap_8089_secret_key'
CORS(app)

# 全局变量
processing_status = {
    "is_running": False,
    "current_step": "",
    "current_url": "",
    "progress": 0,
    "total_urls": 0,
    "logs": [],
    "results": {},
    "uploaded_urls": {},  # 存储表格名称到上传URL的映射
    "comprehensive_score_path": None,  # 综合打分文件路径
    "heatmap_data": None  # 热力图数据
}

# 日志队列
log_queue = Queue()

def add_log(message, level="info"):
    """添加日志消息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message
    }
    processing_status["logs"].append(log_entry)
    log_queue.put(log_entry)
    print(f"[{timestamp}] {message}")

def process_single_url(url, cookie_string, week_time_manager):
    """处理单个URL的完整工作流"""
    try:
        add_log(f"开始处理: {url}")
        
        # 步骤1：下载CSV文件
        add_log("步骤1: 下载CSV文件...")
        exporter = TencentDocAutoExporter(cookie_string)
        csv_content = exporter.export_as_csv_direct(url)
        
        if not csv_content:
            raise Exception("CSV下载失败")
        
        # 获取文档名称
        doc_name = url.split('/')[-1][:20]  # 简化名称
        
        # 步骤2：保存并获取基线
        add_log("步骤2: 获取基线文档...")
        baseline_manager = BaselineManager()
        week_info = week_time_manager.get_current_week_info()
        current_week = week_info["week_number"]
        
        # 保存当前版本
        current_file = baseline_manager.save_current_version(csv_content, doc_name, current_week)
        
        # 获取基线
        baseline_file = baseline_manager.get_baseline_file(doc_name, current_week)
        
        # 步骤3：CSV对比分析
        add_log("步骤3: 执行CSV对比分析...")
        comparator = AdaptiveTableComparator()
        comparison_result = comparator.compare_csv_files(baseline_file, current_file)
        
        # 统计修改数量
        modifications = comparison_result.get("modifications", [])
        mod_count = len(modifications)
        add_log(f"检测到 {mod_count} 处修改")
        
        if mod_count == 0:
            add_log(f"✅ {doc_name} 没有修改，跳过后续处理")
            return {
                "table_name": doc_name,
                "url": url,
                "modifications_count": 0,
                "uploaded_url": None
            }
        
        # 步骤4：AI语义分析
        add_log("步骤4: AI语义分析...")
        deepseek_client = DeepSeekClient()
        
        detailed_scores = []
        for i, mod in enumerate(modifications):
            add_log(f"分析修改 {i+1}/{mod_count}...")
            
            # 获取列级别（简化处理）
            column_level = "L2"  # 默认L2
            if "时间" in mod.get("column_name", "") or "日期" in mod.get("column_name", ""):
                column_level = "L1"
            elif "备注" in mod.get("column_name", "") or "说明" in mod.get("column_name", ""):
                column_level = "L3"
            
            # AI分析（如果是L2）
            if column_level == "L2":
                try:
                    ai_result = deepseek_client.analyze_modification(mod)
                    ai_analysis = {
                        "ai_used": True,
                        "ai_decision": ai_result.get("decision", "REVIEW"),
                        "ai_confidence": ai_result.get("confidence", 50)
                    }
                except:
                    ai_analysis = {"ai_used": False, "reason": "AI分析失败"}
            else:
                ai_analysis = {"ai_used": False, "reason": f"{column_level}_column_rule_based"}
            
            # 计算分数
            base_score = 0.8 if column_level == "L1" else 0.5 if column_level == "L2" else 0.3
            
            detailed_scores.append({
                "modification_id": f"M{i+1:03d}",
                "cell": mod.get("cell", f"R{i}C1"),
                "column_name": mod.get("column_name", "未知列"),
                "column_level": column_level,
                "old_value": mod.get("old_value", ""),
                "new_value": mod.get("new_value", ""),
                "scoring_details": {
                    "base_score": base_score,
                    "final_score": base_score
                },
                "ai_analysis": ai_analysis,
                "risk_assessment": {
                    "risk_level": "HIGH" if column_level == "L1" else "MEDIUM" if column_level == "L2" else "LOW"
                }
            })
        
        # 保存详细打分
        scoring_dir = Path("/root/projects/tencent-doc-manager/scoring_results/detailed")
        scoring_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detail_file = scoring_dir / f"detailed_score_{doc_name}_{timestamp}.json"
        
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "table_name": doc_name,
                    "scoring_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_modifications": mod_count
                },
                "scores": detailed_scores
            }, f, ensure_ascii=False, indent=2)
        
        add_log(f"详细打分已保存: {detail_file}")
        
        # 步骤5：Excel标记
        add_log("步骤5: Excel智能标记...")
        excel_marker = IntelligentExcelMarker()
        
        # 下载Excel格式
        add_log("下载Excel格式文件...")
        excel_content = exporter.export_as_excel_direct(url)
        
        if not excel_content:
            raise Exception("Excel下载失败")
        
        # 保存临时Excel文件
        temp_excel = Path(f"/tmp/{doc_name}_{timestamp}.xlsx")
        with open(temp_excel, 'wb') as f:
            f.write(excel_content)
        
        # 执行标记
        marked_file = excel_marker.mark_excel_with_l1l2l3_colors(
            str(temp_excel),
            str(detail_file)
        )
        
        add_log(f"Excel标记完成: {marked_file}")
        
        # 步骤6：上传到腾讯文档
        add_log("步骤6: 上传到腾讯文档...")
        upload_result = sync_upload_file(
            marked_file,
            upload_option='new',
            target_url='',
            cookie_string=cookie_string
        )
        
        uploaded_url = None
        if upload_result and upload_result.get('success'):
            uploaded_url = upload_result.get('url', '')
            add_log(f"✅ 上传成功: {uploaded_url}")
        else:
            add_log("⚠️ 上传失败，但继续处理", "warning")
        
        # 返回结果
        return {
            "table_name": doc_name,
            "url": url,
            "modifications_count": mod_count,
            "uploaded_url": uploaded_url,
            "detail_file": str(detail_file),
            "risk_summary": {
                "high": sum(1 for s in detailed_scores if s["risk_assessment"]["risk_level"] == "HIGH"),
                "medium": sum(1 for s in detailed_scores if s["risk_assessment"]["risk_level"] == "MEDIUM"),
                "low": sum(1 for s in detailed_scores if s["risk_assessment"]["risk_level"] == "LOW")
            }
        }
        
    except Exception as e:
        add_log(f"❌ 处理失败: {str(e)}", "error")
        return {
            "table_name": url.split('/')[-1][:20],
            "url": url,
            "error": str(e)
        }

def process_urls_serial(urls, cookie_string):
    """串行处理多个URL"""
    global processing_status
    
    try:
        processing_status["is_running"] = True
        processing_status["total_urls"] = len(urls)
        processing_status["results"] = {}
        processing_status["uploaded_urls"] = {}
        
        # 初始化时间管理器
        week_time_manager = WeekTimeManager()
        
        # 存储所有表格的结果
        all_table_scores = []
        
        # 串行处理每个URL
        for i, url in enumerate(urls):
            processing_status["current_url"] = url
            processing_status["progress"] = i
            processing_status["current_step"] = f"处理第 {i+1}/{len(urls)} 个文档"
            
            result = process_single_url(url, cookie_string, week_time_manager)
            
            # 存储结果
            table_name = result["table_name"]
            processing_status["results"][table_name] = result
            
            if result.get("uploaded_url"):
                processing_status["uploaded_urls"][table_name] = result["uploaded_url"]
            
            # 构建综合打分数据
            if result.get("modifications_count", 0) > 0:
                all_table_scores.append({
                    "table_name": table_name,
                    "table_url": url,
                    "modifications_count": result["modifications_count"],
                    "uploaded_url": result.get("uploaded_url"),
                    "table_summary": {
                        "overall_risk_score": 0.5,  # 简化处理
                        "risk_level": "MEDIUM"
                    }
                })
            else:
                all_table_scores.append({
                    "table_name": table_name,
                    "table_url": url,
                    "modifications_count": 0,
                    "uploaded_url": None,
                    "table_summary": {
                        "overall_risk_score": 0.0,
                        "risk_level": "UNMODIFIED"
                    }
                })
        
        # 生成综合打分文件
        add_log("生成综合打分文件...")
        comprehensive_score = {
            "metadata": {
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_tables": len(all_table_scores),
                "total_modifications": sum(t["modifications_count"] for t in all_table_scores)
            },
            "table_scores": all_table_scores
        }
        
        # 保存综合打分
        score_file = Path(f"/tmp/comprehensive_score_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(score_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_score, f, ensure_ascii=False, indent=2)
        
        processing_status["comprehensive_score_path"] = str(score_file)
        add_log(f"综合打分已保存: {score_file}")
        
        # 生成热力图数据
        add_log("生成热力图数据...")
        mapper = SimpleScoringHeatmapMapper()
        heatmap_data = mapper.convert_scoring_to_heatmap(comprehensive_score)
        
        processing_status["heatmap_data"] = heatmap_data
        add_log("✅ 热力图数据生成完成")
        
        processing_status["current_step"] = "处理完成"
        processing_status["progress"] = len(urls)
        add_log(f"🎉 全部处理完成！共处理 {len(urls)} 个文档")
        
    except Exception as e:
        add_log(f"❌ 处理过程出错: {str(e)}", "error")
        traceback.print_exc()
    finally:
        processing_status["is_running"] = False

# API路由

@app.route('/')
def index():
    """主页面 - 整合版UI"""
    html_content = '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档智能监控系统 - 整合版</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; padding: 0; background: #f0f2f5; }
        .log-container {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 10px;
            height: 300px;
            overflow-y: auto;
            border-radius: 4px;
        }
        .log-info { color: #4fc3f7; }
        .log-success { color: #81c784; }
        .log-warning { color: #ffb74d; }
        .log-error { color: #e57373; }
        .heatmap-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .table-row-link {
            cursor: pointer;
            color: #1890ff;
            text-decoration: none;
        }
        .table-row-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        
        function IntegratedHeatmapSystem() {
            const [urls, setUrls] = useState('');
            const [cookie, setCookie] = useState('');
            const [isProcessing, setIsProcessing] = useState(false);
            const [logs, setLogs] = useState([]);
            const [heatmapData, setHeatmapData] = useState(null);
            const [uploadedUrls, setUploadedUrls] = useState({});
            const logEndRef = useRef(null);
            
            // 自动滚动日志到底部
            useEffect(() => {
                logEndRef.current?.scrollIntoView({ behavior: "smooth" });
            }, [logs]);
            
            // 加载保存的Cookie
            useEffect(() => {
                fetch('/api/load-cookie')
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.cookie) {
                            setCookie(data.cookie);
                        }
                    });
            }, []);
            
            // 轮询获取状态
            useEffect(() => {
                if (isProcessing) {
                    const interval = setInterval(() => {
                        fetch('/api/status')
                            .then(res => res.json())
                            .then(data => {
                                setLogs(data.logs || []);
                                setUploadedUrls(data.uploaded_urls || {});
                                
                                if (!data.is_running) {
                                    setIsProcessing(false);
                                    if (data.heatmap_data) {
                                        setHeatmapData(data.heatmap_data);
                                    }
                                }
                            });
                    }, 1000);
                    
                    return () => clearInterval(interval);
                }
            }, [isProcessing]);
            
            const handleSaveCookie = async () => {
                const response = await fetch('/api/save-cookie', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cookie })
                });
                const result = await response.json();
                if (result.success) {
                    alert('Cookie保存成功！');
                }
            };
            
            const handleStartProcessing = async () => {
                const urlList = urls.split('\\n').filter(u => u.trim());
                if (urlList.length === 0) {
                    alert('请输入至少一个URL');
                    return;
                }
                
                if (!cookie) {
                    alert('请输入Cookie');
                    return;
                }
                
                setIsProcessing(true);
                setLogs([]);
                
                const response = await fetch('/api/start-processing', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls: urlList, cookie })
                });
                
                const result = await response.json();
                if (!result.success) {
                    alert('启动失败: ' + result.error);
                    setIsProcessing(false);
                }
            };
            
            const getLogClass = (level) => {
                switch(level) {
                    case 'success': return 'log-success';
                    case 'warning': return 'log-warning';
                    case 'error': return 'log-error';
                    default: return 'log-info';
                }
            };
            
            return (
                <div className="min-h-screen bg-gray-50 p-4">
                    <div className="max-w-7xl mx-auto">
                        <h1 className="text-3xl font-bold text-gray-800 mb-6">
                            腾讯文档智能监控系统 - 整合版
                        </h1>
                        
                        {/* 控制面板 */}
                        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* URL输入 */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        文档URL列表（每行一个）
                                    </label>
                                    <textarea
                                        value={urls}
                                        onChange={(e) => setUrls(e.target.value)}
                                        className="w-full h-32 p-2 border border-gray-300 rounded-md"
                                        placeholder="https://docs.qq.com/sheet/xxx&#10;https://docs.qq.com/sheet/yyy"
                                        disabled={isProcessing}
                                    />
                                </div>
                                
                                {/* Cookie输入 */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Cookie
                                    </label>
                                    <textarea
                                        value={cookie}
                                        onChange={(e) => setCookie(e.target.value)}
                                        className="w-full h-24 p-2 border border-gray-300 rounded-md"
                                        placeholder="输入Cookie字符串..."
                                        disabled={isProcessing}
                                    />
                                    <button
                                        onClick={handleSaveCookie}
                                        className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                                        disabled={isProcessing}
                                    >
                                        保存Cookie
                                    </button>
                                </div>
                            </div>
                            
                            {/* 开始按钮 */}
                            <div className="mt-4">
                                <button
                                    onClick={handleStartProcessing}
                                    disabled={isProcessing}
                                    className={`px-6 py-3 rounded-md text-white font-medium ${
                                        isProcessing 
                                            ? 'bg-gray-400 cursor-not-allowed' 
                                            : 'bg-blue-600 hover:bg-blue-700'
                                    }`}
                                >
                                    {isProcessing ? '处理中...' : '开始处理'}
                                </button>
                            </div>
                        </div>
                        
                        {/* 日志显示 */}
                        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                            <h2 className="text-xl font-semibold mb-4">处理日志</h2>
                            <div className="log-container">
                                {logs.map((log, index) => (
                                    <div key={index} className={getLogClass(log.level)}>
                                        [{log.timestamp}] {log.message}
                                    </div>
                                ))}
                                <div ref={logEndRef} />
                            </div>
                        </div>
                        
                        {/* 热力图显示 */}
                        {heatmapData && (
                            <div className="heatmap-container">
                                <h2 className="text-xl font-semibold mb-4">风险热力图</h2>
                                <HeatmapVisualization 
                                    data={heatmapData}
                                    uploadedUrls={uploadedUrls}
                                />
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        
        // 热力图组件
        function HeatmapVisualization({ data, uploadedUrls }) {
            const canvasRef = useRef(null);
            
            useEffect(() => {
                if (!data || !canvasRef.current) return;
                
                const canvas = canvasRef.current;
                const ctx = canvas.getContext('2d');
                
                const { heatmap_data, table_names, column_names } = data;
                const cellWidth = 40;
                const cellHeight = 30;
                const labelWidth = 150;
                const labelHeight = 30;
                
                canvas.width = labelWidth + column_names.length * cellWidth;
                canvas.height = labelHeight + table_names.length * cellHeight;
                
                // 清空画布
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // 绘制列标题
                ctx.fillStyle = '#333333';
                ctx.font = '12px Arial';
                column_names.forEach((col, i) => {
                    ctx.save();
                    ctx.translate(labelWidth + i * cellWidth + cellWidth/2, labelHeight - 5);
                    ctx.rotate(-Math.PI/4);
                    ctx.fillText(col, 0, 0);
                    ctx.restore();
                });
                
                // 绘制行标题（可点击的链接）
                table_names.forEach((name, i) => {
                    const y = labelHeight + i * cellHeight + cellHeight/2;
                    
                    // 如果有上传的URL，显示为蓝色
                    if (uploadedUrls[name]) {
                        ctx.fillStyle = '#1890ff';
                        ctx.font = 'bold 12px Arial';
                    } else {
                        ctx.fillStyle = '#333333';
                        ctx.font = '12px Arial';
                    }
                    
                    ctx.fillText(name, 10, y);
                });
                
                // 绘制热力图单元格
                heatmap_data.forEach((row, i) => {
                    row.forEach((value, j) => {
                        const x = labelWidth + j * cellWidth;
                        const y = labelHeight + i * cellHeight;
                        
                        // 根据值选择颜色
                        let color;
                        if (value <= 0.05) {
                            color = '#e3f2fd';  // 蓝色 - 无修改
                        } else if (value < 0.3) {
                            color = '#a5d6a7';  // 绿色 - 低风险
                        } else if (value < 0.6) {
                            color = '#fff59d';  // 黄色 - 中风险
                        } else if (value < 0.8) {
                            color = '#ffcc80';  // 橙色 - 高风险
                        } else {
                            color = '#ef5350';  // 红色 - 极高风险
                        }
                        
                        ctx.fillStyle = color;
                        ctx.fillRect(x, y, cellWidth - 1, cellHeight - 1);
                    });
                });
            }, [data, uploadedUrls]);
            
            const handleCanvasClick = (e) => {
                const rect = canvasRef.current.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const labelWidth = 150;
                const labelHeight = 30;
                const cellHeight = 30;
                
                // 检查是否点击在行标题区域
                if (x < labelWidth && y > labelHeight) {
                    const rowIndex = Math.floor((y - labelHeight) / cellHeight);
                    if (rowIndex >= 0 && rowIndex < data.table_names.length) {
                        const tableName = data.table_names[rowIndex];
                        const url = uploadedUrls[tableName];
                        if (url) {
                            window.open(url, '_blank');
                        }
                    }
                }
            };
            
            return (
                <canvas 
                    ref={canvasRef}
                    onClick={handleCanvasClick}
                    style={{ cursor: 'pointer', border: '1px solid #e0e0e0' }}
                />
            );
        }
        
        ReactDOM.render(<IntegratedHeatmapSystem />, document.getElementById('root'));
    </script>
</body>
</html>'''
    return html_content

@app.route('/api/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie"""
    try:
        data = request.json
        cookie_string = data.get('cookie', '')
        
        cookie_file = Path("/root/projects/tencent-doc-manager/config/cookies_8089.json")
        cookie_file.parent.mkdir(exist_ok=True)
        
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump({
                "cookie_string": cookie_string,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/load-cookie', methods=['GET'])
def load_cookie():
    """加载Cookie"""
    try:
        cookie_file = Path("/root/projects/tencent-doc-manager/config/cookies_8089.json")
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({
                    "success": True,
                    "cookie": data.get("cookie_string", "")
                })
        return jsonify({"success": True, "cookie": ""})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/start-processing', methods=['POST'])
def start_processing():
    """开始处理"""
    global processing_status
    
    if processing_status["is_running"]:
        return jsonify({"success": False, "error": "已有任务在运行"})
    
    try:
        data = request.json
        urls = data.get('urls', [])
        cookie = data.get('cookie', '')
        
        if not urls or not cookie:
            return jsonify({"success": False, "error": "缺少必要参数"})
        
        # 清空之前的日志
        processing_status["logs"] = []
        
        # 启动处理线程
        thread = threading.Thread(
            target=process_urls_serial,
            args=(urls, cookie)
        )
        thread.start()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取处理状态"""
    return jsonify(processing_status)

@app.route('/api/heatmap-data', methods=['GET'])
def get_heatmap_data():
    """获取热力图数据"""
    if processing_status["heatmap_data"]:
        return jsonify({
            "success": True,
            "data": processing_status["heatmap_data"]
        })
    return jsonify({"success": False, "error": "暂无热力图数据"})

if __name__ == '__main__':
    print("=" * 60)
    print("腾讯文档智能监控系统 - 整合版")
    print("访问地址: http://202.140.143.88:8089")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8089, debug=False)