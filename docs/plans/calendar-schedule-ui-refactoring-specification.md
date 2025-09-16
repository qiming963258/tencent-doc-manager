# 腾讯文档监控系统 - 日历调度UI重构技术规格文档

## 📋 项目概述

本文档详细记录了腾讯文档智能监控系统中**日历调度功能**的完整重构过程，包括时间管理逻辑、UI界面简化、前后端集成等技术细节。

**重构目标**: 从复杂的智能调度系统简化为直观的双按钮控制界面。

---

## 🕐 时间管理核心逻辑

### 原始需求分析
用户要求将原本的**周一/周四**调度时间点调整为**周二/周四/周六**三个关键时间节点，并实现差异化执行逻辑。

### 时间点重构详情

#### 1. 调度时间节点 (WeekTimeManager)

```python
# /root/projects/tencent-doc-manager/production/core_modules/week_time_manager.py

def get_baseline_strategy(self) -> Tuple[str, str, int]:
    """
    严格的基准版选择策略
    - 周一全天 OR 周二12点前: 使用上周基准版
    - 周二12点后 OR 周三到周六: 使用本周基准版
    """
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=周一, 1=周二...
    hour = now.hour
    
    if weekday < 1 or (weekday == 1 and hour < 12):
        target_week = week_info[1] - 1  # 上周
        return "previous_week", f"使用上周W{target_week}基准版", target_week
    else:
        target_week = week_info[1]  # 本周
        return "current_week", f"使用本周W{target_week}基准版", target_week
```

#### 2. 三个关键时间节点

| 时间节点 | 具体时间 | 执行逻辑 | 功能说明 |
|---------|----------|----------|----------|
| 🔴 **基线时间** | 周二 12:00 | 仅下载CSV | 下载腾讯文档最新数据，不进行比对分析，UI热力图不刷新 |
| 🟡 **周中统计** | 周四 09:00 | 下载+比对+刷新 | 完整工作流：下载→比对分析→生成热力图→UI刷新 |
| 🔵 **周末统计** | 周六 19:00 | 下载+比对+刷新 | 完整工作流：下载→比对分析→生成热力图→UI刷新 |

#### 3. 配置文件结构

```json
// /root/projects/tencent-doc-manager/config/schedule_tasks.json
{
  "preset_tasks": [
    {
      "task_id": "weekly_baseline_download",
      "schedule": {
        "expression": "weekly:tuesday:12:00",
        "timezone": "Asia/Shanghai"
      },
      "options": {
        "task_type": "baseline_download",
        "auto_set_baseline": true
      }
    },
    {
      "task_id": "weekly_midweek_update", 
      "schedule": {
        "expression": "weekly:thursday:09:00"
      },
      "options": {
        "task_type": "midweek_update",
        "auto_comparison": true,
        "generate_verification_table": true
      }
    },
    {
      "task_id": "weekly_full_update",
      "schedule": {
        "expression": "weekly:saturday:19:00"
      },
      "options": {
        "task_type": "full_update",
        "auto_comparison": true,
        "generate_heatmap": true,
        "upload_to_tencent": true
      }
    }
  ]
}
```

---

## 🎨 UI界面重构技术细节

### 重构前问题分析
原系统存在以下UX问题：
1. ❌ 废弃的"刷新周期"选择器意义不明
2. ❌ 被禁用的刷新按钮没有说明
3. ❌ 日历星期位置错位
4. ❌ "智能调度"概念过于复杂
5. ❌ 多个冗余按钮造成用户困惑

### 简化设计原则
**核心理念**: 用户只需要两个简单直观的控制按钮

#### 1. 双按钮设计规格

