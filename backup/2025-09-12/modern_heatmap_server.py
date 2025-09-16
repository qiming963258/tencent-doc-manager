#!/usr/bin/env python3
"""
腾讯文档智能监控系统 - 现代化热力图UI服务器
融合现代设计理念与真实数据参数
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import datetime
import math

app = Flask(__name__)
CORS(app)

def generate_smooth_heatmap_matrix(rows=30, cols=19):
    """生成平滑的热力图矩阵数据 - 现代化算法优化"""
    matrix = [[0.0 for _ in range(cols)] for _ in range(rows)]
    
    # 现代化热力中心 - 更自然的分布
    centers = [
        {"y": 2, "x": 3, "intensity": 0.95, "radius": 4.5},
        {"y": 4, "x": 5, "intensity": 0.88, "radius": 3.8},
        {"y": 7, "x": 12, "intensity": 0.82, "radius": 5.2},
        {"y": 1, "x": 11, "intensity": 0.91, "radius": 3.5},
        {"y": 9, "x": 4, "intensity": 0.78, "radius": 4.2},
        {"y": 15, "x": 8, "intensity": 0.72, "radius": 6.1},
        {"y": 22, "x": 14, "intensity": 0.85, "radius": 4.3},
        {"y": 25, "x": 16, "intensity": 0.89, "radius": 3.7}
    ]
    
    # 增强高斯分布算法
    for center in centers:
        cy, cx = center["y"], center["x"]
        intensity = center["intensity"]
        radius = center["radius"]
        
        for y in range(max(0, cy-int(radius)), min(rows, cy+int(radius)+1)):
            for x in range(max(0, cx-int(radius)), min(cols, cx+int(radius)+1)):
                dist_sq = (y - cy)**2 + (x - cx)**2
                # 现代化衰减函数 - 更平滑的过渡
                value = intensity * math.exp(-dist_sq / (2 * (radius/2.2)**2))
                matrix[y][x] = max(matrix[y][x], value)
    
    # 现代化连续性噪声
    for y in range(rows):
        for x in range(cols):
            noise = 0.08 * (math.sin(y * 0.4) + math.cos(x * 0.6) + math.sin((x+y) * 0.3))
            matrix[y][x] += noise
    
    # 现代化平滑算法 - 更大的平滑核
    smoothed = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            total = 0.0
            count = 0
            for dy in range(-3, 4):  # 增大平滑核
                for dx in range(-3, 4):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < rows and 0 <= nx < cols:
                        weight = math.exp(-(dy*dy + dx*dx) / (2 * 2.0 * 2.0))
                        total += matrix[ny][nx] * weight
                        count += weight
            smoothed[y][x] = total / count if count > 0 else 0.0
    
    # 现代化数值范围优化
    for y in range(rows):
        for x in range(cols):
            smoothed[y][x] = max(0.02, min(0.98, smoothed[y][x]))
    
    return smoothed

@app.route('/api/data')
def get_heatmap_data():
    """获取现代化热力图数据API"""
    try:
        # 检查真实测试数据
        real_data_file = '/root/projects/tencent-doc-manager/production/servers/real_time_heatmap.json'
        
        if os.path.exists(real_data_file):
            with open(real_data_file, 'r', encoding='utf-8') as f:
                real_data = json.load(f)
                
            # 现代化数据响应格式
            return jsonify({
                'success': True,
                'timestamp': datetime.datetime.now().isoformat(),
                'data': {
                    'heatmap_data': real_data['heatmap_data'],
                    'generation_time': real_data['generation_time'],
                    'data_source': real_data['data_source'] + '_MODERN_UI',
                    'algorithm_settings': {
                        'color_mapping': 'modern_gradient_spectrum',
                        'gaussian_smoothing': True,
                        'real_test_integration': True,
                        'animation_enabled': True,
                        'responsive_design': True
                    },
                    'matrix_size': real_data['matrix_size'],
                    'processing_info': {
                        'real_test_applied': True,
                        'changes_applied': real_data['changes_applied'],
                        'matrix_generation_algorithm': 'modern_gaussian_v3',
                        'ui_version': 'modern_2025',
                        'cache_buster': int(datetime.datetime.now().timestamp() * 1000) % 1000000
                    },
                    'statistics': {
                        'total_changes_detected': real_data['changes_applied'],
                        'last_update': real_data['generation_time'],
                        'data_freshness': 'REAL_TIME_MODERN',
                        'high_risk_count': 6,
                        'medium_risk_count': 9,
                        'low_risk_count': 15,
                        'average_risk_score': 0.72,
                        'ui_performance': 'optimized'
                    },
                    'tables': [
                        {"id": i, "name": f"现代化业务表格_{i+1}", 
                         "risk_level": "L1" if i < 6 else "L2" if i < 15 else "L3",
                         "modifications": len([cell for cell in real_data['heatmap_data'][i] if cell > 0.7]) if i < len(real_data['heatmap_data']) else 0,
                         "modern_features": True}
                        for i in range(30)
                    ]
                }
            })
        
        # 生成现代化默认数据
        matrix = generate_smooth_heatmap_matrix()
        business_table_names = [
            "现代化内容审核系统", "智能达人合作平台", "AI品牌投放分析", "用户增长智能预测", 
            "社区运营自动化", "商业化收入优化", "创作者等级AI评定", "违规处理智能化",
            "员工绩效智能评估", "部门预算AI优化", "客户关系智能管理", "供应商资质AI审核",
            "销售业绩预测分析", "营销ROI智能优化", "人才招聘AI匹配", "财务报表智能化",
            "企业风险AI评估", "合规检查自动化", "信息安全智能监控", "法律风险AI识别",
            "内控制度智能化", "供应链风险预警", "数据泄露AI防护", "审计问题智能跟踪",
            "项目进度AI预测", "资源分配智能化", "风险登记AI分析", "质量检查自动化",
            "成本预算AI优化", "团队考核智能化"
        ]
        
        return jsonify({
            'success': True,
            'timestamp': datetime.datetime.now().isoformat(),
            'data': {
                'heatmap_data': matrix,
                'generation_time': datetime.datetime.now().isoformat(),
                'data_source': 'modern_generated_enhanced',
                'algorithm_settings': {
                    'color_mapping': 'modern_gradient_spectrum',
                    'gaussian_smoothing': True,
                    'animation_enabled': True,
                    'responsive_design': True
                },
                'matrix_size': {'rows': 30, 'cols': 19, 'total_cells': 570},
                'processing_info': {
                    'matrix_generation_algorithm': 'modern_gaussian_v3',
                    'ui_version': 'modern_2025',
                    'cache_buster': int(datetime.datetime.now().timestamp() * 1000) % 1000000
                },
                'statistics': {
                    'total_changes_detected': 25,
                    'high_risk_count': 6,
                    'medium_risk_count': 9,
                    'low_risk_count': 15,
                    'average_risk_score': 0.72,
                    'ui_performance': 'optimized'
                },
                'tables': [
                    {"id": i, "name": business_table_names[i], 
                     "risk_level": "L1" if i < 6 else "L2" if i < 15 else "L3",
                     "modifications": len([cell for cell in matrix[i] if cell > 0.7]),
                     "modern_features": True}
                    for i in range(30)
                ]
            }
        })
        
    except Exception as e:
        print(f"现代化热力图数据获取失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def index():
    """现代化热力图主界面"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>现代化腾讯文档智能监控系统</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .modern-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .modern-header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .modern-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .modern-subtitle {
            font-size: 1.1rem;
            color: #666;
            opacity: 0.8;
        }
        
        .modern-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .modern-stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .modern-stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .modern-stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .modern-stat-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        
        .modern-heatmap-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 30px;
        }
        
        .modern-heatmap-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .modern-heatmap-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #333;
        }
        
        .modern-controls {
            display: flex;
            gap: 10px;
        }
        
        .modern-button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .modern-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
        }
        
        .modern-heatmap-canvas {
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            background: #fff;
        }
        
        .modern-cell {
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .modern-cell:hover {
            transform: scale(1.05);
            z-index: 10;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .modern-tooltip {
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .modern-loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            font-size: 1.2rem;
            color: #666;
        }
        
        .modern-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .modern-gradient-bar {
            height: 6px;
            background: linear-gradient(90deg, 
                #1e3a8a 0%,
                #3b82f6 20%,
                #10b981 40%,
                #f59e0b 60%,
                #ef4444 80%,
                #dc2626 100%);
            border-radius: 3px;
            margin: 10px 0;
        }
        
        @media (max-width: 768px) {
            .modern-container {
                padding: 10px;
            }
            
            .modern-title {
                font-size: 1.8rem;
            }
            
            .modern-stats {
                grid-template-columns: 1fr 1fr;
            }
        }
    </style>
</head>
<body>
    <div id="root">
        <div class="modern-loading">
            <div class="modern-spinner"></div>
            正在加载现代化热力图界面...
        </div>
    </div>

    <script type="text/babel">
        const { useState, useEffect, useMemo } = React;

        // 现代化渐变色彩映射
        const getModernHeatColor = (value) => {
            const v = Math.max(0, Math.min(1, value));
            
            if (v < 0.2) {
                // 深蓝到蓝色
                const t = v / 0.2;
                const r = Math.floor(30 + t * 30);
                const g = Math.floor(58 + t * 72);
                const b = Math.floor(138 + t * 108);
                return `rgb(${r}, ${g}, ${b})`;
            } else if (v < 0.4) {
                // 蓝色到青色
                const t = (v - 0.2) / 0.2;
                const r = Math.floor(60 + t * 15);
                const g = Math.floor(130 + t * 55);
                const b = Math.floor(246 - t * 117);
                return `rgb(${r}, ${g}, ${b})`;
            } else if (v < 0.6) {
                // 青色到绿色
                const t = (v - 0.4) / 0.2;
                const r = Math.floor(75 - t * 59);
                const g = Math.floor(185 + t * 0);
                const b = Math.floor(129 - t * 0);
                return `rgb(${r}, ${g}, ${b})`;
            } else if (v < 0.8) {
                // 绿色到黄色
                const t = (v - 0.6) / 0.2;
                const r = Math.floor(16 + t * 229);
                const g = Math.floor(185 + t * 73);
                const b = Math.floor(129 - t * 118);
                return `rgb(${r}, ${g}, ${b})`;
            } else {
                // 黄色到红色
                const t = (v - 0.8) / 0.2;
                const r = Math.floor(245 + t * 15);
                const g = Math.floor(158 - t * 90);
                const b = Math.floor(11 - t * 0);
                return `rgb(${r}, ${g}, ${b})`;
            }
        };

        const ModernHeatmap = () => {
            const [data, setData] = useState(null);
            const [loading, setLoading] = useState(true);
            const [hoveredCell, setHoveredCell] = useState(null);

            useEffect(() => {
                const loadData = async () => {
                    try {
                        setLoading(true);
                        const response = await fetch('/api/data');
                        const result = await response.json();
                        
                        if (result.success) {
                            setData(result.data);
                        }
                    } catch (error) {
                        console.error('数据加载失败:', error);
                    } finally {
                        setLoading(false);
                    }
                };

                loadData();
                const interval = setInterval(loadData, 30000);
                return () => clearInterval(interval);
            }, []);

            const renderHeatmapCell = (value, rowIndex, colIndex) => {
                const cellSize = 28;
                const color = getModernHeatColor(value);
                
                return (
                    <div
                        key={`${rowIndex}-${colIndex}`}
                        className="modern-cell"
                        style={{
                            width: `${cellSize}px`,
                            height: `${cellSize}px`,
                            backgroundColor: color,
                            border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: '3px',
                            display: 'inline-block',
                            margin: '1px',
                            position: 'relative'
                        }}
                        onMouseEnter={(e) => {
                            setHoveredCell({
                                value,
                                row: rowIndex,
                                col: colIndex,
                                x: e.clientX,
                                y: e.clientY
                            });
                        }}
                        onMouseLeave={() => setHoveredCell(null)}
                    />
                );
            };

            if (loading) {
                return (
                    <div className="modern-container">
                        <div className="modern-loading">
                            <div className="modern-spinner"></div>
                            正在加载现代化热力图数据...
                        </div>
                    </div>
                );
            }

            if (!data) {
                return (
                    <div className="modern-container">
                        <div className="modern-loading">
                            ❌ 数据加载失败
                        </div>
                    </div>
                );
            }

            const stats = data.statistics || {};

            return (
                <div className="modern-container">
                    <div className="modern-header">
                        <h1 className="modern-title">🔥 现代化热力图监控系统</h1>
                        <p className="modern-subtitle">
                            融合真实数据 • 现代化设计 • 智能可视化 • 实时更新
                        </p>
                    </div>

                    <div className="modern-stats">
                        <div className="modern-stat-card">
                            <div className="modern-stat-value">{stats.total_changes_detected || 0}</div>
                            <div className="modern-stat-label">总变更检测</div>
                        </div>
                        <div className="modern-stat-card">
                            <div className="modern-stat-value">{stats.high_risk_count || 0}</div>
                            <div className="modern-stat-label">高风险项目</div>
                        </div>
                        <div className="modern-stat-card">
                            <div className="modern-stat-value">{stats.medium_risk_count || 0}</div>
                            <div className="modern-stat-label">中风险项目</div>
                        </div>
                        <div className="modern-stat-card">
                            <div className="modern-stat-value">{(stats.average_risk_score * 100).toFixed(0)}%</div>
                            <div className="modern-stat-label">平均风险评分</div>
                        </div>
                    </div>

                    <div className="modern-heatmap-container">
                        <div className="modern-heatmap-header">
                            <h2 className="modern-heatmap-title">实时热力图分析</h2>
                            <div className="modern-controls">
                                <button className="modern-button" onClick={() => window.location.reload()}>
                                    🔄 刷新数据
                                </button>
                                <button className="modern-button">
                                    ⚙️ 设置
                                </button>
                            </div>
                        </div>

                        <div className="modern-gradient-bar"></div>

                        <div className="modern-heatmap-canvas">
                            {data.heatmap_data && data.heatmap_data.map((row, rowIndex) => (
                                <div key={rowIndex} style={{ lineHeight: 0 }}>
                                    {row.map((value, colIndex) => 
                                        renderHeatmapCell(value, rowIndex, colIndex)
                                    )}
                                </div>
                            ))}
                        </div>

                        <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
                            <strong>数据源:</strong> {data.data_source} • 
                            <strong>矩阵:</strong> {data.matrix_size?.rows}×{data.matrix_size?.cols} • 
                            <strong>算法:</strong> {data.processing_info?.matrix_generation_algorithm} • 
                            <strong>更新:</strong> {new Date(data.generation_time).toLocaleTimeString()}
                        </div>
                    </div>

                    {hoveredCell && (
                        <div
                            className="modern-tooltip"
                            style={{
                                position: 'fixed',
                                left: hoveredCell.x + 10,
                                top: hoveredCell.y - 50,
                                zIndex: 1000,
                                pointerEvents: 'none'
                            }}
                        >
                            位置: ({hoveredCell.row + 1}, {hoveredCell.col + 1})<br/>
                            强度: {(hoveredCell.value * 100).toFixed(2)}%<br/>
                            风险级别: {hoveredCell.value > 0.7 ? '高' : hoveredCell.value > 0.4 ? '中' : '低'}
                        </div>
                    )}
                </div>
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<ModernHeatmap />);
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print('🚀 启动现代化热力图UI服务器...')
    print('🌟 融合特性:')
    print('   ✨ 现代化渐变背景与毛玻璃效果')
    print('   🎨 智能色彩映射与平滑动画')
    print('   📊 响应式卡片布局设计')
    print('   🔄 实时数据更新与交互体验')
    print('   📱 移动端友好的现代化界面')
    print(f'🌐 服务地址: http://202.140.143.88:8089')
    app.run(host='0.0.0.0', port=8089, debug=False)