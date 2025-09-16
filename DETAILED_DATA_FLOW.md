# 🔬 腾讯文档智能监控系统 - 极详细数据流动图

## 第一部分：用户输入与初始化流程

### 用户Cookie获取流程
用户打开浏览器
↓
访问 https://docs.qq.com
↓
输入用户名密码
↓
腾讯后台返回认证Token
↓
浏览器存储Cookie到本地
↓
用户F12打开开发者工具
↓
切换到Network标签
↓
刷新页面触发请求
↓
找到docs.qq.com域名请求
↓
查看Request Headers
↓
复制Cookie字段全文
↓
Cookie字符串存入剪贴板

### UI界面数据输入流程
用户访问 http://202.140.143.88:8090/
↓
浏览器发送GET请求
↓
Flask接收请求 (auto_download_ui_system.py:764)
↓
render_template_string(HTML_TEMPLATE)
↓
HTML页面返回给浏览器
↓
浏览器渲染页面DOM
↓
JavaScript初始化 (window.onload)
↓
loadConfig()函数执行
↓
fetch('/api/get_config') API调用
↓
读取 auto_download_config.json 文件
↓
JSON.parse()解析配置
↓
配置数据填充到表单
↓
用户点击Cookie输入框
↓
粘贴Cookie字符串
↓
document.getElementById('cookie').value 赋值
↓
Cookie暂存在前端内存

### URL添加流程
用户输入腾讯文档URL
↓
document.getElementById('new-url').value 获取
↓
JavaScript验证URL格式
↓
url.startsWith('https://docs.qq.com/') 检查
↓
urlList.push(url) 添加到数组
↓
updateURLList() 更新显示
↓
innerHTML动态生成URL列表HTML
↓
URL数组存储在前端 urlList 变量

### 配置保存流程
用户点击"保存配置"按钮
↓
saveConfig() JavaScript函数触发
↓
收集表单所有数据:
  - document.getElementById('cookie').value
  - document.getElementById('format').value
  - document.getElementById('interval').value
  - document.getElementById('download-dir').value
  - urlList数组
↓
构建config JSON对象
↓
JSON.stringify(config) 序列化
↓
fetch('/api/save_config', {method: 'POST'})
↓
Flask接收POST请求
↓
request.json 解析请求体
↓
save_config(config) Python函数
↓
json.dump() 写入文件
↓
/root/projects/tencent-doc-manager/auto_download_config.json 保存
↓
返回 {'success': True} 响应

## 第二部分：定时调度与下载流程

### 定时任务启动流程
用户点击"启动定时"按钮
↓
startScheduler() JavaScript函数
↓
fetch('/api/start_scheduler', {method: 'POST'})
↓
Flask api_start_scheduler() 处理
↓
load_config() 读取配置文件
↓
scheduler_stop_flag.clear() 清除停止标志
↓
threading.Thread(target=scheduler_worker) 创建线程
↓
scheduler_thread.start() 启动线程
↓
DOWNLOAD_STATUS['is_running'] = True
↓
scheduler_worker() 在新线程执行
↓
config.get('interval', 60) 获取间隔时间
↓
进入while循环等待

### 自动下载触发流程
定时器到达设定时间
↓
run_download_task() 函数执行
↓
asyncio.new_event_loop() 创建事件循环
↓
loop.run_until_complete(download_documents())
↓
download_documents() 异步函数开始
↓
load_config() 重新读取配置
↓
config.get('cookie') 获取Cookie字符串
↓
config.get('urls') 获取URL列表
↓
config.get('format') 获取下载格式
↓
config.get('download_dir') 获取保存目录
↓
TencentDocAutoExporter() 创建导出器实例

### Playwright浏览器初始化流程
exporter.start_browser(headless=True)
↓
async_playwright().start() 启动Playwright
↓
self.playwright = playwright实例
↓
os.makedirs(download_dir) 创建下载目录
↓
playwright.chromium.launch() 启动Chromium
↓
browser实例创建，参数:
  - headless=True
  - downloads_path=download_dir
↓
browser.new_context() 创建上下文
↓
context设置:
  - accept_downloads=True
  - user_agent='Mozilla/5.0...'
↓
context.new_page() 创建页面
↓
page.on("download", _handle_download) 监听下载