```jsx
// 自动下载开关按钮
<button className={`${scheduleConfig.auto_download_enabled 
  ? 'bg-green-600 text-white hover:bg-green-700'    // 🟢 亮绿色 = 开启状态
  : 'bg-gray-400 text-white'                       // ⚪ 灰色 = 关闭状态
}`}>
  {scheduleConfig.auto_download_enabled ? '🟢 自动下载已开启' : '⚪ 自动下载已关闭'}
</button>

// 立即刷新按钮
<button disabled={downloading} className={`${downloading
  ? 'bg-gray-400 text-white cursor-not-allowed'     // ⏳ 执行中 = 灰色禁用
  : 'bg-blue-600 text-white hover:bg-blue-700'      // ⚡ 就绪状态 = 亮蓝色  
}`}>
  {downloading ? '⏳ 刷新中...' : '⚡ 立即刷新'}
</button>
```

#### 2. 状态管理简化

```jsx
// 重构前：复杂的多状态管理
const [scheduleConfig, setScheduleConfig] = useState({
  baseline_enabled: false,
  midweek_enabled: false, 
  weekend_enabled: false,
  scheduler_running: false
});
const [scheduleStatus, setScheduleStatus] = useState('');

// 重构后：单一状态管理
const [scheduleConfig, setScheduleConfig] = React.useState({
  auto_download_enabled: false  // 只保留一个核心状态
});
const [downloading, setDownloading] = React.useState(false);
const [downloadStatus, setDownloadStatus] = React.useState('');
```

### 日历显示修复

#### 问题：星期位置错位
**原因**: JavaScript日期计算错误，没有正确处理月份第一天对应的星期

**修复方案**:
```jsx
// 修复前：错误的日期计算
const dayNum = i - 6 + new Date(new Date().getFullYear(), new Date().getMonth(), 1).getDay();

// 修复后：正确的日历布局算法
const today = new Date();
const year = today.getFullYear();
const month = today.getMonth();
const firstDay = new Date(year, month, 1);
const firstDayWeekday = firstDay.getDay(); // 0=周日，1=周一...6=周六
const daysInMonth = new Date(year, month + 1, 0).getDate();

// 填充前置空白格子
for (let i = 0; i < firstDayWeekday; i++) {
  calendarCells.push(<div key={`empty-${i}`} className="text-slate-300">
    {new Date(year, month, -firstDayWeekday + i + 1).getDate()}
  </div>);
}

// 填充当月日期
for (let day = 1; day <= daysInMonth; day++) {
  const currentDate = new Date(year, month, day);
  const weekday = currentDate.getDay();
  
  // 特殊日期标记 (周二/周四/周六)
  let specialClass = '';
  if (weekday === 2) specialClass = 'bg-red-100 text-red-800';      // 周二基线
  else if (weekday === 4) specialClass = 'bg-cyan-100 text-cyan-800'; // 周四周中  
  else if (weekday === 6) specialClass = 'bg-blue-100 text-blue-800'; // 周六周末
  
  calendarCells.push(<div key={day} className={specialClass}>{day}</div>);
}
```

---

## 🔧 后端API设计

### 1. 配置管理API

```python
@app.route('/api/get-schedule-config', methods=['GET'])
def get_schedule_config():
    """获取调度配置状态"""
    try:
        with open('/root/projects/tencent-doc-manager/config/schedule_tasks.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify({
            "success": True,
            "config": {
                "baseline_enabled": config_data["preset_tasks"][0].get("enabled", False)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/update-schedule-config', methods=['POST'])  
def update_schedule_config():
    """更新调度配置"""
    data = request.get_json()
    auto_download_enabled = data.get('auto_download_enabled')
    
    try:
        # 更新配置文件
        with open('/root/projects/tencent-doc-manager/config/schedule_tasks.json', 'r+', encoding='utf-8') as f:
            config_data = json.load(f)
            config_data["preset_tasks"][0]["enabled"] = auto_download_enabled
            f.seek(0)
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            f.truncate()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

### 2. 差异化下载API

```python
@app.route('/api/start-download', methods=['POST'])
def start_download():
    """支持差异化执行的下载API"""
    data = request.get_json() or {}
    task_type = data.get('task_type', 'full')  # baseline/midweek/weekend/full
    
    if task_type == 'baseline':
        # 基线任务：仅下载，不比对，不刷新UI
        return execute_baseline_download()
    else:
        # 完整流程：下载 + 比对分析 + UI刷新
        return execute_full_workflow()
