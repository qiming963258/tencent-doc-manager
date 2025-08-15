#!/usr/bin/env python3
"""
修复版热力图UI服务器 - 本地化资源加载
解决CDN连接问题，使用内联样式和简化的React组件
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/uploads/<filename>')
def download_file(filename):
    """提供上传文件的下载服务"""
    uploads_dir = '/root/projects/tencent-doc-manager/uploads'
    return send_from_directory(uploads_dir, filename)

@app.route('/api/test-data')
def get_test_data():
    """获取最新的测试数据"""
    try:
        # 找到最新的UI数据文件
        data_dir = '/root/projects/tencent-doc-manager'
        ui_files = [f for f in os.listdir(data_dir) if f.startswith('ui_data_') and f.endswith('.json')]
        if ui_files:
            latest_file = sorted(ui_files)[-1]
            with open(os.path.join(data_dir, latest_file), 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
    except Exception as e:
        print(f"Error loading test data: {e}")
    
    # 返回默认数据
    return jsonify({"tables": [], "statistics": {}})

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档变更监控 - 热力图分析</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .main-content {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .controls {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
        }
        
        .btn-primary:hover {
            background: #0056b3;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #1e7e34;
            transform: translateY(-2px);
        }
        
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        
        .btn-info:hover {
            background: #117a8b;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #545b62;
            transform: translateY(-2px);
        }
        
        .heatmap-section {
            padding: 30px;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
        }
        
        .heatmap-container {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            border: 2px solid #e9ecef;
        }
        
        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(19, 1fr);
            gap: 2px;
            max-width: 100%;
            overflow-x: auto;
        }
        
        .heatmap-cell {
            width: 32px;
            height: 28px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .heatmap-cell:hover {
            transform: scale(1.1);
            z-index: 10;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .statistics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            color: #6c757d;
        }
        
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 8px;
            margin: 20px;
            border: 1px solid #f5c6cb;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .btn {
                justify-content: center;
            }
            
            .heatmap-cell {
                width: 24px;
                height: 20px;
                font-size: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 腾讯文档变更监控热力图</h1>
            <p>企业级智能文档变更监控与风险评估系统</p>
        </div>
        
        <div class="main-content">
            <div class="controls">
                <button class="btn btn-primary" onclick="refreshData()">
                    <span>🔄</span>
                    刷新数据
                </button>
                <button class="btn btn-success" onclick="window.open('/uploads/half_filled_result_1755067386.xlsx', '_blank')">
                    <span>📥</span>
                    下载半填充Excel
                </button>
                <button class="btn btn-info" onclick="window.open('/uploads/tencent_import_guide.json', '_blank')">
                    <span>📋</span>
                    腾讯文档导入指导
                </button>
                <button class="btn btn-secondary" onclick="toggleGrid()">
                    <span>⚏</span>
                    <span id="gridToggleText">显示网格</span>
                </button>
            </div>
            
            <div class="heatmap-section">
                <div class="section-title">📊 30×19 智能热力图矩阵</div>
                <div id="heatmapContainer" class="heatmap-container">
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        正在加载热力图数据...
                    </div>
                </div>
                
                <div class="statistics" id="statisticsContainer">
                    <!-- 统计数据将在这里显示 -->
                </div>
            </div>
        </div>
    </div>
    
    <div id="tooltip" class="tooltip" style="display: none;"></div>

    <script>
        let heatmapData = null;
        let showGrid = false;
        
        // 获取科学热力图颜色
        function getScientificHeatColor(value) {
            if (value === 0) return '#f1f5f9';
            
            // 5级科学色彩分段：蓝→青→绿→黄→血红
            if (value <= 0.2) return '#3b82f6';      // 蓝色
            if (value <= 0.4) return '#06b6d4';      // 青色
            if (value <= 0.6) return '#10b981';      // 绿色
            if (value <= 0.8) return '#f59e0b';      // 黄色
            return '#dc2626';                        // 血红色
        }
        
        // 创建热力图
        function createHeatmap(data) {
            const container = document.getElementById('heatmapContainer');
            const grid = document.createElement('div');
            grid.className = 'heatmap-grid';
            
            // 创建30行×19列的矩阵
            for (let row = 0; row < 30; row++) {
                for (let col = 0; col < 19; col++) {
                    const cell = document.createElement('div');
                    cell.className = 'heatmap-cell';
                    
                    // 获取数据值
                    const value = (data.heatmap_matrix && 
                                  data.heatmap_matrix[row] && 
                                  data.heatmap_matrix[row][col]) || 0;
                    
                    cell.style.backgroundColor = getScientificHeatColor(value);
                    cell.textContent = value > 0 ? value.toFixed(2) : '';
                    
                    // 添加悬浮事件
                    cell.addEventListener('mouseenter', (e) => showTooltip(e, row, col, value));
                    cell.addEventListener('mouseleave', hideTooltip);
                    cell.addEventListener('mousemove', moveTooltip);
                    
                    grid.appendChild(cell);
                }
            }
            
            container.innerHTML = '';
            container.appendChild(grid);
        }
        
        // 显示提示
        function showTooltip(e, row, col, value) {
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = `
                <strong>位置:</strong> 第${row + 1}行, 第${col + 1}列<br>
                <strong>风险值:</strong> ${value.toFixed(3)}<br>
                <strong>风险等级:</strong> ${getRiskLevel(value)}<br>
                <strong>颜色:</strong> ${getColorName(value)}
            `;
            tooltip.style.display = 'block';
            moveTooltip(e);
        }
        
        function hideTooltip() {
            document.getElementById('tooltip').style.display = 'none';
        }
        
        function moveTooltip(e) {
            const tooltip = document.getElementById('tooltip');
            tooltip.style.left = e.pageX + 15 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';
        }
        
        function getRiskLevel(value) {
            if (value === 0) return '无风险';
            if (value <= 0.3) return '低风险';
            if (value <= 0.6) return '中风险';
            if (value <= 0.8) return '高风险';
            return '极高风险';
        }
        
        function getColorName(value) {
            if (value === 0) return '浅灰色';
            if (value <= 0.2) return '蓝色';
            if (value <= 0.4) return '青色';
            if (value <= 0.6) return '绿色';
            if (value <= 0.8) return '黄色';
            return '血红色';
        }
        
        // 创建统计面板
        function createStatistics(data) {
            const container = document.getElementById('statisticsContainer');
            const stats = data.statistics || {};
            
            container.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.l1_count || 0}</div>
                    <div class="stat-label">🔴 严重修改(L1)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.l2_count || 0}</div>
                    <div class="stat-label">🟡 异常修改(L2)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.l3_count || 0}</div>
                    <div class="stat-label">🟢 常规修改(L3)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_hotspots || 0}</div>
                    <div class="stat-label">🔥 总热点数量</div>
                </div>
            `;
        }
        
        // 加载数据
        async function loadData() {
            try {
                const response = await fetch('/api/test-data');
                const data = await response.json();
                
                heatmapData = data;
                createHeatmap(data);
                createStatistics(data);
                
                console.log('热力图数据加载成功:', data);
            } catch (error) {
                console.error('数据加载失败:', error);
                document.getElementById('heatmapContainer').innerHTML = 
                    '<div class="error">❌ 数据加载失败，请检查服务器连接</div>';
            }
        }
        
        // 刷新数据
        function refreshData() {
            document.getElementById('heatmapContainer').innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    正在刷新数据...
                </div>
            `;
            loadData();
        }
        
        // 切换网格
        function toggleGrid() {
            showGrid = !showGrid;
            const cells = document.querySelectorAll('.heatmap-cell');
            const toggleText = document.getElementById('gridToggleText');
            
            cells.forEach(cell => {
                if (showGrid) {
                    cell.style.border = '1px solid #ccc';
                } else {
                    cell.style.border = 'none';
                }
            });
            
            toggleText.textContent = showGrid ? '隐藏网格' : '显示网格';
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
        });
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("🚀 启动修复版热力图UI服务器...")
    print("📊 访问地址: http://192.140.176.198:8089")
    print("🔧 本地化资源，无需外部CDN依赖")
    app.run(host='0.0.0.0', port=8089, debug=True)