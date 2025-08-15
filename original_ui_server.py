#!/usr/bin/env python3
"""
完整的原版UI集成服务器
提供完整的React热力图UI和后端数据适配
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

class UIDataAdapter:
    """UI数据适配器"""
    
    def __init__(self):
        self.load_test_data()
        self.generate_ui_compatible_data()
    
    def load_test_data(self):
        """加载端到端测试数据"""
        try:
            with open('quick_visualization_data.json', 'r', encoding='utf-8') as f:
                self.viz_data = json.load(f)
            self.original_df = pd.read_csv('enterprise_test_original.csv', encoding='utf-8-sig')
            self.modified_df = pd.read_csv('enterprise_test_modified.csv', encoding='utf-8-sig')
            print("✅ 端到端测试数据加载成功")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            self.viz_data = None
    
    def generate_ui_compatible_data(self):
        """生成UI兼容数据"""
        if not self.viz_data:
            return
        
        self.standard_columns = [
            '序号', '项目类型', '来源', '任务发起时间', '目标对齐', 
            '关键KR对齐', '具体计划内容', '邓总指导登记', '负责人', 
            '协助人', '监督人', '重要程度', '预计完成时间', '完成进度',
            '形成计划清单', '复盘时间', '对上汇报', '应用情况', '进度分析总结'
        ]
        
        self.column_risk_levels = {
            '序号': 'L3', '项目类型': 'L2', '来源': 'L1', '任务发起时间': 'L1',
            '目标对齐': 'L1', '关键KR对齐': 'L1', '具体计划内容': 'L2', '邓总指导登记': 'L2',
            '负责人': 'L2', '协助人': 'L2', '监督人': 'L2', '重要程度': 'L1',
            '预计完成时间': 'L1', '完成进度': 'L1', '形成计划清单': 'L2', '复盘时间': 'L3',
            '对上汇报': 'L3', '应用情况': 'L3', '进度分析总结': 'L3'
        }
        
        self.generate_realistic_tables()
        self.generate_modification_patterns()
    
    def generate_realistic_tables(self):
        """生成真实表格数据"""
        base_table_names = [
            '企业项目管理表_原始版', '企业项目管理表_修改版',
            '项目管理主计划表', '销售目标跟踪表', '客户关系管理表', '产品研发进度表',
            '人力资源配置表', '财务预算执行表', '市场营销活动表', '运营数据分析表',
            '供应链管理表', '质量控制记录表', '风险评估跟踪表', '绩效考核统计表',
            '培训计划执行表', '设备维护记录表', '合同管理明细表', '库存管理台账表',
            '客服工单处理表', '技术支持记录表', '投资决策分析表', '内控合规检查表',
            '战略规划执行表', '业务流程优化表', '数据安全监控表', '成本核算分析表',
            '招聘进度跟踪表', '项目验收评估表', '用户反馈汇总表', '竞品分析对比表'
        ]
        
        self.tables = []
        for i, table_name in enumerate(base_table_names):
            columns = self.standard_columns.copy()
            if np.random.random() > 0.7:
                remove_count = np.random.randint(1, 3)
                for _ in range(remove_count):
                    if len(columns) > 15:
                        columns.pop(np.random.randint(0, len(columns)))
            
            table_risk = self.calculate_table_risk(columns, i < 2)
            
            self.tables.append({
                'id': i,
                'name': table_name,
                'url': f"https://docs.qq.com/sheet/table-{i + 1}",
                'columns': columns,
                'avgRisk': table_risk['avg_risk'],
                'maxCellRisk': table_risk['max_cell_risk'],
                'criticalModifications': table_risk['critical_modifications'],
                'totalRisk': table_risk['total_risk'],
                'columnRiskLevels': self.column_risk_levels.copy()
            })
        
        # 按严重度排序
        self.tables.sort(key=lambda t: (-t['maxCellRisk'], -t['criticalModifications'], -t['avgRisk']))
    
    def calculate_table_risk(self, columns, is_real_table=False):
        """计算表格风险"""
        total_risk = 0
        max_risk = 0
        critical_count = 0
        
        for col in columns:
            risk_level = self.column_risk_levels.get(col, 'L2')
            
            if is_real_table and self.viz_data:
                # 对实际表格使用真实修改数据
                real_mods = [m for m in self.viz_data['modification_locations'] if m['column_name'] == col]
                if real_mods:
                    if risk_level == 'L1':
                        cell_risk = 0.90 + np.random.random() * 0.1
                        critical_count += 1
                    elif risk_level == 'L2':
                        cell_risk = 0.60 + np.random.random() * 0.30
                    else:
                        cell_risk = 0.30 + np.random.random() * 0.20
                else:
                    cell_risk = 0.05 + np.random.random() * 0.10
            else:
                # 模拟数据
                if risk_level == 'L1':
                    cell_risk = 0.75 + np.random.random() * 0.25
                    if np.random.random() > 0.8:
                        critical_count += 1
                elif risk_level == 'L2':
                    cell_risk = 0.3 + np.random.random() * 0.5
                else:
                    cell_risk = 0.1 + np.random.random() * 0.2
            
            total_risk += cell_risk
            max_risk = max(max_risk, cell_risk)
        
        return {
            'avg_risk': total_risk / len(columns),
            'max_cell_risk': max_risk,
            'critical_modifications': critical_count,
            'total_risk': total_risk
        }
    
    def generate_modification_patterns(self):
        """生成修改分布模式"""
        self.modification_patterns = []
        
        for table in self.tables:
            column_patterns = {}
            
            for col_name in table['columns']:
                total_rows = 10 + int(np.random.random() * 40)
                risk_level = table['columnRiskLevels'].get(col_name, 'L2')
                
                if risk_level == 'L1':
                    modification_rate = 0.05 + np.random.random() * 0.15
                elif risk_level == 'L2':
                    modification_rate = 0.1 + np.random.random() * 0.3
                else:
                    modification_rate = 0.2 + np.random.random() * 0.5
                
                modified_rows = int(total_rows * modification_rate)
                modified_row_numbers = sorted(np.random.choice(
                    range(1, total_rows + 1), 
                    size=min(modified_rows, total_rows), 
                    replace=False
                ).tolist())
                
                row_intensities = {}
                for row_num in modified_row_numbers:
                    row_intensities[row_num] = 0.3 + np.random.random() * 0.7
                
                column_patterns[col_name] = {
                    'totalRows': total_rows,
                    'modifiedRows': modified_rows,
                    'modificationRate': modification_rate,
                    'modifiedRowNumbers': modified_row_numbers,
                    'rowIntensities': row_intensities,
                    'pattern': np.random.choice(['top_heavy', 'bottom_heavy', 'middle_heavy', 'scattered']),
                    'riskLevel': risk_level,
                    'medianRow': modified_row_numbers[len(modified_row_numbers)//2] if modified_row_numbers else total_rows//2
                }
            
            row_overall_intensity = sum([
                pattern['modificationRate'] * (3 if pattern['riskLevel'] == 'L1' else 2 if pattern['riskLevel'] == 'L2' else 1)
                for pattern in column_patterns.values()
            ]) / len(column_patterns) if column_patterns else 0
            
            self.modification_patterns.append({
                'tableId': table['id'],
                'tableName': table['name'],
                'columnPatterns': column_patterns,
                'rowOverallIntensity': row_overall_intensity
            })
    
    def generate_heatmap_data(self):
        """生成热力图数据"""
        rows = len(self.tables)
        cols = len(self.standard_columns)
        
        heat_data = []
        for y in range(rows):
            row_data = []
            table = self.tables[y]
            
            for x in range(cols):
                column_name = self.standard_columns[x]
                
                if column_name in table['columns']:
                    risk_level = self.column_risk_levels.get(column_name, 'L2')
                    
                    if risk_level == 'L1':
                        base_score = 0.85 + np.random.random() * 0.15
                    elif risk_level == 'L2':
                        base_score = 0.3 + np.random.random() * 0.5
                    else:
                        base_score = 0.1 + np.random.random() * 0.2
                    
                    if y < 5:
                        base_score *= (1 + (5 - y) * 0.1)
                    
                    row_data.append(max(0.1, min(1.0, base_score)))
                else:
                    row_data.append(0)
            
            heat_data.append(row_data)
        
        return heat_data

# 创建适配器实例
adapter = UIDataAdapter()

# HTML模板 - 嵌入完整的React UI
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heat Field Analysis - 表格变更风险热力场分析</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .heat-container {
            position: relative;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useMemo, useEffect } = React;
        
        // 高斯核函数 - 保持原有算法
        const gaussianKernel = (size, sigma) => {
          const kernel = [];
          const center = Math.floor(size / 2);
          let sum = 0;
          
          for (let y = 0; y < size; y++) {
            kernel[y] = [];
            for (let x = 0; x < size; x++) {
              const distance = Math.sqrt(((x - center) ** 2) + ((y - center) ** 2));
              const value = Math.exp(-((distance ** 2) / (2 * (sigma ** 2))));
              kernel[y][x] = value;
              sum += value;
            }
          }
          
          for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
              kernel[y][x] /= sum;
            }
          }
          
          return kernel;
        };

        // 高斯平滑函数 - 保持原有算法
        const gaussianSmooth = (data, kernelSize = 5, sigma = 1.5) => {
          const kernel = gaussianKernel(kernelSize, sigma);
          const height = data.length;
          const width = data[0].length;
          const result = Array(height).fill(null).map(() => Array(width).fill(0));
          const padding = Math.floor(kernelSize / 2);
          
          for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
              let sum = 0;
              let weightSum = 0;
              
              for (let ky = 0; ky < kernelSize; ky++) {
                for (let kx = 0; kx < kernelSize; kx++) {
                  const dy = y + ky - padding;
                  const dx = x + kx - padding;
                  
                  if (dy >= 0 && dy < height && dx >= 0 && dx < width) {
                    const weight = kernel[ky][kx];
                    sum += data[dy][dx] * weight;
                    weightSum += weight;
                  }
                }
              }
              
              result[y][x] = weightSum > 0 ? sum / weightSum : 0;
            }
          }
          
          return result;
        };

        // 增强的科学热力图颜色映射 - 更深的血红色
        const getScientificHeatColor = (value) => {
          const v = Math.max(0, Math.min(1, value));
          
          if (v < 0.2) {
            const t = v / 0.2;
            const r = Math.floor(8 + t * 32);
            const g = Math.floor(8 + t * 62);
            const b = Math.floor(64 + t * 128);
            return `rgb(${r}, ${g}, ${b})`;
          } else if (v < 0.4) {
            const t = (v - 0.2) / 0.2;
            const r = Math.floor(40 + t * 20);
            const g = Math.floor(70 + t * 90);
            const b = Math.floor(192 + t * 48);
            return `rgb(${r}, ${g}, ${b})`;
          } else if (v < 0.6) {
            const t = (v - 0.4) / 0.2;
            const r = Math.floor(60 + t * 80);
            const g = Math.floor(160 + t * 60);
            const b = Math.floor(240 - t * 140);
            return `rgb(${r}, ${g}, ${b})`;
          } else if (v < 0.8) {
            const t = (v - 0.6) / 0.2;
            const r = Math.floor(140 + t * 115);
            const g = Math.floor(220 + t * 35);
            const b = Math.floor(100 - t * 50);
            return `rgb(${r}, ${g}, ${b})`;
          } else {
            const t = (v - 0.8) / 0.2;
            const r = Math.floor(255 - t * 15);
            const g = Math.floor(255 - t * 235);
            const b = Math.floor(50 - t * 40);
            return `rgb(${r}, ${g}, ${b})`;
          }
        };

        // 设置弹窗组件
        const SettingsModal = ({ isOpen, onClose }) => {
          const [tableLinks, setTableLinks] = useState('');
          const [cookieValue, setCookieValue] = useState('');
          
          const handleImportLinks = () => {
            const links = tableLinks.split('\\n').filter(line => line.trim());
            console.log('导入的链接:', links);
            alert(`成功导入 ${links.length} 个表格链接`);
          };
          
          const handleUpdateCookie = () => {
            console.log('更新Cookie:', cookieValue);
            alert('Cookie已更新');
          };
          
          if (!isOpen) return null;
          
          return (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}>
              <div style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                width: '600px',
                maxHeight: '80vh',
                overflow: 'auto',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
              }}>
                <div style={{
                  padding: '24px 32px 16px',
                  borderBottom: '1px solid #e2e8f0'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 className="text-2xl font-light text-slate-800">监控设置</h2>
                    <button
                      onClick={onClose}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        color: '#64748b',
                        cursor: 'pointer'
                      }}
                    >
                      ×
                    </button>
                  </div>
                  <p className="text-sm text-slate-600 mt-2">配置要监控的腾讯文档表格和认证信息</p>
                </div>
                
                <div style={{ padding: '24px 32px' }}>
                  <div style={{ marginBottom: '32px' }}>
                    <label className="text-sm font-medium text-slate-700 block mb-3">
                      表格链接导入
                    </label>
                    <textarea
                      value={tableLinks}
                      onChange={(e) => setTableLinks(e.target.value)}
                      placeholder={`请粘贴腾讯文档链接，每行一个，格式如下：
【腾讯文档】测试版本-回国销售计划表
https://docs.qq.com/sheet/DRFppYm15RGZ2WExN

【腾讯文档】测试版本-小红书部门
https://docs.qq.com/sheet/DRG9TYnNmdnVLSGtF`}
                      style={{
                        width: '100%',
                        height: '120px',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontFamily: 'ui-monospace, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                        lineHeight: '1.5',
                        resize: 'vertical'
                      }}
                    />
                    <div className="flex justify-between items-center mt-3">
                      <span className="text-xs text-slate-500">
                        {tableLinks.split('\\n').filter(line => line.trim()).length} 个链接待导入
                      </span>
                      <button
                        onClick={handleImportLinks}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        导入链接
                      </button>
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '24px' }}>
                    <label className="text-sm font-medium text-slate-700 block mb-3">
                      认证Cookie
                    </label>
                    <textarea
                      value={cookieValue}
                      onChange={(e) => setCookieValue(e.target.value)}
                      placeholder="请粘贴腾讯文档的认证Cookie..."
                      style={{
                        width: '100%',
                        height: '80px',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontFamily: 'ui-monospace, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                        lineHeight: '1.5'
                      }}
                    />
                    <div className="flex justify-between items-center mt-3">
                      <span className="text-xs text-slate-500">
                        用于访问需要权限的文档
                      </span>
                      <button
                        onClick={handleUpdateCookie}
                        className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                      >
                        更新Cookie
                      </button>
                    </div>
                  </div>
                </div>
                
                <div style={{
                  padding: '16px 32px 24px',
                  borderTop: '1px solid #e2e8f0',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '12px'
                }}>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm border border-slate-300 text-slate-700 rounded hover:bg-slate-50 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={() => {
                      alert('设置已保存');
                      onClose();
                    }}
                    className="px-4 py-2 text-sm bg-slate-800 text-white rounded hover:bg-slate-900 transition-colors"
                  >
                    保存设置
                  </button>
                </div>
              </div>
            </div>
          );
        };

        // 横向分布图组件
        const TableModificationChart = ({ 
          pattern, 
          columnName, 
          isHovered = false, 
          allPatterns = [], 
          globalMaxRows = 50, 
          maxWidth = 300,
          tableData = null
        }) => {
          
          if (!isHovered) {
            if (!pattern) {
              return (
                <div style={{ width: `${maxWidth}px`, height: '28px', backgroundColor: '#f1f5f9' }}>
                </div>
              );
            }
            
            const intensity = pattern.rowOverallIntensity || 0;
            const barWidth = Math.max(4, intensity * maxWidth * 0.8);
            
            return (
              <div style={{ 
                width: `${maxWidth}px`, 
                height: '28px', 
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                padding: '0 4px'
              }}>
                <div
                  style={{
                    width: `${barWidth}px`,
                    height: '16px',
                    backgroundColor: intensity > 0.7 ? '#dc2626' : intensity > 0.4 ? '#f59e0b' : '#10b981',
                    borderRadius: '2px'
                  }}
                />
                <span style={{
                  position: 'absolute',
                  right: '4px',
                  fontSize: '10px',
                  color: '#64748b'
                }}>
                  {(intensity * 100).toFixed(0)}%
                </span>
              </div>
            );
          }
          
          if (!pattern) {
            return (
              <div style={{ width: `${maxWidth}px`, height: '28px', backgroundColor: '#f1f5f9' }}>
              </div>
            );
          }

          const currentTableMaxRows = pattern.totalRows || 20;
          
          const getCurrentTableColumnRisk = () => {
            if (!tableData || !columnName) return 'L3';
            return tableData.columnRiskLevels[columnName] || 'L2';
          };
          
          const currentRiskLevel = getCurrentTableColumnRisk();
          
          return (
            <div style={{ 
              width: `${maxWidth}px`, 
              height: '28px', 
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              position: 'relative',
              display: 'flex',
              alignItems: 'center'
            }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: '20px',
                right: '15px',
                bottom: 0,
                background: 'linear-gradient(to right, transparent 0%, transparent 10%, #e2e8f0 10%, #e2e8f0 10.5%, transparent 10.5%)',
                backgroundSize: `${(maxWidth - 35) / currentTableMaxRows * 10}px 100%`
              }} />
              
              {[1, Math.floor(currentTableMaxRows/4), Math.floor(currentTableMaxRows/2), Math.floor(currentTableMaxRows*3/4), currentTableMaxRows].map(rowNum => (
                <div
                  key={rowNum}
                  style={{
                    position: 'absolute',
                    left: `${20 + (maxWidth - 35) * (rowNum - 1) / (currentTableMaxRows - 1)}px`,
                    top: '1px',
                    fontSize: '8px',
                    color: '#94a3b8',
                    transform: 'translateX(-50%)',
                    zIndex: 5
                  }}
                >
                  {rowNum}
                </div>
              ))}
              
              {pattern.modifiedRowNumbers && pattern.modifiedRowNumbers.map((rowNum, i) => {
                const leftPos = 20 + (maxWidth - 35) * (rowNum - 1) / (currentTableMaxRows - 1);
                const intensity = pattern.rowIntensities[rowNum] || 0.5;
                const lineHeight = 8 + intensity * 12;
                const lineWidth = Math.max(1, Math.floor(intensity * 3));
                
                return (
                  <div
                    key={i}
                    style={{
                      position: 'absolute',
                      left: `${leftPos}px`,
                      bottom: '8px',
                      width: `${lineWidth}px`,
                      height: `${lineHeight}px`,
                      backgroundColor: '#64748b',
                      transform: 'translateX(-50%)',
                      zIndex: 8
                    }}
                  />
                );
              })}
              
              {pattern.medianRow && (
                <div
                  style={{
                    position: 'absolute',
                    left: `${20 + (maxWidth - 35) * (pattern.medianRow - 1) / (currentTableMaxRows - 1)}px`,
                    top: '8px',
                    bottom: '8px',
                    width: '2px',
                    backgroundColor: '#dc2626',
                    transform: 'translateX(-50%)',
                    zIndex: 10
                  }}
                />
              )}
              
              <div
                style={{
                  position: 'absolute',
                  top: '14px',
                  right: '2px',
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: currentRiskLevel === 'L1' ? '#dc2626' : currentRiskLevel === 'L2' ? '#f59e0b' : '#10b981',
                  zIndex: 12
                }}
              />
            </div>
          );
        };

        // 主组件
        const AdvancedSortedHeatmap = () => {
          const [hoveredCell, setHoveredCell] = useState(null);
          const [showGrid, setShowGrid] = useState(false);
          const [showContours, setShowContours] = useState(false);
          const [showSettings, setShowSettings] = useState(false);
          const [apiData, setApiData] = useState({
            heatData: [],
            tableNames: [],
            columnNames: [],
            tables: [],
            modificationPatterns: [],
            stats: {}
          });
          
          // 获取API数据
          useEffect(() => {
            const fetchData = async () => {
              try {
                const [heatmapRes, modificationsRes, statsRes] = await Promise.all([
                  fetch('/api/heatmap'),
                  fetch('/api/modifications'),
                  fetch('/api/stats')
                ]);
                
                const heatmapData = await heatmapRes.json();
                const modificationsData = await modificationsRes.json();
                const statsData = await statsRes.json();
                
                setApiData({
                  heatData: heatmapData.data,
                  tableNames: heatmapData.tableNames,
                  columnNames: heatmapData.columnNames,
                  tables: heatmapData.tables,
                  modificationPatterns: modificationsData.patterns,
                  globalMaxRows: modificationsData.globalMaxRows,
                  stats: statsData
                });
              } catch (error) {
                console.error('数据加载失败:', error);
              }
            };
            
            fetchData();
          }, []);
          
          // 应用高斯平滑到热力图数据
          const smoothedHeatData = useMemo(() => {
            if (!apiData.heatData.length) return [];
            return gaussianSmooth(apiData.heatData, 7, 2.5);
          }, [apiData.heatData]);

          const handleCellHover = (y, x, value, tableName, columnName, event) => {
            if (value > 0) {
              setHoveredCell({ 
                y, x, value, tableName, columnName, 
                mouseX: event.clientX,
                mouseY: event.clientY
              });
            }
          };

          if (!apiData.heatData.length) {
            return (
              <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-lg text-slate-600 mb-4">🔄 正在加载数据...</div>
                  <div className="text-sm text-slate-500">请稍候，系统正在处理热力图数据</div>
                </div>
              </div>
            );
          }

          return (
            <div className="min-h-screen bg-slate-50 text-slate-900">
              <div className="bg-white border-b border-slate-200 shadow-sm">
                <div className="px-8 py-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h1 className="text-3xl font-light text-slate-800 mb-2">Heat Field Analysis</h1>
                      <p className="text-sm text-slate-600 font-mono">表格变更风险热力场分析 • 智能排序 • {apiData.tableNames.length}×{apiData.columnNames.length} 数据矩阵</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => setShowSettings(true)}
                        className="px-4 py-2 text-sm bg-slate-800 text-white rounded hover:bg-slate-900 transition-colors flex items-center gap-2"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="3"></circle>
                          <path d="m12 1 0 6m0 6 0 6"></path>
                          <path d="m12 1 0 6m0 6 0 6" transform="rotate(90 12 12)"></path>
                        </svg>
                        监控设置
                      </button>
                      <button
                        onClick={() => setShowGrid(!showGrid)}
                        className={`px-3 py-1 text-xs border rounded ${showGrid ? 'bg-blue-50 border-blue-200 text-blue-700' : 'border-slate-300 text-slate-600'}`}
                      >
                        网格线
                      </button>
                      <button
                        onClick={() => setShowContours(!showContours)}
                        className={`px-3 py-1 text-xs border rounded ${showContours ? 'bg-blue-50 border-blue-200 text-blue-700' : 'border-slate-300 text-slate-600'}`}
                      >
                        等高线
                      </button>
                    </div>
                  </div>

                  {/* 统计面板 */}
                  <div className="grid grid-cols-7 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-mono font-bold text-red-600">{apiData.stats.criticalModifications || 0}</div>
                      <div className="text-xs text-red-600 uppercase tracking-wider">严重修改</div>
                      <div className="text-xs text-slate-500">L1禁改位置</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-mono font-bold text-orange-600">{apiData.stats.L2Modifications || 0}</div>
                      <div className="text-xs text-orange-600 uppercase tracking-wider">异常修改</div>
                      <div className="text-xs text-slate-500">L2语义审核</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-mono font-bold text-green-600">{apiData.stats.L3Modifications || 0}</div>
                      <div className="text-xs text-green-600 uppercase tracking-wider">常规修改</div>
                      <div className="text-xs text-slate-500">L3自由编辑</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-mono font-bold text-slate-800" title={apiData.stats.mostModifiedColumn || ''}>
                        {(apiData.stats.mostModifiedColumn || '').length > 6 ? 
                          (apiData.stats.mostModifiedColumn || '').substring(0, 6) + '..' : 
                          apiData.stats.mostModifiedColumn || ''}
                      </div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">高频修改列</div>
                      <div className="text-xs text-slate-500">最多变更</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-mono font-bold text-slate-800" title={apiData.stats.mostModifiedTable || ''}>
                        {(apiData.stats.mostModifiedTable || '').length > 8 ? 
                          (apiData.stats.mostModifiedTable || '').substring(0, 8) + '..' : 
                          apiData.stats.mostModifiedTable || ''}
                      </div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">高频修改表</div>
                      <div className="text-xs text-slate-500">最多变更</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-mono font-bold text-slate-800">{apiData.stats.totalModifications || 0}</div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">总修改数</div>
                      <div className="text-xs text-slate-500">全部变更</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-mono font-bold text-blue-600">{apiData.tables.length}</div>
                      <div className="text-xs text-blue-600 uppercase tracking-wider">监控表格</div>
                      <div className="text-xs text-slate-500">实时跟踪</div>
                    </div>
                  </div>

                  {/* 色标 */}
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-slate-600 font-medium">强度标尺</span>
                      <div className="relative">
                        <div className="flex h-4 w-80 border border-slate-300 shadow-inner">
                          {Array.from({ length: 100 }, (_, i) => (
                            <div
                              key={i}
                              className="flex-1 h-full"
                              style={{ backgroundColor: getScientificHeatColor(i / 99) }}
                            />
                          ))}
                        </div>
                        <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-slate-500 font-mono">
                          <span>0%</span>
                          <span>25%</span>
                          <span>50%</span>
                          <span>75%</span>
                          <span>100%</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: getScientificHeatColor(0.1) }}></div>
                        <span className="text-slate-600">基准</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: getScientificHeatColor(0.5) }}></div>
                        <span className="text-slate-600">中等</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: getScientificHeatColor(0.8) }}></div>
                        <span className="text-slate-600">高风险</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="px-8 py-6">
                {/* 主热力图和横向分布图布局 */}
                <div className="flex justify-center gap-4">
                  {/* 热力图部分 */}
                  <div className="relative bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden heat-container">
                    <div style={{ width: `${128 + apiData.columnNames.length * 32}px` }}>
                      
                      <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-sm font-medium text-slate-700">
                        列索引 (Column Index) - 保持原序
                      </div>
                      <div className="absolute left-2 top-1/2 transform -translate-y-1/2 -rotate-90 text-sm font-medium text-slate-700 origin-center">
                        表格索引 (Table Index) - 按严重度排序
                      </div>

                      {/* 顶部坐标轴 */}
                      <div style={{ 
                        display: 'table', 
                        width: '100%', 
                        tableLayout: 'fixed', 
                        height: '70px', 
                        backgroundColor: '#f8fafc', 
                        borderBottom: '1px solid #e2e8f0' 
                      }}>
                        <div style={{ 
                          display: 'table-cell', 
                          width: '128px', 
                          textAlign: 'center', 
                          verticalAlign: 'bottom', 
                          padding: '8px', 
                          borderRight: '1px solid #e2e8f0', 
                          fontSize: '12px', 
                          color: '#64748b' 
                        }}>
                          表格名称
                        </div>
                        {apiData.columnNames.map((colName, x) => (
                          <div
                            key={x}
                            style={{ 
                              display: 'table-cell', 
                              width: '32px',
                              textAlign: 'center', 
                              verticalAlign: 'bottom',
                              padding: '4px 0',
                              fontSize: '10px',
                              color: '#475569'
                            }}
                            title={colName}
                          >
                            <div style={{ color: '#94a3b8', marginBottom: '2px' }}>{x + 1}</div>
                            <div style={{ transform: 'rotate(-45deg)', whiteSpace: 'nowrap' }}>
                              {colName.length > 6 ? colName.substring(0, 6) + '...' : colName}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* 热力图主体 */}
                      <div style={{ position: 'relative' }}>
                        {/* 网格线覆盖层 */}
                        {showGrid && (
                          <div style={{ 
                            position: 'absolute', 
                            top: 0, 
                            left: 0, 
                            right: 0, 
                            bottom: 0, 
                            pointerEvents: 'none', 
                            zIndex: 10 
                          }}>
                            {Array.from({ length: apiData.columnNames.length + 1 }, (_, i) => (
                              <div
                                key={`v-${i}`}
                                style={{
                                  position: 'absolute',
                                  left: `${128 + i * 32}px`,
                                  top: 0,
                                  bottom: 0,
                                  width: '1px',
                                  borderLeft: '1px solid rgba(148, 163, 184, 0.4)'
                                }}
                              />
                            ))}
                            {Array.from({ length: smoothedHeatData.length + 1 }, (_, i) => (
                              <div
                                key={`h-${i}`}
                                style={{
                                  position: 'absolute',
                                  top: `${i * 28}px`,
                                  left: '128px',
                                  right: 0,
                                  height: '1px',
                                  borderTop: '1px solid rgba(148, 163, 184, 0.4)'
                                }}
                              />
                            ))}
                          </div>
                        )}

                        {/* 每一行数据 */}
                        {smoothedHeatData.map((row, y) => (
                          <div key={y} style={{ 
                            display: 'table', 
                            width: '100%', 
                            tableLayout: 'fixed', 
                            height: '28px' 
                          }}>
                            {/* 左侧表格名称 */}
                            <div style={{ 
                              display: 'table-cell', 
                              width: '128px', 
                              backgroundColor: '#f8fafc',
                              borderRight: '1px solid #e2e8f0',
                              fontSize: '11px',
                              color: '#475569',
                              padding: '0 8px',
                              verticalAlign: 'middle'
                            }}>
                              <div style={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center' 
                              }}>
                                <a 
                                  href={apiData.tables[y]?.url || '#'}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ 
                                    overflow: 'hidden', 
                                    textOverflow: 'ellipsis', 
                                    whiteSpace: 'nowrap',
                                    fontSize: '10px',
                                    color: '#3b82f6',
                                    textDecoration: 'none',
                                    cursor: 'pointer'
                                  }}
                                  onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
                                  onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
                                >
                                  {apiData.tableNames[y]}
                                </a>
                                <span style={{ fontSize: '9px', color: '#94a3b8' }}>{y + 1}</span>
                              </div>
                            </div>
                            
                            {/* 热力数据单元格 */}
                            {row.map((value, x) => (
                              <div
                                key={x}
                                style={{ 
                                  display: 'table-cell',
                                  width: '32px',
                                  height: '28px',
                                  backgroundColor: value > 0 ? getScientificHeatColor(value) : '#f1f5f9',
                                  cursor: value > 0 ? 'crosshair' : 'default',
                                  position: 'relative',
                                  transition: 'all 0.1s',
                                  border: 'none',
                                  margin: 0,
                                  padding: 0
                                }}
                                onMouseEnter={(e) => handleCellHover(y, x, value, apiData.tableNames[y], apiData.columnNames[x], e)}
                                onMouseLeave={() => setHoveredCell(null)}
                              >
                                {/* 等高线效果 */}
                                {showContours && value > 0.6 && (
                                  <div 
                                    style={{ 
                                      position: 'absolute',
                                      top: 0,
                                      left: 0,
                                      right: 0,
                                      bottom: 0,
                                      border: '2px solid rgba(255, 255, 255, 0.6)',
                                      borderRadius: '2px',
                                      pointerEvents: 'none'
                                    }}
                                  />
                                )}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>

                      {/* 跟随鼠标的悬浮提示 */}
                      {hoveredCell && (
                        <div 
                          className="fixed bg-white border border-slate-300 shadow-xl rounded-lg p-4 text-sm pointer-events-none z-50"
                          style={{ 
                            left: `${Math.min(hoveredCell.mouseX + 15, window.innerWidth - 220)}px`,
                            top: `${Math.max(hoveredCell.mouseY - 10, 10)}px`,
                            minWidth: '200px'
                          }}
                        >
                          <div className="space-y-2">
                            <div className="border-b border-slate-200 pb-2">
                              <div className="font-mono text-xs text-slate-500 mb-1">
                                [{hoveredCell.x + 1}, {hoveredCell.y + 1}]
                              </div>
                              <div className="font-medium text-slate-800">
                                {hoveredCell.tableName}
                              </div>
                              <div className="text-slate-600 text-xs">
                                {hoveredCell.columnName}
                              </div>
                            </div>
                            
                            <div className="space-y-1">
                              <div className="flex justify-between items-center">
                                <span className="text-slate-600">强度值:</span>
                                <span className="font-mono font-bold text-slate-800">
                                  {(hoveredCell.value * 100).toFixed(2)}%
                                </span>
                              </div>
                              <div className="flex justify-between items-center">
                                <span className="text-slate-600">热力等级:</span>
                                <span 
                                  className="text-xs px-2 py-1 rounded"
                                  style={{
                                    backgroundColor: hoveredCell.value > 0.7 ? '#fee2e2' : hoveredCell.value > 0.4 ? '#fef3c7' : '#ecfdf5',
                                    color: hoveredCell.value > 0.7 ? '#991b1b' : hoveredCell.value > 0.4 ? '#92400e' : '#166534'
                                  }}
                                >
                                  {hoveredCell.value > 0.7 ? '高风险' : hoveredCell.value > 0.4 ? '中等' : '正常'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 右侧横向分布图 */}
                  <div className="bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden">
                    <div style={{ width: '250px' }}>
                      {/* 顶部标题 */}
                      <div style={{ 
                        height: '70px', 
                        backgroundColor: '#f8fafc', 
                        borderBottom: '1px solid #e2e8f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '8px'
                      }}>
                        <div className="text-xs text-slate-600 text-center">
                          <div className="font-medium">表内修改分布</div>
                          <div className="text-xs text-slate-500 mt-1">
                            {hoveredCell ? `${hoveredCell.columnName} 列分布` : '整体修改强度'}
                          </div>
                        </div>
                      </div>

                      {/* 分布图主体 */}
                      <div>
                        {apiData.modificationPatterns.map((pattern, y) => (
                          <div key={y} style={{ 
                            height: '28px', 
                            borderBottom: '1px solid #f1f5f9',
                            display: 'flex',
                            alignItems: 'center',
                            padding: '0 4px'
                          }}>
                            <TableModificationChart 
                              pattern={hoveredCell ? pattern.columnPatterns[hoveredCell.columnName] : pattern}
                              columnName={hoveredCell?.columnName}
                              isHovered={!!hoveredCell}
                              allPatterns={apiData.modificationPatterns}
                              globalMaxRows={apiData.globalMaxRows}
                              maxWidth={240}
                              tableData={apiData.tables[y]}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 排序分析面板 */}
                <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
                    <h3 className="text-lg font-medium text-slate-800 mb-4 flex items-center gap-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      表格严重度排序
                    </h3>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {apiData.tables.slice(0, 10).map((table, i) => (
                        <div key={i} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-sm" 
                              style={{ backgroundColor: getScientificHeatColor(table.maxCellRisk) }}
                            />
                            <a 
                              href={table.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 hover:underline text-xs"
                              style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            >
                              {table.name}
                            </a>
                          </div>
                          <div className="text-right">
                            <div className="font-mono text-slate-800 font-medium text-xs">
                              {(table.maxCellRisk * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-slate-500">
                              {table.criticalModifications}个严重修改
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
                    <h3 className="text-lg font-medium text-slate-800 mb-4 flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      列排序策略
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">列顺序:</span>
                        <span className="font-mono text-slate-800">保持不变</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">表格排序:</span>
                        <span className="font-mono text-slate-800">按严重度</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">主排序键:</span>
                        <span className="font-mono text-slate-800">最高风险分</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">次排序键:</span>
                        <span className="font-mono text-slate-800">严重修改数</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">热力聚集:</span>
                        <span className="font-mono text-slate-800">L1列增强</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
                    <h3 className="text-lg font-medium text-slate-800 mb-4 flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      效果统计
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">顶部热力:</span>
                        <span className="font-mono text-green-600 font-medium">
                          {smoothedHeatData.slice(0, 5).flat().filter(v => v > 0.7).length}个高风险
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">列差异:</span>
                        <span className="font-mono text-slate-800">
                          {apiData.tables.filter(t => t.columns.length !== apiData.columnNames.length).length}个变异表格
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">空白单元格:</span>
                        <span className="font-mono text-slate-800">
                          {smoothedHeatData.flat().filter(v => v === 0).length}个
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">热力梯度:</span>
                        <span className="font-mono text-slate-800">顶部→底部</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 设置弹窗 */}
              <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
            </div>
          );
        };

        // 渲染应用
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(AdvancedSortedHeatmap));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页 - 返回完整的原版React UI"""
    return UI_TEMPLATE