### Cookie认证流程
exporter.login_with_cookies(cookie_string)
↓
cookies.split(';') 分割Cookie字符串
↓
遍历每个cookie片段
↓
cookie.split('=', 1) 分割name和value
↓
domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
↓
为每个domain创建cookie对象:
  {
    'name': cookie_name,
    'value': cookie_value,
    'domain': domain,
    'path': '/',
    'httpOnly': False,
    'secure': True,
    'sameSite': 'None'
  }
↓
cookie_list累积所有cookie对象
↓
page.context.add_cookies(cookie_list)
↓
浏览器存储116个cookies（4域名×29个）

### 文档访问与导出流程
遍历config['urls']中每个URL
↓
exporter.export_document(url, format)
↓
page.goto(url, wait_until='domcontentloaded')
↓
页面HTML加载完成
↓
page.wait_for_timeout(3000) 等待3秒
↓
page.wait_for_load_state('networkidle') 
↓
网络请求完成
↓
_try_menu_export() 尝试菜单导出
↓
page.query_selector('.titlebar-icon.titlebar-icon-more')
↓
找到"更多"按钮元素
↓
menu_btn.click() 点击菜单
↓
page.wait_for_timeout(1000)
↓
page.query_selector('li.mainmenu-submenu-exportAs')
↓
找到"导出为"选项
↓
export_as_btn.hover() 悬停触发子菜单
↓
page.wait_for_timeout(500)
↓
根据format选择导出类型:
  - CSV: 'li.mainmenu-item-export-csv'
  - Excel: 'li.mainmenu-item-export-local'
↓
export_btn.click() 点击导出
↓
触发浏览器下载事件

### 文件下载处理流程
download事件触发
↓
_handle_download(download) 回调函数
↓
download.suggested_filename 获取文件名
↓
os.path.join(download_dir, filename) 构建路径
↓
download.save_as(filepath) 保存文件
↓
文件字节流写入磁盘
↓
downloaded_files.append(filepath)
↓
文件保存完成，例如:
  /root/projects/tencent-doc-manager/auto_downloads/测试版本-小红书部门.xlsx

## 第三部分：数据处理与分析流程

### CSV版本管理流程
CSVVersionManager 初始化
↓
version_manager.add_version(filepath)
↓
读取CSV文件头部
↓
pandas.read_csv(filepath)
↓
DataFrame对象创建
↓
df.columns 获取列名列表
↓
df.values 获取数据矩阵
↓
计算文件MD5哈希
↓
hashlib.md5(file_content).hexdigest()
↓
version_info = {
  'file_path': filepath,
  'timestamp': datetime.now(),
  'hash': md5_hash,
  'columns': column_list,
  'row_count': len(df)
}
↓
versions_history.append(version_info)

### 版本对比流程
version_manager.compare_versions(v1, v2)
↓
load_csv_data(v1.file_path)
↓
load_csv_data(v2.file_path)
↓
df1.shape 获取维度
↓
df2.shape 获取维度
↓
检查行列数是否相同
↓
遍历每个单元格 (i, j)
↓
old_value = df1.iloc[i, j]
↓
new_value = df2.iloc[i, j]
↓
if old_value != new_value:
  changes.append({
    'row': i,
    'col': j,
    'old': old_value,
    'new': new_value
  })
↓
返回changes列表

### AI分析请求流程
对每个change进行分析
↓
构建分析上下文:
  {
    'column_name': df.columns[j],
    'row_context': df.iloc[i].to_dict(),
    'old_value': change['old'],
    'new_value': change['new']
  }
↓
claude_request = {
  'prompt': f"分析此单元格变化...",
  'context': context_json
}
↓
requests.post('http://localhost:8081/api/analyze')
↓
Claude API处理请求
↓
分析变化类型:
  - 数值变化幅度
  - 文本语义差异
  - 日期逻辑检查
  - 业务规则验证
↓
返回分析结果:
  {
    'risk_level': 'L2',
    'confidence': 0.85,
    'reason': '金额增长超过20%',
    'suggestion': '需要财务审核'
  }

### 列名标准化流程
获取所有原始列名
↓
columns = df.columns.tolist()
↓
遍历每个列名
↓
发送到Claude进行语义分析
↓
"产品名称" → analyze_column_name()
↓
匹配标准化词典:
  {
    '产品': 'product',
    '名称': 'name',
    '部门': 'department',
    '金额': 'amount'
  }
↓
生成标准列名: 'product_name'
↓
column_mapping[原始名] = 标准名
↓
df.rename(columns=column_mapping)
↓
标准化后的DataFrame

