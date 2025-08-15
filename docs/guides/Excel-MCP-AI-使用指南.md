# Excel MCP AI调用标准使用指南

## 📋 概述

本文档为AI系统调用Excel MCP (@negokaz/excel-mcp-server) 的标准使用指南，确保AI正确、高效地使用Excel MCP功能。

## 🚀 快速开始

### 1. MCP服务器状态检查
在使用前，首先确认MCP服务器已正确连接：

```bash
# 检查MCP服务器状态
claude mcp list
```

应该看到以下服务器处于连接状态：
- ✅ **excel-optimized**: npx -y @negokaz/excel-mcp-server (推荐使用)
- ✅ **excel**: npx -y @negokaz/excel-mcp-server (基础版本)

### 2. 基础配置信息
- **内存优化配置**: EXCEL_MCP_PAGING_CELLS_LIMIT="2000" (适合4h2g服务器)
- **支持的文件格式**: .xlsx, .xls
- **并发处理**: 支持多工作表同时操作
- **最大单次处理**: 2000个单元格 (可配置)

## 🔧 核心API使用指南

### 1. 文件信息获取

#### excel_describe_sheets - 获取工作表信息
```python
# 获取Excel文件的所有工作表信息
result = mcp__excel_optimized__excel_describe_sheets(
    fileAbsolutePath="/path/to/file.xlsx"
)
```

**返回结果示例**:
```json
{
  "sheets": [
    {
      "name": "Sheet1",
      "index": 0,
      "range": "A1:E100"
    }
  ]
}
```

**AI使用注意事项**:
- ✅ 必须使用绝对路径
- ✅ 路径中的中文需要正确编码
- ❌ 不要使用相对路径如 "./file.xlsx"

### 2. 数据读取操作

#### excel_read_sheet - 读取工作表数据
```python
# 读取指定范围的数据
result = mcp__excel_optimized__excel_read_sheet(
    fileAbsolutePath="/root/projects/file.xlsx",
    sheetName="数据表",
    range="A1:E10",  # 可选，默认读取所有数据
    showFormula=False,  # 是否显示公式
    showStyle=False     # 是否显示样式信息
)
```

**AI最佳实践**:
1. **分页读取大文件**: 超过2000单元格时自动分页
2. **中文工作表名**: 直接使用中文名称，如 "员工信息"
3. **范围格式**: 使用 "A1:E10" 格式，不是 "A1-E10"

**返回结果格式**:
```html
<table>
<tr><th></th><th>A</th><th>B</th><th>C</th></tr>
<tr><th>1</th><td>姓名</td><td>年龄</td><td>部门</td></tr>
<tr><th>2</th><td>张三</td><td>25</td><td>技术部</td></tr>
</table>
```

### 3. 数据写入操作

#### excel_write_to_sheet - 写入数据到工作表
```python
# 写入数据到Excel工作表
result = mcp__excel_optimized__excel_write_to_sheet(
    fileAbsolutePath="/root/projects/file.xlsx",
    sheetName="新数据表",
    newSheet=True,  # 是否创建新工作表
    range="A1:C3",
    values=[
        ["姓名", "年龄", "城市"],
        ["张三", 25, "北京"],
        ["李四", 30, "上海"]
    ]
)
```

**数据格式规范**:
- ✅ **二维数组**: 使用嵌套列表格式
- ✅ **中文支持**: 直接使用中文字符
- ✅ **数据类型**: 支持字符串、数字、布尔值、null
- ✅ **公式**: 以 "=" 开头，如 "=SUM(A1:A10)"

**AI写入最佳实践**:
```python
# 正确的数据格式
values = [
    ["标题1", "标题2", "标题3"],           # 第一行：标题
    ["数据1", 100, True],               # 第二行：混合数据类型
    ["=A2+B2", "=NOW()", "=IF(B2>50,\"高\",\"低\")"]  # 第三行：公式
]

# 错误的格式 - 避免使用
values = "A1:C3,数据1,数据2,数据3"  # ❌ 字符串格式
values = [["数据1"], "数据2", "数据3"]  # ❌ 不一致的数组格式
```

### 4. 格式化操作

#### excel_format_range - 格式化单元格范围
```python
# 格式化单元格样式
result = mcp__excel_optimized__excel_format_range(
    fileAbsolutePath="/root/projects/file.xlsx",
    sheetName="数据表",
    range="A1:C1",
    styles=[
        [
            {
                "font": {"bold": True, "color": "#FFFFFF", "size": 12},
                "fill": {"type": "pattern", "pattern": "solid", "color": ["#4472C4"]},
                "border": [
                    {"type": "top", "style": "continuous", "color": "#000000"},
                    {"type": "bottom", "style": "continuous", "color": "#000000"}
                ]
            },
            None,  # 第二个单元格不设置样式
            {
                "font": {"italic": True, "color": "#DC2626"}
            }
        ]
    ]
)
```

