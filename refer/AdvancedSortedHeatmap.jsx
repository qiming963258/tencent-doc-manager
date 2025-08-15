import React, { useState, useMemo } from 'react';

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
    // 更深的血红色：从亮红到深血红
    const r = Math.floor(255 - t * 15); // 保持高红色值
    const g = Math.floor(255 - t * 235); // 大幅降低绿色值，最终接近20
    const b = Math.floor(50 - t * 40);   // 大幅降低蓝色值，最终接近10
    return `rgb(${r}, ${g}, ${b})`;
  }
};

// 设置弹窗组件
const SettingsModal = ({ isOpen, onClose }) => {
  const [tableLinks, setTableLinks] = useState('');
  const [cookieValue, setCookieValue] = useState('');
  
  const handleImportLinks = () => {
    const links = tableLinks.split('\n').filter(line => line.trim());
    console.log('导入的链接:', links);
    // 这里可以添加实际的导入逻辑
    alert(`成功导入 ${links.length} 个表格链接`);
  };
  
  const handleUpdateCookie = () => {
    console.log('更新Cookie:', cookieValue);
    // 这里可以添加实际的Cookie更新逻辑
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
        {/* 弹窗头部 */}
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
        
        {/* 弹窗内容 */}
        <div style={{ padding: '24px 32px' }}>
          {/* 表格链接导入 */}
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
                {tableLinks.split('\n').filter(line => line.trim()).length} 个链接待导入
              </span>
              <button
                onClick={handleImportLinks}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                导入链接
              </button>
            </div>
          </div>
          
          {/* Cookie设置 */}
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
          
          {/* 监控配置 */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-3">
              监控配置
            </label>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">检查频率:</span>
                <select className="text-slate-800 border border-slate-300 rounded px-2 py-1 text-xs">
                  <option>每5分钟</option>
                  <option>每15分钟</option>
                  <option>每30分钟</option>
                  <option>每小时</option>
                </select>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">告警阈值:</span>
                <select className="text-slate-800 border border-slate-300 rounded px-2 py-1 text-xs">
                  <option>L1级别修改</option>
                  <option>高风险修改</option>
                  <option>所有修改</option>
                </select>
              </div>
            </div>
          </div>
        </div>
        
        {/* 弹窗底部 */}
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

// 横向分布图组件 - 支持静态和悬浮两种模式
const TableModificationChart = ({ 
  pattern, 
  columnName, 
  isHovered = false, 
  allPatterns = [], 
  globalMaxRows = 50, 
  maxWidth = 300,
  tableData = null // 新增：当前表格的数据用于状态点
}) => {
  
  if (!isHovered) {
    // 静态模式：显示当前行的整体修改强度柱状图
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
        {/* 静态柱状图 */}
        <div
          style={{
            width: `${barWidth}px`,
            height: '16px',
            backgroundColor: intensity > 0.7 ? '#dc2626' : intensity > 0.4 ? '#f59e0b' : '#10b981',
            borderRadius: '2px'
          }}
        />
        {/* 强度数值 */}
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
  
  // 悬浮模式：显示该列所有表格的修改分布
  if (!pattern) {
    return (
      <div style={{ width: `${maxWidth}px`, height: '28px', backgroundColor: '#f1f5f9' }}>
      </div>
    );
  }

  // 使用当前表格的实际行数作为标尺最大值
  const currentTableMaxRows = pattern.totalRows || 20;
  
  // 获取当前表格在当前列的风险状态
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
      {/* 横向标尺背景 */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: '20px',
        right: '15px', // 给风险指示器留出空间
        bottom: 0,
        background: 'linear-gradient(to right, transparent 0%, transparent 10%, #e2e8f0 10%, #e2e8f0 10.5%, transparent 10.5%)',
        backgroundSize: `${(maxWidth - 35) / currentTableMaxRows * 10}px 100%`
      }} />
      
      {/* 行号标尺 - 基于当前表格的实际行数 */}
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
      
      {/* 当前表格的修改分布 */}
      {pattern.modifiedRowNumbers && pattern.modifiedRowNumbers.map((rowNum, i) => {
        const leftPos = 20 + (maxWidth - 35) * (rowNum - 1) / (currentTableMaxRows - 1);
        const intensity = pattern.rowIntensities[rowNum] || 0.5;
        const lineHeight = 8 + intensity * 12; // 8-20px高度
        const lineWidth = Math.max(1, Math.floor(intensity * 3)); // 1-3px宽度
        
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
      
      {/* 中位数红线 */}
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
      
      {/* 风险等级指示器 - 反映当前表格在当前列的状态 */}
      <div
        style={{
          position: 'absolute',
          top: '14px', // 移到中下位置
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

// 模拟真实表格数据，包含列差异
const generateRealisticTableData = () => {
  // 使用实际参考表格的列名（保持前19个，不编造新列名）
  const standardColumns = [
    '序号', '项目类型', '来源', '任务发起时间', '目标对齐', 
    '关键KR对齐', '具体计划内容', '邓总指导登记', '负责人', 
    '协助人', '监督人', '重要程度', '预计完成时间', '完成进度',
    '形成计划清单', '复盘时间', '对上汇报', '应用情况', '进度分析总结'
  ];

  // 列风险等级配置 - 基于文档中的分类（仅实际列名）
  const columnRiskLevels = {
    '序号': 'L3',           // 用户修正：序号属于L3
    '项目类型': 'L2',
    '来源': 'L1',           // 数据来源，绝对不能修改
    '任务发起时间': 'L1',   // 时间相关，绝对不能修改
    '目标对齐': 'L1',       // 用户特别强调，绝对不能修改
    '关键KR对齐': 'L1',     // 目标对齐相关，绝对不能修改
    '具体计划内容': 'L2',   // 计划内容，需要语义审核
    '邓总指导登记': 'L2',   // 指导意见，需要语义审核
    '负责人': 'L2',         // 人员管理，需要语义审核
    '协助人': 'L2',
    '监督人': 'L2',
    '重要程度': 'L1',       // 进度追踪，绝对不能修改
    '预计完成时间': 'L1',   // 时间相关，绝对不能修改
    '完成进度': 'L1',       // 进度追踪，绝对不能修改
    '形成计划清单': 'L2',   // 交付物，需要语义审核
    '复盘时间': 'L3',       // 用户修正：复盘时间属于L3
    '对上汇报': 'L3',       // 沟通汇报，可自由编辑
    '应用情况': 'L3',
    '进度分析总结': 'L3'    // 分析总结，可自由编辑
  };

  const tables = [];
  for (let i = 0; i < 30; i++) {
    // 真实的工作表名字
    const tableNames = [
      '项目管理主计划表', '销售目标跟踪表', '客户关系管理表', '产品研发进度表', 
      '人力资源配置表', '财务预算执行表', '市场营销活动表', '运营数据分析表',
      '供应链管理表', '质量控制记录表', '风险评估跟踪表', '绩效考核统计表',
      '培训计划执行表', '设备维护记录表', '合同管理明细表', '库存管理台账表',
      '客服工单处理表', '技术支持记录表', '投资决策分析表', '内控合规检查表',
      '战略规划执行表', '业务流程优化表', '数据安全监控表', '成本核算分析表',
      '招聘进度跟踪表', '项目验收评估表', '用户反馈汇总表', '竞品分析对比表',
      '渠道伙伴管理表', '知识产权管理表'
    ];
    
    const tableName = tableNames[i];
    const tableUrl = `https://docs.qq.com/sheet/table-${i + 1}`;
    
    let columns = [...standardColumns];
    
    // 随机移除1-2列来模拟真实的列差异
    if (Math.random() > 0.7) {
      const removeCount = Math.random() > 0.5 ? 1 : 2;
      for (let j = 0; j < removeCount; j++) {
        const removeIndex = Math.floor(Math.random() * columns.length);
        columns.splice(removeIndex, 1);
      }
    }

    // 计算表格的修改严重度
    let tableRiskSum = 0;
    let maxCellRisk = 0;
    let criticalModifications = 0;

    columns.forEach(col => {
      const riskLevel = columnRiskLevels[col] || 'L2';
      let cellRisk = 0;

      // 基于风险等级生成基础评分，加入更广泛的数值范围
      if (riskLevel === 'L1') {
        // L1列：添加一些超高风险数据
        if (Math.random() > 0.9) {
          cellRisk = 0.90 + Math.random() * 0.1; // 0.90-1.0 极高风险
        } else if (Math.random() > 0.8) {
          cellRisk = 0.85 + Math.random() * 0.15; // 0.85-1.0 高风险
        } else {
          cellRisk = 0.75 + Math.random() * 0.15; // 0.75-0.9 中高风险
        }
        if (Math.random() > 0.8) criticalModifications++; // L1列被修改是严重事件
      } else if (riskLevel === 'L2') {
        // L2列：保持中等范围但增加变化
        if (Math.random() > 0.95) {
          cellRisk = 0.80 + Math.random() * 0.15; // 少数高风险
        } else {
          cellRisk = 0.3 + Math.random() * 0.5; // 0.3-0.8 正常范围
        }
      } else { // L3
        // L3列：添加一些极低强度数据
        if (Math.random() > 0.85) {
          cellRisk = 0.05 + Math.random() * 0.05; // 0.05-0.1 极低风险
        } else {
          cellRisk = 0.1 + Math.random() * 0.2; // 0.1-0.3 正常范围
        }
      }

      tableRiskSum += cellRisk;
      maxCellRisk = Math.max(maxCellRisk, cellRisk);
    });

    const avgRisk = tableRiskSum / columns.length;

    tables.push({
      id: i,
      name: tableName,
      url: tableUrl,
      columns,
      avgRisk,
      maxCellRisk,
      criticalModifications,
      totalRisk: tableRiskSum,
      columnRiskLevels
    });
  }

  // 按修改严重程度排序表格：最严重的在顶部
  tables.sort((a, b) => {
    // 主要按最高风险分数排序
    if (Math.abs(a.maxCellRisk - b.maxCellRisk) > 0.05) {
      return b.maxCellRisk - a.maxCellRisk;
    }
    // 次要按严重修改数量排序
    if (a.criticalModifications !== b.criticalModifications) {
      return b.criticalModifications - a.criticalModifications;
    }
    // 最后按平均风险排序
    return b.avgRisk - a.avgRisk;
  });

  return { tables, standardColumns, columnRiskLevels };
};

// 生成表格内部修改分布数据
const generateTableModificationPatterns = (tables, columnNames) => {
  // 首先确定全局最大行数用于标尺
  const globalMaxRows = Math.max(...tables.map(() => 10 + Math.floor(Math.random() * 40)));
  
  const patterns = tables.map(table => {
    const columnPatterns = {};
    
    table.columns.forEach(colName => {
      // 模拟表格内部行数（每个表格有10-50行数据）
      const totalRows = 10 + Math.floor(Math.random() * 40);
      // 模拟被修改的行数（基于列风险等级）
      const riskLevel = table.columnRiskLevels[colName] || 'L2';
      let modificationRate = 0;
      
      if (riskLevel === 'L1') {
        modificationRate = 0.05 + Math.random() * 0.15; // L1列修改率低但影响大
      } else if (riskLevel === 'L2') {
        modificationRate = 0.1 + Math.random() * 0.3; // L2列修改率中等
      } else {
        modificationRate = 0.2 + Math.random() * 0.5; // L3列修改率高但影响小
      }
      
      const modifiedRows = Math.floor(totalRows * modificationRate);
      
      // 生成修改位置分布（基于实际行号而非相对位置）
      const modifiedRowNumbers = [];
      const patterns = ['top_heavy', 'bottom_heavy', 'middle_heavy', 'scattered', 'clustered'];
      const pattern = patterns[Math.floor(Math.random() * patterns.length)];
      
      for (let i = 0; i < modifiedRows; i++) {
        let rowNumber;
        switch (pattern) {
          case 'top_heavy':
            rowNumber = Math.floor(Math.random() * Math.ceil(totalRows * 0.4)) + 1; // 前40%行
            break;
          case 'bottom_heavy':
            rowNumber = Math.floor(Math.random() * Math.ceil(totalRows * 0.4)) + Math.ceil(totalRows * 0.6); // 后40%行
            break;
          case 'middle_heavy':
            rowNumber = Math.floor(Math.random() * Math.ceil(totalRows * 0.4)) + Math.ceil(totalRows * 0.3); // 中间40%行
            break;
          case 'scattered':
            rowNumber = Math.floor(Math.random() * totalRows) + 1; // 均匀分布
            break;
          case 'clustered':
            const center = Math.floor(totalRows / 2);
            const offset = Math.floor((Math.random() - 0.5) * totalRows * 0.3);
            rowNumber = Math.max(1, Math.min(totalRows, center + offset));
            break;
          default:
            rowNumber = Math.floor(Math.random() * totalRows) + 1;
        }
        if (!modifiedRowNumbers.includes(rowNumber)) {
          modifiedRowNumbers.push(rowNumber);
        }
      }
      
      modifiedRowNumbers.sort((a, b) => a - b);
      
      // 计算每行的修改强度
      const rowIntensities = {};
      modifiedRowNumbers.forEach(rowNum => {
        rowIntensities[rowNum] = 0.3 + Math.random() * 0.7; // 0.3-1.0的修改强度
      });
      
      columnPatterns[colName] = {
        totalRows,
        modifiedRows,
        modificationRate,
        modifiedRowNumbers,
        rowIntensities,
        pattern,
        riskLevel,
        medianRow: modifiedRowNumbers.length > 0 ? modifiedRowNumbers[Math.floor(modifiedRowNumbers.length / 2)] : Math.floor(totalRows / 2)
      };
    });
    
    // 计算当前行的整体修改强度（用于静态柱状图）
    const rowOverallIntensity = Object.values(columnPatterns).reduce((sum, pattern) => {
      return sum + pattern.modificationRate * (pattern.riskLevel === 'L1' ? 3 : pattern.riskLevel === 'L2' ? 2 : 1);
    }, 0) / Object.keys(columnPatterns).length;
    
    return {
      tableId: table.id,
      tableName: table.name,
      columnPatterns,
      rowOverallIntensity // 用于静态显示
    };
  });
  
  return { patterns, globalMaxRows };
};

// 生成排序后的热力图数据
const generateSortedHeatData = () => {
  const { tables, standardColumns } = generateRealisticTableData();
  const rows = tables.length;
  const cols = standardColumns.length;
  
  // 创建数据矩阵，保持列顺序不变
  const baseData = Array(rows).fill(null).map((_, y) => 
    Array(cols).fill(null).map((_, x) => {
      const table = tables[y];
      const columnName = standardColumns[x];
      
      // 如果表格包含这一列，计算风险分数
      if (table.columns.includes(columnName)) {
        const riskLevel = table.columnRiskLevels[columnName] || 'L2';
        let score = 0;

        if (riskLevel === 'L1') {
          score = 0.85 + Math.random() * 0.15;
        } else if (riskLevel === 'L2') {
          score = 0.3 + Math.random() * 0.5;
        } else {
          score = 0.1 + Math.random() * 0.2;
        }

        // 为顶部严重的表格增强分数
        if (y < 5) {
          score *= (1 + (5 - y) * 0.1);
        }

        return Math.max(0.1, Math.min(1, score));
      } else {
        return 0; // 表格中不存在此列
      }
    })
  );
  
  // 添加热力聚集效果：在严重的列上增加额外的热源（更新列索引为19列）
  const criticalColumns = [2, 3, 4, 5, 11, 12, 13]; // 来源、任务发起时间、目标对齐、关键KR对齐、重要程度、预计完成时间、完成进度
  criticalColumns.forEach(colIndex => {
    for (let row = 0; row < Math.min(10, rows); row++) {
      if (baseData[row][colIndex] > 0) {
        baseData[row][colIndex] = Math.min(1, baseData[row][colIndex] * 1.3);
      }
    }
  });

  // 应用高斯平滑
  const smoothed = gaussianSmooth(baseData, 7, 2.5);
  
  return {
    data: smoothed,
    tableNames: tables.map(t => t.name),
    columnNames: standardColumns,
    tables
  };
};

const AdvancedSortedHeatmap = () => {
  const [hoveredCell, setHoveredCell] = useState(null);
  const [showGrid, setShowGrid] = useState(false);
  const [showContours, setShowContours] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // 添加修改模式数据生成
  const { data: heatData, tableNames, columnNames, tables } = useMemo(() => generateSortedHeatData(), []);
  const { patterns: modificationPatterns, globalMaxRows } = useMemo(() => generateTableModificationPatterns(tables, columnNames), [tables, columnNames]);
  
  // 计算真实有意义的统计数据
  const meaningfulStats = useMemo(() => {
    const allCellData = [];
    const columnModifications = {};
    const tableModifications = {};
    
    // 收集所有单元格数据
    heatData.forEach((row, tableIndex) => {
      const table = tables[tableIndex];
      tableModifications[table.name] = { L1: 0, L2: 0, L3: 0, total: 0 };
      
      row.forEach((value, colIndex) => {
        if (value > 0) {
          const columnName = columnNames[colIndex];
          const riskLevel = table.columnRiskLevels[columnName] || 'L2';
          
          // 统计列修改
          if (!columnModifications[columnName]) {
            columnModifications[columnName] = { count: 0, totalIntensity: 0, riskLevel };
          }
          columnModifications[columnName].count++;
          columnModifications[columnName].totalIntensity += value;
          
          // 统计表格修改
          tableModifications[table.name][riskLevel]++;
          tableModifications[table.name].total++;
          
          allCellData.push({ value, riskLevel, tableName: table.name, columnName });
        }
      });
    });
    
    // 计算各级别修改数量
    const L1Modifications = allCellData.filter(d => d.riskLevel === 'L1').length;
    const L2Modifications = allCellData.filter(d => d.riskLevel === 'L2').length;
    const L3Modifications = allCellData.filter(d => d.riskLevel === 'L3').length;
    
    // 找出修改最多的列
    const mostModifiedColumn = Object.entries(columnModifications)
      .sort(([,a], [,b]) => b.count - a.count)[0];
    
    // 找出修改最多的表格
    const mostModifiedTable = Object.entries(tableModifications)
      .sort(([,a], [,b]) => b.total - a.total)[0];
    
    // 计算严重修改（L1级别且高强度）
    const criticalModifications = allCellData.filter(d => d.riskLevel === 'L1' && d.value > 0.8).length;
    
    return {
      criticalModifications, // 严重修改
      L1Modifications,       // L1级别修改
      L2Modifications,       // L2级别修改  
      L3Modifications,       // L3级别修改
      mostModifiedColumn: mostModifiedColumn ? mostModifiedColumn[0] : '无',
      mostModifiedTable: mostModifiedTable ? mostModifiedTable[0] : '无',
      totalModifications: allCellData.length
    };
  }, [heatData, tables, columnNames]);

  const handleCellHover = (y, x, value, tableName, columnName, event) => {
    if (value > 0) {
      // 获取鼠标的实际坐标位置
      setHoveredCell({ 
        y, x, value, tableName, columnName, 
        mouseX: event.clientX,
        mouseY: event.clientY
      });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* 保持原有的顶部面板 */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-light text-slate-800 mb-2">Heat Field Analysis</h1>
              <p className="text-sm text-slate-600 font-mono">表格变更风险热力场分析 • 智能排序 • {tableNames.length}×{columnNames.length} 数据矩阵</p>
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

          {/* 有意义的统计面板 */}
          <div className="grid grid-cols-7 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-red-600">{meaningfulStats.criticalModifications}</div>
              <div className="text-xs text-red-600 uppercase tracking-wider">严重修改</div>
              <div className="text-xs text-slate-500">L1禁改位置</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-orange-600">{meaningfulStats.L2Modifications}</div>
              <div className="text-xs text-orange-600 uppercase tracking-wider">异常修改</div>
              <div className="text-xs text-slate-500">L2语义审核</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-green-600">{meaningfulStats.L3Modifications}</div>
              <div className="text-xs text-green-600 uppercase tracking-wider">常规修改</div>
              <div className="text-xs text-slate-500">L3自由编辑</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-mono font-bold text-slate-800" title={meaningfulStats.mostModifiedColumn}>
                {meaningfulStats.mostModifiedColumn.length > 6 ? 
                  meaningfulStats.mostModifiedColumn.substring(0, 6) + '..' : 
                  meaningfulStats.mostModifiedColumn}
              </div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">高频修改列</div>
              <div className="text-xs text-slate-500">最多变更</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-mono font-bold text-slate-800" title={meaningfulStats.mostModifiedTable}>
                {meaningfulStats.mostModifiedTable.length > 8 ? 
                  meaningfulStats.mostModifiedTable.substring(0, 8) + '..' : 
                  meaningfulStats.mostModifiedTable}
              </div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">高频修改表</div>
              <div className="text-xs text-slate-500">最多变更</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-slate-800">{meaningfulStats.totalModifications}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">总修改数</div>
              <div className="text-xs text-slate-500">全部变更</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-blue-600">{tables.length}</div>
              <div className="text-xs text-blue-600 uppercase tracking-wider">监控表格</div>
              <div className="text-xs text-slate-500">实时跟踪</div>
            </div>
          </div>

          {/* 保持原有的色标 */}
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
            {/* 调整宽度：128px(左标签) + 19×32px(数据列) = 736px */}
            <div style={{ width: `${128 + columnNames.length * 32}px` }}>
              
              {/* 保持原有的坐标轴标签 */}
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-sm font-medium text-slate-700">
                列索引 (Column Index) - 保持原序
              </div>
              <div className="absolute left-2 top-1/2 transform -translate-y-1/2 -rotate-90 text-sm font-medium text-slate-700 origin-center">
                表格索引 (Table Index) - 按严重度排序
              </div>

              {/* 保持原有的顶部坐标轴 */}
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
                {columnNames.map((colName, x) => (
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
                    {Array.from({ length: columnNames.length + 1 }, (_, i) => (
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
                    {Array.from({ length: heatData.length + 1 }, (_, i) => (
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
                {heatData.map((row, y) => (
                  <div key={y} style={{ 
                    display: 'table', 
                    width: '100%', 
                    tableLayout: 'fixed', 
                    height: '28px' 
                  }}>
                    {/* 左侧表格名称 - 可点击的链接 */}
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
                          href={tables[y]?.url || '#'}
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
                          {tableNames[y]}
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
                        onMouseEnter={(e) => handleCellHover(y, x, value, tableNames[y], columnNames[x], e)}
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
                        <span className="text-slate-600">相对位置:</span>
                        <span className="font-mono text-xs text-slate-600">
                          {meaningfulStats.totalModifications > 0 ? (hoveredCell.value * 100).toFixed(1) : 0}%
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
            <div style={{ width: '250px' }}> {/* 大约是热力图宽度的1/3 */}
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
                {modificationPatterns.map((pattern, y) => (
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
                      allPatterns={modificationPatterns}
                      globalMaxRows={globalMaxRows}
                      maxWidth={240}
                      tableData={tables[y]} // 传入当前表格数据
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 新增排序分析面板 */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-medium text-slate-800 mb-4 flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              表格严重度排序
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {tables.slice(0, 10).map((table, i) => (
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
                  {heatData.slice(0, 5).flat().filter(v => v > 0.7).length}个高风险
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">列差异:</span>
                <span className="font-mono text-slate-800">
                  {tables.filter(t => t.columns.length !== columnNames.length).length}个变异表格
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">空白单元格:</span>
                <span className="font-mono text-slate-800">
                  {heatData.flat().filter(v => v === 0).length}个
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">热力梯度:</span>
                <span className="font-mono text-slate-800">顶部→底部</span>
              </div>
            </div>
          </div>
        </div>

        {/* 更新解决方案说明 */}
        <div className="mt-6 bg-slate-50 border border-slate-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-slate-800 mb-3">增强功能特性</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-600 leading-relaxed">
            <div>
              <strong className="text-slate-800">1. 智能状态识别:</strong> 状态点反映每个表格在特定列的真实风险等级，动态显示L1/L2/L3状态。
            </div>
            <div>
              <strong className="text-slate-800">2. 实用统计数据:</strong> 显示严重修改、异常修改、常规修改数量，以及修改最频繁的列和表格。
            </div>
            <div>
              <strong className="text-slate-800">3. 监控设置面板:</strong> 支持批量导入腾讯文档链接，配置Cookie认证和监控参数。
            </div>
            <div>
              <strong className="text-slate-800">4. 个性化标尺:</strong> 每个表格使用自己的行数生成精确的修改位置标尺。
            </div>
          </div>
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <div className="text-sm text-blue-800">
              <strong>统计数据说明:</strong> 
              <ul className="mt-2 space-y-1 text-xs">
                <li>• <strong>严重修改：</strong>L1级别禁止修改位置的变更，需要立即关注</li>
                <li>• <strong>异常修改：</strong>L2级别需要语义审核的变更，需要人工确认</li>
                <li>• <strong>常规修改：</strong>L3级别可自由编辑的变更，仅作记录</li>
                <li>• <strong>热点识别：</strong>自动识别修改最频繁的列和表格，便于重点监控</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 设置弹窗 */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
};

export default AdvancedSortedHeatmap;