### 评分计算流程
对每个单元格计算风险分值
↓
base_score = calculate_base_score(change)
↓
根据变化类型确定基础分:
  - 数值变化: abs(new - old) / old * 10
  - 文本变化: edit_distance(old, new) / len(old) * 10
↓
risk_weight获取:
  - L1 (低风险): 0.3
  - L2 (中风险): 0.6
  - L3 (高风险): 1.0
↓
frequency_factor = 变化频率 / 总变化数
↓
final_score = base_score * risk_weight * frequency_factor
↓
scores_matrix[row][col] = final_score

## 第四部分：可视化生成流程

### 热力图矩阵生成流程
scores_matrix 30×19 初始化
↓
numpy.zeros((30, 19)) 创建零矩阵
↓
遍历所有变化单元格
↓
(row, col) → 映射到矩阵坐标
↓
matrix[i][j] = cell_score
↓
处理稀疏数据:
  - 空值填充为0
  - 异常值截断到[0, 100]
↓
matrix_data = {
  'data': matrix.tolist(),
  'rows': 30,
  'cols': 19,
  'total_cells': 570
}

### 高斯平滑处理流程
导入scipy.ndimage
↓
gaussian_filter(matrix, sigma=1.0)
↓
构建高斯核矩阵
↓
卷积运算:
  for i in range(30):
    for j in range(19):
      kernel_sum = 0
      weight_sum = 0
      for ki in [-2, -1, 0, 1, 2]:
        for kj in [-2, -1, 0, 1, 2]:
          if valid_position(i+ki, j+kj):
            weight = gaussian(ki, kj, sigma)
            kernel_sum += matrix[i+ki][j+kj] * weight
            weight_sum += weight
      smoothed[i][j] = kernel_sum / weight_sum
↓
smoothed_matrix 生成完成

### 色彩映射流程
对每个单元格值进行颜色映射
↓
value = smoothed_matrix[i][j]
↓
确定颜色区间:
  if value < 20:
    color_range = 'blue'
    rgb = (0, 0, 255)
  elif value < 40:
    color_range = 'cyan'
    rgb = (0, 255, 255)
  elif value < 60:
    color_range = 'green'
    rgb = (0, 255, 0)
  elif value < 80:
    color_range = 'yellow'
    rgb = (255, 255, 0)
  else:
    color_range = 'red'
    rgb = (255, 0, 0)
↓
线性插值计算精确颜色:
  t = (value - range_min) / (range_max - range_min)
  r = int(r1 + (r2 - r1) * t)
  g = int(g1 + (g2 - g1) * t)
  b = int(b1 + (b2 - b1) * t)
↓
rgb_to_hex(r, g, b)
↓
color_matrix[i][j] = '#RRGGBB'

### 统计数据生成流程
遍历scores_matrix
↓
统计各风险等级数量:
  high_risk_count = 0
  medium_risk_count = 0
  low_risk_count = 0
↓
for score in matrix.flat:
  if score >= 80:
    high_risk_count += 1
  elif score >= 40:
    medium_risk_count += 1
  else:
    low_risk_count += 1
↓
计算热点区域:
  hot_spots = []
  for i in range(30):
    for j in range(19):
      if matrix[i][j] > 80:
        hot_spots.append({'row': i, 'col': j, 'value': matrix[i][j]})
↓
statistics = {
  'total_changes': len(changes),
  'high_risk': high_risk_count,
  'medium_risk': medium_risk_count,
  'low_risk': low_risk_count,
  'hot_spots': hot_spots,
  'max_value': matrix.max(),
  'mean_value': matrix.mean(),
  'std_dev': matrix.std()
}

## 第五部分：Excel处理流程

### Excel文件创建流程
import openpyxl
↓
workbook = Workbook()
↓
worksheet = workbook.active
↓
worksheet.title = "风险分析报告"
↓
设置列宽:
  for col in range(1, 20):
    worksheet.column_dimensions[chr(64+col)].width = 12
↓
设置行高:
  for row in range(1, 31):
    worksheet.row_dimensions[row].height = 20

### 数据写入流程
遍历原始数据
↓
for i, row_data in enumerate(data_rows):
  for j, cell_value in enumerate(row_data):
    cell = worksheet.cell(row=i+1, column=j+1)
    cell.value = cell_value
