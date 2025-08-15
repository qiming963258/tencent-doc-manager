#!/usr/bin/env python3
"""
独立的热力图Web展示服务器
专门为当前端到端测试生成的热力图数据提供Web访问
完全独立，不影响原有UI系统的任何功能
"""

from flask import Flask, render_template_string, jsonify, send_file
import json
import os
import pandas as pd

app = Flask(__name__)

# HTML模板 - 简单的热力图展示界面
HEATMAP_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档管理系统 - 热力图分析报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
            color: #334155;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
        }
        
        .title {
            color: #1e293b;
            font-size: 28px;
            font-weight: 300;
            margin: 0 0 10px 0;
        }
        
        .subtitle {
            color: #64748b;
            font-size: 14px;
            margin: 0;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }
        
        .stat-desc {
            font-size: 11px;
            color: #64748b;
        }
        
        .l1 { color: #dc2626; }
        .l2 { color: #ea580c; }
        .l3 { color: #16a34a; }
        
        .heatmap-container {
            overflow-x: auto;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            margin-bottom: 30px;
        }
        
        .heatmap-table {
            border-collapse: collapse;
            width: 100%;
            min-width: 800px;
        }
        
        .heatmap-table th,
        .heatmap-table td {
            border: 1px solid #e2e8f0;
            padding: 8px;
            text-align: center;
            font-size: 12px;
        }
        
        .heatmap-table th {
            background-color: #f1f5f9;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .row-header {
            background-color: #f8fafc !important;
            font-weight: 500;
            text-align: left !important;
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .risk-cell {
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
        }
        
        .risk-cell:hover {
            transform: scale(1.1);
            z-index: 5;
            border: 2px solid #3b82f6 !important;
        }
        
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8fafc;
            border-radius: 6px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        }
        
        .details-section {
            margin-top: 30px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 500;
            color: #1e293b;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .detail-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
        }
        
        .detail-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .detail-item {
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .detail-item:last-child {
            border-bottom: none;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            transform: translate(-50%, -100%);
            white-space: nowrap;
        }
        
        .download-section {
            margin-top: 30px;
            text-align: center;
            padding: 20px;
            background: #f1f5f9;
            border-radius: 6px;
        }
        
        .download-button {
            display: inline-block;
            padding: 12px 24px;
            margin: 0 10px;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .download-button:hover {
            background: #2563eb;
        }
        
        .download-button.excel {
            background: #059669;
        }
        
        .download-button.excel:hover {
            background: #047857;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">📊 表格变更风险热力图分析</h1>
            <p class="subtitle">基于端到端测试数据生成 • 实时风险评估 • {{ matrix_size[0] }}×{{ matrix_size[1] }} 数据矩阵</p>
        </div>
        
        <!-- 统计数据面板 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number l1">{{ risk_distribution.L1 }}</div>
                <div class="stat-label l1">L1级别变更</div>
                <div class="stat-desc">绝对禁止修改</div>
            </div>
            <div class="stat-card">
                <div class="stat-number l2">{{ risk_distribution.L2 }}</div>
                <div class="stat-label l2">L2级别变更</div>
                <div class="stat-desc">需AI分析审核</div>
            </div>
            <div class="stat-card">
                <div class="stat-number l3">{{ risk_distribution.L3 }}</div>
                <div class="stat-label l3">L3级别变更</div>
                <div class="stat-desc">可自由编辑</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_changes }}</div>
                <div class="stat-label">总变更数</div>
                <div class="stat-desc">所有修改位置</div>
            </div>
        </div>
        
        <!-- 风险等级图例 -->
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ffffff;"></div>
                <span>无变更</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ffeb3b;"></div>
                <span>L3-低风险</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ff9800;"></div>
                <span>L2-中风险</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #f44336;"></div>
                <span>L1-高风险</span>
            </div>
        </div>
        
        <!-- 热力图表格 -->
        <div class="heatmap-container">
            <table class="heatmap-table">
                <thead>
                    <tr>
                        <th class="row-header">数据行</th>
                        {% for col_name in column_names %}
                        <th title="{{ col_name }}">{{ col_name[:6] }}{% if col_name|length > 6 %}...{% endif %}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row_index in range(matrix_size[0]) %}
                    <tr>
                        <td class="row-header">第{{ row_index + 1 }}行</td>
                        {% for col_index in range(matrix_size[1]) %}
                        {% set risk_value = risk_matrix[row_index][col_index] %}
                        <td class="risk-cell" 
                            style="background-color: {% if risk_value == 0 %}#ffffff{% elif risk_value == 1 %}#ffeb3b{% elif risk_value == 2 %}#ff9800{% else %}#f44336{% endif %}; color: {% if risk_value >= 2 %}white{% else %}#333{% endif %};"
                            title="行{{ row_index + 1 }}, {{ column_names[col_index] }}: {% if risk_value == 0 %}无变更{% elif risk_value == 1 %}L3-低风险{% elif risk_value == 2 %}L2-中风险{% else %}L1-高风险{% endif %}"
                            onmouseover="showTooltip(event, '{{ column_names[col_index] }}', {{ risk_value }}, {{ row_index + 1 }})"
                            onmouseout="hideTooltip()">
                            {% if risk_value > 0 %}{{ risk_value }}{% endif %}
                        </td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- 详细分析 -->
        <div class="details-section">
            <h2 class="section-title">🔍 详细分析结果</h2>
            <div class="details-grid">
                <div class="detail-card">
                    <h3>变更位置详情</h3>
                    <ul class="detail-list">
                        {% for mod in modification_locations[:10] %}
                        <li class="detail-item">
                            <span>第{{ mod.row + 1 }}行 - {{ mod.column_name }}</span>
                            <span class="{% if mod.risk_level == 'L1' %}l1{% elif mod.risk_level == 'L2' %}l2{% else %}l3{% endif %}">{{ mod.risk_level }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                    {% if modification_locations|length > 10 %}
                    <p style="text-align: center; margin-top: 10px; color: #64748b; font-size: 12px;">
                        显示前10个，共{{ modification_locations|length }}个变更位置
                    </p>
                    {% endif %}
                </div>
                
                <div class="detail-card">
                    <h3>风险等级说明</h3>
                    <ul class="detail-list">
                        <li class="detail-item">
                            <span><strong class="l1">L1级别</strong></span>
                            <span>绝对禁止</span>
                        </li>
                        <li class="detail-item">
                            <span><strong class="l2">L2级别</strong></span>
                            <span>AI审核</span>
                        </li>
                        <li class="detail-item">
                            <span><strong class="l3">L3级别</strong></span>
                            <span>自由编辑</span>
                        </li>
                        <li class="detail-item">
                            <span>检测算法</span>
                            <span>自适应对比</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- 下载链接 -->
        <div class="download-section">
            <h3>📁 报告下载</h3>
            <p style="margin-bottom: 20px; color: #64748b;">下载完整的分析报告文件</p>
            <a href="/download/excel" class="download-button excel">📊 Excel报告</a>
            <a href="/download/html" class="download-button">🌐 HTML报告</a>
            <a href="/download/json" class="download-button">📋 JSON数据</a>
        </div>
    </div>

    <script>
        let tooltip = null;
        
        function showTooltip(event, columnName, riskValue, rowNumber) {
            if (tooltip) hideTooltip();
            
            tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            
            const riskText = riskValue === 0 ? '无变更' : 
                           riskValue === 1 ? 'L3-低风险' : 
                           riskValue === 2 ? 'L2-中风险' : 'L1-高风险';
            
            tooltip.innerHTML = `
                <strong>第${rowNumber}行 - ${columnName}</strong><br>
                风险等级: ${riskText}<br>
                风险值: ${riskValue}
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = event.target.getBoundingClientRect();
            tooltip.style.left = (rect.left + rect.width / 2) + 'px';
            tooltip.style.top = (rect.top - 10) + 'px';
        }
        
        function hideTooltip() {
            if (tooltip) {
                document.body.removeChild(tooltip);
                tooltip = null;
            }
        }
        
        // 添加键盘快捷键支持
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideTooltip();
            }
        });
    </script>
</body>
</html>
"""

class HeatmapWebServer:
    """独立的热力图Web展示服务器"""
    
    def __init__(self):
        self.app = app
        self.setup_routes()
        self.load_data()
    
    def load_data(self):
        """加载热力图数据"""
        try:
            # 加载可视化数据
            with open('quick_visualization_data.json', 'r', encoding='utf-8') as f:
                self.viz_data = json.load(f)
            
            # 加载表格数据用于列名
            self.original_df = pd.read_csv('enterprise_test_original.csv', encoding='utf-8-sig')
            
            print("✅ 热力图数据加载成功")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            self.viz_data = None
            self.original_df = None
    
    def setup_routes(self):
        """设置Web路由"""
        
        @self.app.route('/')
        def index():
            """主页 - 显示热力图"""
            if not self.viz_data:
                return "<h1>❌ 数据加载失败</h1><p>请确保已运行端到端测试生成数据</p>"
            
            # 准备模板数据
            template_data = {
                'matrix_size': self.viz_data['matrix_size'],
                'risk_matrix': self.viz_data['risk_matrix'],
                'modification_locations': self.viz_data['modification_locations'],
                'risk_distribution': self.viz_data['risk_distribution'],
                'column_names': list(self.original_df.columns) if self.original_df is not None else [],
                'total_changes': len(self.viz_data['modification_locations'])
            }
            
            return render_template_string(HEATMAP_TEMPLATE, **template_data)
        
        @self.app.route('/api/data')
        def api_data():
            """API接口 - 返回JSON数据"""
            if not self.viz_data:
                return jsonify({'error': '数据未加载'}), 500
            
            return jsonify(self.viz_data)
        
        @self.app.route('/download/<format>')
        def download_report(format):
            """下载报告文件"""
            try:
                if format == 'excel':
                    file_path = '热力图可视化报告.xlsx'
                    return send_file(file_path, as_attachment=True, 
                                   download_name='热力图分析报告.xlsx',
                                   mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                
                elif format == 'html':
                    file_path = '热力图可视化报告.html'
                    return send_file(file_path, as_attachment=True,
                                   download_name='热力图分析报告.html',
                                   mimetype='text/html')
                
                elif format == 'json':
                    file_path = 'quick_visualization_data.json'
                    return send_file(file_path, as_attachment=True,
                                   download_name='热力图数据.json',
                                   mimetype='application/json')
                
                else:
                    return "❌ 不支持的文件格式", 400
                    
            except FileNotFoundError:
                return f"❌ 文件 {format} 不存在", 404
            except Exception as e:
                return f"❌ 下载失败: {str(e)}", 500
        
        @self.app.route('/status')
        def status():
            """系统状态"""
            status_info = {
                'data_loaded': self.viz_data is not None,
                'total_modifications': len(self.viz_data['modification_locations']) if self.viz_data else 0,
                'risk_distribution': self.viz_data['risk_distribution'] if self.viz_data else {},
                'matrix_size': self.viz_data['matrix_size'] if self.viz_data else [0, 0],
                'files_available': {
                    'excel': os.path.exists('热力图可视化报告.xlsx'),
                    'html': os.path.exists('热力图可视化报告.html'), 
                    'json': os.path.exists('quick_visualization_data.json')
                }
            }
            return jsonify(status_info)
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """启动Web服务器"""
        print(f"🌐 启动热力图Web服务器...")
        print(f"📡 访问地址: http://{host}:{port}")
        print(f"📊 API接口: http://{host}:{port}/api/data") 
        print(f"🔍 系统状态: http://{host}:{port}/status")
        print("=" * 50)
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函数"""
    server = HeatmapWebServer()
    
    # 检查数据文件是否存在
    if not os.path.exists('quick_visualization_data.json'):
        print("⚠️ 未找到热力图数据文件，请先运行以下命令生成数据：")
        print("python3 quick_e2e_test.py")
        print("python3 heatmap_visualizer.py")
        return
    
    try:
        server.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()