**样式配置详解**:

1. **字体样式 (font)**:
   ```json
   {
     "bold": true,           // 粗体
     "italic": true,         // 斜体
     "size": 12,            // 字号
     "color": "#FF0000",    // 颜色 (16进制)
     "underline": "single", // 下划线
     "strike": true         // 删除线
   }
   ```

2. **填充样式 (fill)**:
   ```json
   {
     "type": "pattern",
     "pattern": "solid",         // 图案类型
     "color": ["#FF0000"]       // 颜色数组
   }
   ```

3. **边框样式 (border)**:
   ```json
   [
     {"type": "left", "style": "continuous", "color": "#000000"},
     {"type": "right", "style": "continuous", "color": "#000000"},
     {"type": "top", "style": "continuous", "color": "#000000"},
     {"type": "bottom", "style": "continuous", "color": "#000000"}
   ]
   ```

### 5. 表格创建操作

#### excel_create_table - 创建数据表格
```python
# 创建Excel表格
result = mcp__excel_optimized__excel_create_table(
    fileAbsolutePath="/root/projects/file.xlsx",
    sheetName="数据表",
    tableName="员工信息表",
    range="A1:E10"  # 可选，默认自动检测范围
)
```

**表格创建注意事项**:
- ✅ 表格名称要求唯一
- ✅ 范围必须包含标题行
- ✅ 自动应用筛选和格式

### 6. 工作表复制操作

#### excel_copy_sheet - 复制工作表
```python
# 复制工作表
result = mcp__excel_optimized__excel_copy_sheet(
    fileAbsolutePath="/root/projects/file.xlsx",
    srcSheetName="原始数据",
    dstSheetName="数据备份"
)
```

## 🎯 AI使用场景最佳实践

### 场景1: 数据分析和报告生成

```python
# 步骤1: 读取原始数据
data = mcp__excel_optimized__excel_read_sheet(
    fileAbsolutePath="/path/to/data.xlsx",
    sheetName="原始数据"
)

# 步骤2: 分析数据并生成新的汇总表
summary_data = [
    ["部门", "人数", "平均年龄", "总薪资"],
    ["技术部", 15, 28.5, 450000],
    ["市场部", 12, 26.8, 360000],
    ["=SUM(B2:B3)", "=AVERAGE(C2:C3)", "=SUM(D2:D3)", ""]
]

# 步骤3: 创建汇总报告
mcp__excel_optimized__excel_write_to_sheet(
    fileAbsolutePath="/path/to/data.xlsx",
    sheetName="部门汇总",
    newSheet=True,
    range="A1:D4",
    values=summary_data
)

# 步骤4: 格式化报告
mcp__excel_optimized__excel_format_range(
    fileAbsolutePath="/path/to/data.xlsx",
    sheetName="部门汇总",
    range="A1:D1",
    styles=[[
        {"font": {"bold": True, "color": "#FFFFFF"}, 
         "fill": {"type": "pattern", "pattern": "solid", "color": ["#4472C4"]}}
    ] * 4]
)
```

### 场景2: 数据验证和错误标记

```python
# 读取数据进行验证
data = mcp__excel_optimized__excel_read_sheet(
    fileAbsolutePath="/path/to/validation.xlsx",
    sheetName="待验证数据"
)

# 标记错误数据
error_styles = []
for row_idx in range(len(data)):
    row_styles = []
    for col_idx in range(len(data[row_idx])):
        if validate_cell_data(data[row_idx][col_idx]):
            row_styles.append(None)  # 正确数据不设置样式
        else:
            row_styles.append({
                "fill": {"type": "pattern", "pattern": "solid", "color": ["#FFEBEE"]},
                "font": {"color": "#D32F2F"},
                "border": [{"type": "left", "style": "thick", "color": "#D32F2F"}]
            })
    error_styles.append(row_styles)

# 应用错误标记
mcp__excel_optimized__excel_format_range(
    fileAbsolutePath="/path/to/validation.xlsx",
    sheetName="待验证数据",
    range="A1:E10",
    styles=error_styles
)
```

### 场景3: 批量数据处理

```python
# 分批处理大量数据，避免内存溢出
def process_large_excel_file(file_path, sheet_name):
    # 获取工作表信息
    sheet_info = mcp__excel_optimized__excel_describe_sheets(
        fileAbsolutePath=file_path
    )
    
    # 分页读取数据 (每页2000单元格)
    total_rows = extract_total_rows(sheet_info)
    page_size = 50  # 每页50行，避免超过2000单元格限制
    
    processed_data = []
    
    for page_start in range(1, total_rows, page_size):
        page_end = min(page_start + page_size - 1, total_rows)
        range_str = f"A{page_start}:Z{page_end}"
        
        # 读取当前页数据
        page_data = mcp__excel_optimized__excel_read_sheet(
            fileAbsolutePath=file_path,
            sheetName=sheet_name,
            range=range_str
        )
        
        # 处理数据
        processed_page = process_data_page(page_data)
        processed_data.extend(processed_page)
    
    return processed_data
```