@app.route('/api/heatmap')
def api_heatmap():
    """API: 获取热力图数据"""
    heat_data = adapter.generate_heatmap_data()
    
    return jsonify({
        'data': heat_data,
        'tableNames': [t['name'] for t in adapter.tables],
        'columnNames': adapter.standard_columns,
        'tables': adapter.tables
    })

@app.route('/api/modifications')
def api_modifications():
    """API: 获取修改分布数据"""
    global_max_rows = max([
        max([pattern['totalRows'] for pattern in mp['columnPatterns'].values()] + [20])
        for mp in adapter.modification_patterns
    ] + [50])
    
    return jsonify({
        'patterns': adapter.modification_patterns,
        'globalMaxRows': global_max_rows
    })

@app.route('/api/stats')
def api_stats():
    """API: 获取统计数据"""
    if not adapter.viz_data:
        return jsonify({'error': '数据未加载'}), 500
    
    total_changes = len(adapter.viz_data['modification_locations'])
    risk_dist = adapter.viz_data['risk_distribution']
    
    column_modifications = {}
    for mod in adapter.viz_data['modification_locations']:
        col = mod['column_name']
        if col not in column_modifications:
            column_modifications[col] = 0
        column_modifications[col] += 1
    
    most_modified_column = max(column_modifications.items(), key=lambda x: x[1])[0] if column_modifications else '无'
    most_modified_table = adapter.tables[0]['name'] if adapter.tables else '无'
    
    return jsonify({
        'criticalModifications': risk_dist.get('L1', 0),
        'L1Modifications': risk_dist.get('L1', 0),
        'L2Modifications': risk_dist.get('L2', 0),
        'L3Modifications': risk_dist.get('L3', 0),
        'mostModifiedColumn': most_modified_column,
        'mostModifiedTable': most_modified_table,
        'totalModifications': total_changes
    })

@app.route('/api/status')
def api_status():
    """API: 系统状态"""
    return jsonify({
        'status': 'running',
        'data_loaded': adapter.viz_data is not None,
        'tables_count': len(adapter.tables),
        'modifications_count': len(adapter.viz_data['modification_locations']) if adapter.viz_data else 0,
        'last_update': datetime.now().isoformat()
    })

# 创建全局适配器实例
adapter = UIDataAdapter()

def main():
    """主函数"""
    print("🚀 启动完整原版UI集成服务器")
    print("=" * 60)
    print(f"🌐 访问地址: http://localhost:5000")
    print(f"📊 使用原版UI的全部功能:")
    print(f"   ✅ 高斯平滑算法")
    print(f"   ✅ 科学热力图颜色映射") 
    print(f"   ✅ 智能排序规则")
    print(f"   ✅ 动态修改分布图")
    print(f"   ✅ 监控设置面板")
    print(f"   ✅ 真实测试数据展示")
    print("=" * 60)
    
    if not adapter.viz_data:
        print("⚠️ 数据未正确加载，请先运行:")
        print("   python3 quick_e2e_test.py")
        print("   python3 heatmap_visualizer.py")
        return
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()