```

---

## 🚀 核心技术特性

### 1. 自适应时间管理
- **智能基准版选择**: 根据当前时间自动判断使用本周还是上周的基准数据
- **严格时间验证**: 基于`WeekTimeManager`的精确时间逻辑
- **容错处理**: 基准版文件缺失时的自动回退机制

### 2. 差异化执行逻辑
- **基线模式**: 仅执行数据下载，保留上次的UI状态
- **完整模式**: 执行下载→比对→热力图生成→UI刷新的完整链路
- **手动模式**: 用户主动触发的强制刷新

### 3. 实时状态同步
- **配置同步**: Cookie和链接输入后自动保存并同步到后端
- **状态反馈**: 按钮颜色实时反映开关和执行状态  
- **错误处理**: 完整的异常捕获和用户友好的错误提示

---

## 📊 文件结构与依赖

### 核心文件清单
```
/root/projects/tencent-doc-manager/
├── production/servers/
│   └── final_heatmap_server.py           # 主服务器文件 (Flask + React)
├── production/core_modules/
│   └── week_time_manager.py              # 时间管理核心模块
├── config/
│   └── schedule_tasks.json               # 调度配置文件
└── plans/
    └── calendar-schedule-ui-refactoring-specification.md  # 本技术文档
```

### 技术栈
- **后端**: Python 3.x, Flask Framework
- **前端**: React 18, Tailwind CSS
- **时间管理**: Python datetime, ISO周数计算
- **数据存储**: JSON配置文件, CSV版本管理
- **服务器**: 生产环境运行在 http://202.140.143.88:8089

---

## ✅ 验收标准

### 功能验收清单
- [x] **时间节点正确**: 周二12:00基线 / 周四09:00周中 / 周六19:00周末
- [x] **双按钮简化**: 自动下载开关(绿色/灰色) + 立即刷新按钮(蓝色/灰色)
- [x] **差异化执行**: 基线仅下载 vs 完整流程
- [x] **日历修复**: 星期位置正确对齐，特殊日期高亮显示
- [x] **配置同步**: Cookie和链接保存后立即同步
- [x] **状态反馈**: 按钮颜色实时反映当前状态
- [x] **错误处理**: JavaScript运行时错误完全修复

### 用户体验提升
1. **简化操作**: 从8个复杂按钮简化为2个核心按钮
2. **直观反馈**: 颜色编码的状态指示系统
3. **错误消除**: 清理所有废弃元素和JavaScript错误
4. **性能优化**: 精简React状态管理，减少不必要的渲染

---

## 🔮 未来扩展方向

### 1. 调度器集成
- 集成Linux crontab或systemd timer实现真正的定时任务
- 添加任务执行历史和日志记录
- 实现任务失败重试机制

### 2. 移动端适配
- 响应式设计优化
- 触屏操作友好的按钮设计
- Progressive Web App (PWA) 支持

### 3. 高级功能
- 自定义时间节点配置
- 多租户调度隔离
- 实时WebSocket状态推送

---

## 📝 变更日志

### v2.0.0 (2025-08-23)
- **BREAKING CHANGE**: 完全重构调度UI界面
- **NEW**: 双按钮简化控制方案
- **NEW**: 差异化执行逻辑 (基线 vs 完整流程)
- **FIX**: 日历星期位置错位问题
- **FIX**: JavaScript运行时错误修复
- **REMOVE**: 智能调度复杂概念和相关UI

### v1.x.x (历史版本)
- 复杂的智能调度系统 (已废弃)
- 多按钮界面设计 (已简化)

---

## 👨‍💻 开发者备注

**重构完成时间**: 2025-08-23 22:30 UTC+8  
**服务器状态**: ✅ 正常运行中  
**测试状态**: ✅ 前后端集成测试通过  
**文档状态**: ✅ 技术规格完整记录  

**核心改进价值**: 将复杂的企业级调度系统成功简化为用户友好的双按钮控制界面，在保持强大功能的同时大幅提升了用户体验和系统稳定性。