## ⚠️ 常见错误及解决方案

### 错误1: 文件路径问题
```
Error: File not found or access denied
```

**解决方案**:
- ✅ 使用绝对路径: `/root/projects/file.xlsx`
- ✅ 检查文件权限
- ✅ 确保文件存在且未被其他程序占用

### 错误2: 中文编码问题
```
Error: Invalid character encoding
```

**解决方案**:
- ✅ 文件名和工作表名直接使用中文
- ✅ 数据内容使用UTF-8编码
- ❌ 避免使用特殊字符如 / \ : * ? " < > |

### 错误3: 数据格式错误
```
Error: Invalid data format for range
```

**解决方案**:
- ✅ 确保 values 是二维数组格式
- ✅ 检查数组维度与指定范围匹配
- ✅ null 值使用 null，不是 "null" 字符串

### 错误4: 内存超限
```
Error: Cell limit exceeded
```

**解决方案**:
- ✅ 使用分页读取，每次不超过2000单元格
- ✅ 优先使用 excel-optimized 版本
- ✅ 分批处理大文件

## 📊 性能优化建议

### 1. 内存优化
- **使用excel-optimized版本**: 配置EXCEL_MCP_PAGING_CELLS_LIMIT="2000"
- **分页处理**: 大文件自动分页，避免一次性加载
- **及时释放**: 处理完成后及时关闭文件句柄

### 2. 速度优化
- **批量操作**: 合并多个小操作为一个大操作
- **范围优化**: 精确指定需要的数据范围
- **格式化合并**: 相同格式的单元格一起处理

### 3. 错误处理
```python
async def safe_excel_operation(operation_func, **kwargs):
    """安全的Excel操作包装器"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return await operation_func(**kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            logger.warning(f"Excel操作失败，第{attempt + 1}次重试: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # 指数退避
    
    return None
```

## 🔍 调试和监控

### 1. 操作日志
```python
import logging

# 配置Excel MCP操作日志
excel_logger = logging.getLogger('excel_mcp')
excel_logger.setLevel(logging.INFO)

def log_excel_operation(operation, file_path, sheet_name, **kwargs):
    """记录Excel操作日志"""
    excel_logger.info(f"Excel操作: {operation}")
    excel_logger.info(f"文件: {file_path}")
    excel_logger.info(f"工作表: {sheet_name}")
    excel_logger.info(f"参数: {kwargs}")
```

### 2. 性能监控
```python
import time
from contextlib import contextmanager

@contextmanager
def monitor_excel_performance(operation_name):
    """监控Excel操作性能"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"Excel操作 '{operation_name}' 耗时: {duration:.2f}秒")
```

## 📚 附录

### A. 支持的样式属性完整列表

#### 字体属性 (font)
- `bold`: 布尔值，是否粗体
- `italic`: 布尔值，是否斜体  
- `size`: 数字，字号大小
- `color`: 字符串，颜色值 (如 "#FF0000")
- `underline`: 字符串，下划线类型 ("none", "single", "double")
- `strike`: 布尔值，是否删除线

#### 填充属性 (fill)
- `type`: 字符串，填充类型 ("pattern", "gradient")
- `pattern`: 字符串，图案类型 ("solid", "darkGray", "lightGray", etc.)
- `color`: 数组，颜色值列表

#### 边框属性 (border)
- `type`: 字符串，边框位置 ("left", "right", "top", "bottom")
- `style`: 字符串，边框样式 ("continuous", "dash", "dot", "thick")
- `color`: 字符串，边框颜色

### B. 常用公式示例
```excel
=SUM(A1:A10)          # 求和
=AVERAGE(B1:B10)      # 平均值
=COUNT(C1:C10)        # 计数
=IF(D1>100,"高","低")  # 条件判断
=VLOOKUP(E1,A:B,2,FALSE)  # 查找
=NOW()                # 当前时间
=CONCATENATE(A1,B1)   # 文本连接
```

### C. 错误代码对照表
| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| E001 | 文件不存在 | 检查文件路径 |
| E002 | 权限不足 | 检查文件权限 |
| E003 | 格式错误 | 检查数据格式 |
| E004 | 内存超限 | 使用分页处理 |
| E005 | 工作表不存在 | 检查工作表名称 |

---

**文档版本**: v1.0
**创建时间**: 2025-08-12
**适用版本**: @negokaz/excel-mcp-server latest
**维护团队**: AI系统开发组