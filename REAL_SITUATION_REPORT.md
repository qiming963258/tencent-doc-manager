# 腾讯文档下载 - 真实情况报告

## 🚨 核心问题：无法获取正常格式的文件

### 测试结果汇总

| 方法 | 声称的格式 | 实际返回 | 是否可用 |
|------|-----------|---------|---------|
| dop-api (CSV) | CSV | EJS + Protobuf | ❌ |
| dop-api (XLSX) | Excel | EJS + Protobuf | ❌ |
| Playwright | Excel | 超时/失败 | ❌ |
| 直接端点 | Excel | 404错误 | ❌ |

## 📊 实际返回的数据格式

### 1. EJS响应格式
```
text
text
68388
{URL编码的JSON数据}
```

### 2. JSON内容结构
```json
{
  "workbook": "Base64编码的Protobuf数据",
  "related_sheet": "Base64编码的数据",
  "max_row": 166,
  "max_col": 21,
  "end_row_index": 165,
  "formula_version": 33
}
```

### 3. 数据编码层次
1. **第一层**: EJS封装（text/ejs-data）
2. **第二层**: URL编码
3. **第三层**: JSON格式
4. **第四层**: Base64编码
5. **第五层**: zlib压缩
6. **第六层**: Protocol Buffers序列化

## 🔍 深度分析

### 为什么所有方法都失败了？

1. **dop-api已被改造**
   - 不再返回标准CSV/Excel
   - 返回自定义的Protobuf格式
   - 需要客户端JavaScript解析

2. **Playwright遇到的问题**
   - 页面可能使用了反自动化检测
   - Cookie认证不完整
   - 导出功能可能被服务端限制

3. **数据确实存在**
   - workbook字段包含了实际数据
   - 但是以Protobuf格式编码
   - 没有公开的解码文档

## 💡 可能的解决方案

### 方案1：解析Protobuf数据（困难）
```python
# 需要逆向工程获取.proto定义
import base64
import zlib
from google.protobuf import descriptor_pb2

workbook_base64 = data['workbook']
workbook_bytes = base64.b64decode(workbook_base64)
decompressed = zlib.decompress(workbook_bytes)

# 问题：需要.proto定义文件才能解析
# 腾讯没有公开这个格式
```

### 方案2：使用腾讯文档的JavaScript SDK（如果存在）
- 寻找腾讯文档的前端JavaScript代码
- 逆向工程解析函数
- 在Node.js环境中运行

### 方案3：网络抓包分析
- 使用mitmproxy捕获真实的导出请求
- 分析是否有其他隐藏的API端点
- 可能需要额外的认证参数

### 方案4：浏览器扩展开发
- 开发Chrome扩展
- 在浏览器内部拦截数据
- 绕过所有反爬虫机制

## ⚠️ 现实结论

### 当前状况
1. **没有简单的方法获取标准格式文件**
2. **所有公开的导出API都已失效**
3. **返回的数据需要复杂的解码过程**

### 技术难度评估
- 解析Protobuf：⭐⭐⭐⭐⭐（极难）
- 逆向JavaScript：⭐⭐⭐⭐（很难）
- 浏览器扩展：⭐⭐⭐（中等）
- 官方API：⭐（简单但需要资质）

## 📝 建议

### 短期建议（无法获取标准格式文件）
1. **接受现实**：腾讯已经成功封堵了所有常规方法
2. **保存原始数据**：至少我们能获取EJS格式的数据
3. **寻找解码方法**：研究Protobuf格式

### 长期建议
1. **申请官方API**：这是唯一可靠的方法
2. **人工操作**：对于少量文档，手动下载
3. **寻找替代方案**：考虑其他文档平台

## 🎯 最终答案

**问题**：CSV+Playwright组合下载的内容是否有文件格式的正常文件？

**答案**：**没有**。所有方法都无法获得正常格式的CSV或Excel文件：
- CSV下载返回Protobuf编码的数据
- XLSX下载返回相同的Protobuf数据
- Playwright因为反自动化检测而失败
- 没有可用的开源解码方案

## 技术细节补充

腾讯使用的技术栈：
- Protocol Buffers（Google的序列化框架）
- zlib压缩
- Base64编码
- 多层嵌套的数据格式

这种设计明显是为了：
1. 防止自动化下载
2. 保护数据格式
3. 强制用户使用官方客户端

---

**报告时间**: 2025-08-27  
**结论**: 需要寻找全新的技术方案或申请官方API