↓
检查是否有变化标记
↓
if (i, j) in changes_dict:
  change_info = changes_dict[(i, j)]
  apply_formatting(cell, change_info)

### 半填充格式应用流程
导入PatternFill, Font, Border
↓
根据风险等级选择颜色:
  risk_colors = {
    'L1': 'C6EFCE',  # 浅绿
    'L2': 'FFEB9C',  # 浅黄
    'L3': 'FFC7CE'   # 浅红
  }
↓
创建PatternFill对象:
  pattern = PatternFill(
    patternType='lightUp',
    fgColor=risk_colors[risk_level],
    bgColor='FFFFFF'
  )
↓
cell.fill = pattern
↓
添加边框:
  border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
  )
↓
cell.border = border

### AI批注添加流程
导入Comment
↓
创建批注文本:
  comment_text = f"""
  原值: {change_info['old']}
  新值: {change_info['new']}
  风险等级: {change_info['risk_level']}
  AI分析: {change_info['ai_analysis']}
  建议: {change_info['suggestion']}
  置信度: {change_info['confidence']:.2f}
  """
↓
comment = Comment(comment_text, "Claude AI")
↓
comment.width = 300
↓
comment.height = 200
↓
cell.comment = comment

### Excel保存流程
output_path = '/root/projects/tencent-doc-manager/marked_excel.xlsx'
↓
workbook.save(output_path)
↓
文件写入磁盘
↓
os.path.getsize(output_path) 获取文件大小
↓
计算MD5:
  with open(output_path, 'rb') as f:
    md5 = hashlib.md5(f.read()).hexdigest()
↓
记录文件信息:
  {
    'path': output_path,
    'size': file_size,
    'md5': md5,
    'timestamp': datetime.now()
  }

## 第六部分：腾讯文档上传流程

### 上传准备流程
TencentDocUploader() 实例化
↓
uploader.start_browser(headless=True)
↓
playwright启动浏览器
↓
uploader.login_with_cookies(cookies)
↓
多域名Cookie设置（同下载流程）
↓
准备上传文件路径:
  file_to_upload = marked_excel_path

### 页面导航流程
page.goto('https://docs.qq.com/desktop')
↓
等待DOM加载:
  wait_until='domcontentloaded'
↓
page.wait_for_timeout(3000)
↓
page.wait_for_load_state('networkidle')
↓
检查登录状态:
  login_check = page.query_selector('.user-info')
↓
if not login_check:
  raise Exception("未登录")

### 导入按钮查找流程
import_selectors = [
  'button[class*="import"]:not([class*="disabled"])',
  'div[class*="upload"]:not([class*="disabled"])',
  'button[class*="desktop-import"]',
  'button:has-text("导入")',
  'button:has-text("上传")'
]
↓
遍历选择器列表
↓
for selector in import_selectors:
  btn = page.query_selector(selector)
  if btn:
    is_visible = btn.is_visible()
    is_enabled = btn.is_enabled()
    if is_visible and is_enabled:
      import_button = btn
      break

### 文件选择流程
设置文件选择监听:
  file_chooser_promise = page.wait_for_event('filechooser')
↓
import_button.click()
↓
等待filechooser事件:
  file_chooser = await file_chooser_promise
↓
file_chooser.set_files(file_path)
↓
文件路径设置完成

### 确认上传流程
等待上传对话框:
  page.wait_for_timeout(2000)
↓
查找确认按钮:
  confirm_selectors = [
    'div[class*="dui-button"]:has-text("确定")',
    'button:has-text("确定")',
    'button:has-text("确认")'
  ]
↓
confirm_button = page.query_selector(selector)
↓
confirm_button.click()
↓
监控上传进度:
  for i in range(60):
    page.wait_for_timeout(1000)
    try:
      page.wait_for_load_state('networkidle', timeout=1000)
      break
    except:
      continue
↓
上传完成验证:
  success_indicator = page.query_selector('.upload-success')

## 第七部分：UI展示流程

### Web服务器启动流程
final_heatmap_server.py 执行
↓
Flask(__name__) 初始化
↓
app.run(host='0.0.0.0', port=8089)
↓
服务器监听8089端口
↓
等待HTTP请求

### 首页加载流程
用户访问 http://202.140.143.88:8089/
↓
Flask路由 @app.route('/')
↓
render_template('heatmap.html')
↓
HTML返回给浏览器
↓
浏览器解析HTML
↓
加载CSS样式
↓
加载JavaScript
↓
React.createElement() 创建组件
↓
ReactDOM.render() 渲染到DOM

