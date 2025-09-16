# EJS格式解码分析报告

## 📊 测试结果总结

### ✅ 成功部分
1. **下载成功率**: 100% - Cookie认证有效，可以成功下载文件
2. **URL端点确认**: 
   - CSV: `https://docs.qq.com/dop-api/opendoc?id={DOC_ID}&type=export_csv`
   - Excel: `https://docs.qq.com/dop-api/opendoc?id={DOC_ID}&type=export_xlsx`
3. **文件格式识别**: EJS (Enhanced JavaScript) - 腾讯专有格式

### ❌ 问题发现
1. **不是标准Excel/CSV**: 返回的是 `text/ejs-data` 格式，不是二进制Excel
2. **多层编码**: 
   - 外层: EJS容器格式
   - 中层: URL编码 + JSON封装
   - 内层: Base64编码
   - 核心: zlib压缩（但使用了非标准压缩字典）
3. **解压失败**: 虽然有zlib标志(0x7801)，但标准zlib解压失败

## 🔍 数据结构分析

### EJS文件结构
```
head                      # 文件头标识
json                      # JSON段标识
7495                      # JSON数据长度
{clientVars, bodyData...} # 文档元数据(7495字符)
text                      # 文本段标识
text                      
68388                     # workbook数据长度
%7B%22workbook%22...      # URL编码的workbook数据(68388字符)
  ├── workbook (Base64)   # 1684字符
  │   └── zlib压缩数据    # 1263字节（解压失败）
  ├── related_sheet       # 相关表格数据
  ├── max_row: 166        # 表格行数
  └── max_col: 21         # 表格列数
```

### 关键发现
- 表格实际大小: 166行 × 21列
- workbook数据确实存在但被加密/压缩
- zlib压缩使用了自定义字典或加密

## 🚫 腾讯的防护机制

1. **非标准压缩**: 使用修改版zlib，标准库无法解压
2. **私有格式**: EJS格式非公开标准
3. **多层编码**: 增加逆向难度
4. **动态加密**: 可能使用会话相关的密钥

## 💡 可行的解决方案

### 方案1: 浏览器自动化（推荐）
```python
# 使用Playwright模拟真实浏览器操作
# 通过页面UI触发导出，让浏览器处理解密
async def browser_export():
    page = await browser.new_page()
    await page.goto(doc_url)
    await page.click("导出按钮")
    # 浏览器会自动处理EJS解密
```

### 方案2: 逆向工程
- 需要分析腾讯文档的JavaScript代码
- 找到EJS解码函数
- 提取解密算法
- 风险：可能违反服务条款

### 方案3: 官方API
- 申请腾讯文档开放平台API
- 需要企业认证
- 有使用限制

## 📝 结论

1. **直接下载可行但无法解码**: Cookie方式能下载但得到加密的EJS格式
2. **腾讯使用了专有加密**: 非标准zlib压缩，无法用常规方法解码
3. **推荐使用浏览器自动化**: 让浏览器处理解密，获取真实文件

## 🔧 下一步建议

1. **短期方案**: 使用Playwright自动化，模拟用户点击导出
2. **长期方案**: 
   - 研究官方API可能性
   - 或继续优化浏览器自动化稳定性

## 📁 相关文件
- `simple_real_test.py` - 成功下载EJS文件
- `deep_workbook_decoder.py` - 解码尝试（失败）
- `test_DWEVjZndkR2xVSWJN_*.csv/xlsx` - 下载的EJS格式文件

---
**生成时间**: 2025-08-27
**结论**: EJS格式需要浏览器环境解密，建议使用自动化方案