### 数据请求流程
React组件 componentDidMount()
↓
fetch('/api/heatmap-data')
↓
Flask处理API请求
↓
读取最新的matrix_data
↓
JSON.stringify(matrix_data)
↓
返回给前端
↓
response.json() 解析
↓
setState({heatmapData: data})
↓
触发React重新渲染

### 热力图渲染流程
HeatmapComponent.render()
↓
创建SVG元素
↓
计算单元格尺寸:
  cellWidth = 800 / 30
  cellHeight = 600 / 19
↓
遍历矩阵数据:
  for i in range(30):
    for j in range(19):
      创建rect元素:
        <rect
          x={i * cellWidth}
          y={j * cellHeight}
          width={cellWidth}
          height={cellHeight}
          fill={colorMatrix[i][j]}
          onClick={() => handleCellClick(i, j)}
        />
↓
添加到SVG容器
↓
浏览器渲染可视化

### 交互事件处理流程
用户点击热力图单元格
↓
onClick事件触发
↓
handleCellClick(row, col)
↓
获取单元格详细信息:
  {
    position: {row, col},
    value: matrix[row][col],
    original_value: originalData[row][col],
    change_info: changes[`${row}_${col}`],
    ai_analysis: aiResults[`${row}_${col}`]
  }
↓
setState({selectedCell: cellInfo})
↓
显示详情弹窗
↓
渲染详细信息面板

### WebSocket实时更新流程
建立WebSocket连接:
  ws = new WebSocket('ws://202.140.143.88:8089/ws')
↓
ws.onopen 连接建立
↓
服务器定时推送:
  while True:
    new_data = get_latest_data()
    ws.send(json.dumps(new_data))
    time.sleep(5)
↓
ws.onmessage 接收数据
↓
JSON.parse(event.data)
↓
updateHeatmap(newData)
↓
setState触发重新渲染
↓
UI实时更新

### 统计面板更新流程
收到新数据
↓
计算统计信息:
  totalChanges = Object.keys(changes).length
  highRiskCount = values.filter(v => v > 80).length
  mediumRiskCount = values.filter(v => v > 40 && v <= 80).length
  lowRiskCount = values.filter(v => v <= 40).length
↓
更新统计组件:
  <StatisticsPanel
    total={totalChanges}
    high={highRiskCount}
    medium={mediumRiskCount}
    low={lowRiskCount}
  />
↓
DOM更新显示最新统计

## 第八部分：用户决策流程

### 风险识别流程
用户查看热力图
↓
识别红色高风险区域
↓
点击查看详情
↓
阅读AI分析结果
↓
理解变化原因
↓
评估风险等级

### 导出报告流程
点击"导出报告"按钮
↓
generateReport() 函数执行
↓
收集所有分析数据:
  - 热力图数据
  - 变化列表
  - AI分析结果
  - 统计信息
↓
生成PDF/Excel报告
↓
浏览器下载文件

### 审批决策流程
基于分析结果
↓
判断是否需要干预
↓
如需干预:
  - 联系相关部门
  - 要求解释说明
  - 执行回滚操作
↓
如无需干预:
  - 记录审核结果
  - 归档分析报告
↓
更新审批状态

## 总计数据流动节点

**统计结果**：
- 用户输入流程：12个节点
- Cookie认证流程：11个节点
- 文档下载流程：24个节点
- CSV处理流程：18个节点
- AI分析流程：15个节点
- 热力图生成：22个节点
- Excel处理：20个节点
- 上传流程：18个节点
- UI展示流程：25个节点
- 用户决策：10个节点

**总计：175个数据流动节点**

## 关键数据结构流转

```
原始Cookie字符串
↓
Cookie对象数组（116个）
↓
认证后的Page对象
↓
下载的文件路径
↓
CSV DataFrame
↓
变化检测数组
↓
AI分析结果JSON
↓
风险评分矩阵（30×19）
↓
高斯平滑矩阵
↓
颜色映射矩阵
↓
Excel工作簿对象
↓
标记后的Excel文件
↓
上传成功响应
↓
React组件状态
↓
SVG渲染元素
↓
用户交互事件
↓
最终决策结果
```

这就是完整的、极其详细的数据流动图，包含了175个具体的数据流动节点！