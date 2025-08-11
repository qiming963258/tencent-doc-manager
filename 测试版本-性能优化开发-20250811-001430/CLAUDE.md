# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Simple and practical Tencent Document CSV export tool. The project evolved from over-engineered microservices architecture back to a focused single-purpose tool.

**Current Status**: Simplified to single-file tools after discovering the complexity of Tencent Document's protobuf data format.

## Development Commands

### Running the Tools
```bash
# Recommended: Playwright-based exporter (works with real table content)
python tencent_csv_playwright.py "https://docs.qq.com/sheet/YOUR_DOC_URL"

# Basic API exporter (limited functionality, metadata only)
python simple_csv_exporter.py "https://docs.qq.com/sheet/YOUR_DOC_URL"

# Legacy testing tool
python tencent_doc_api_tester.py
```

### Dependencies
```bash
# For Playwright version (recommended)
pip install playwright requests
playwright install chromium

# For API version
pip install requests
```

### Testing and Development
```bash
# Test with a sample document (visible browser for debugging)
python tencent_csv_playwright.py "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2" --visible

# Test with authentication
python tencent_csv_playwright.py "YOUR_DOC_URL" -c "your_cookies_here" --visible

# Test with custom output filename
python tencent_csv_playwright.py "YOUR_DOC_URL" -o "custom_name.csv"

# Complete parameter list for Playwright version:
# --visible: Show browser window (for debugging)
# -c, --cookies: Authentication cookies
# -o, --output: Custom output filename
# --timeout: Custom timeout in seconds (default: 60)

# Complete parameter list for API version:
# -c, --cookies: Authentication cookies  
# -o, --output: Custom output filename
# --debug: Enable debug output
```

## MCP Tools Usage

### Excel MCP Server - AI 必读指南
**⚠️ 使用 Excel MCP 前必须阅读**: @EXCEL_MCP_AI_GUIDE.md

**核心要点**:
1. **参数陷阱**: `create_table` 使用 `data_range` (不是 `range`)
2. **路径格式**: 使用正斜杠 `"D:/path/file.xlsx"`  
3. **标准流程**: metadata → read → write → format → advanced
4. **常用工具**: `read_data_from_excel`, `write_data_to_excel`, `format_range`, `create_table`
5. **错误处理**: 检查参数名、路径格式、工作表名称

关键操作示例：
```javascript
// 读取文件
get_workbook_metadata({filepath: "file.xlsx"})
read_data_from_excel({filepath: "file.xlsx", sheet_name: "Sheet1"})

// 写入数据  
write_data_to_excel({filepath: "file.xlsx", sheet_name: "Sheet1", data: [["A","B"], ["1","2"]]})

// 格式化
format_range({filepath: "file.xlsx", sheet_name: "Sheet1", range: "A1:B1", 
  format_options: {font: {bold: true}, fill: {start_color: "4472C4"}}})

// 创建表格（注意 data_range 参数！）
create_table({filepath: "file.xlsx", sheet_name: "Sheet1", data_range: "A1:B2"})
```

### 其他 MCP 工具
For detailed Excel MCP usage, see: @EXCEL_MCP_USAGE_GUIDE.md

**Important**: Use `data_range` parameter for `create_table` (not `range`)

## Code Architecture

### Current Implementation (Simplified)

1. **tencent_csv_playwright.py** - Main tool using browser automation
   - Uses Playwright for real content extraction
   - Handles authentication via cookies
   - Multiple extraction strategies for different table formats

2. **simple_csv_exporter.py** - API-based version (limited)
   - Direct API calls to Tencent Document API
   - Limited by protobuf data encoding (only extracts metadata)
   - Kept for reference and potential future protobuf decoding

3. **tencent_doc_api_tester.py** - Original testing tool
   - Legacy code for API endpoint testing
   - Contains useful URL parsing utilities

### Key Technical Insights

**Why Playwright instead of API**:
- Tencent Documents use protobuf encoding for table data
- Direct API responses contain encoded binary data, not readable JSON
- Browser automation gets the rendered content after client-side decoding

**Authentication**:
- Cookie-based authentication works for both approaches
- No official API keys or OAuth required for public documents
- For private/protected documents, get cookies from browser F12 Developer Tools → Network tab
- Cookie format: "cookie1=value1; cookie2=value2"

### Data Extraction Strategy

The Playwright version uses multiple fallback methods in sequence:
1. **DOM parsing**: Search for table cells using selectors like `[class*="cell"]`, `[class*="grid"]`, `.dox-table td`
2. **Clipboard method**: Use Ctrl+A and Ctrl+C to copy content, then parse clipboard text
3. **Text extraction**: Fallback to `page.text_content()` and parse raw text

**Implementation Details**:
- Each method has timeout and error handling
- Data is structured as rows/columns or flat text depending on extraction method
- CSV output format: `tencent_doc_{doc_id}_{tab_id}.csv`
- Default timeout: 60 seconds for page load, 3 seconds for table loading

### Error Handling Patterns

Common error scenarios and their handling:
- **Page load timeout**: Retry with visible browser to diagnose
- **Empty data extraction**: Check document permissions and try different selectors
- **Authentication failures**: Verify cookie format and expiration
- **Clipboard API restrictions**: Automatically falls back to DOM parsing
- **Complex table structures**: May require manual parsing adjustments

## Archived Components

The `archive/` directory contains:
- `deprecated_microservices/` - Previous over-engineered backend architecture
- `deprecated_tests/` - Unit tests for the complex architecture
- `architecture-decisions.md` - Marked as deprecated but kept for reference

These were removed after realizing the solution was over-engineered for the simple requirement of CSV export.

## Known Limitations

1. **API version cannot decode table content** - Protobuf parsing would require reverse engineering
2. **Playwright version depends on browser** - Slower but more reliable
3. **Complex tables may need manual parsing** - Some formatting might be lost in CSV conversion

## Development Guidelines

When modifying this codebase:
- **Focus on the Playwright version** (`tencent_csv_playwright.py`) for actual functionality
- **Keep the API version** (`simple_csv_exporter.py`) for educational purposes and potential protobuf research
- **Avoid over-engineering** - This project was simplified from a complex microservices architecture (see `archive/` directory)
- **Test with real URLs** - Use actual Tencent Document URLs to verify functionality
- **Handle Chinese content** - This is a Chinese-language tool; ensure proper UTF-8 encoding for CSV output

### Debugging Workflow
1. Use `--visible` flag to see browser behavior
2. Check console output for extraction method used
3. Verify document accessibility without authentication first
4. Test with cookies if authentication is required
5. Check CSV output format and encoding

### Code Modification Strategy
- **Playwright selectors**: Modify the selector list in `extract_table_data()` if new table formats are encountered
- **Timeout adjustments**: Increase timeouts for slow-loading documents
- **Authentication**: Cookie parsing logic is in `login_with_cookies()` method
- **Output formatting**: CSV generation logic handles Chinese characters and special formatting

**Important**: This is a Chinese-language tool - URLs, comments, and README are in Chinese
CSV files are saved with format: `tencent_doc_{doc_id}_{tab_id}.csv` in current directory

## Troubleshooting

### Common Issues
1. **"未能提取到表格数据" (No table data extracted)** - Check URL format and document permissions
2. **Authentication failures** - Verify cookie format and expiration
3. **Playwright installation issues** - Run `playwright install chromium`
4. **Empty CSV output** - Document may require login cookies or have complex table structure

### Debugging Commands
```bash
# Run with visible browser to see what's happening
python tencent_csv_playwright.py "YOUR_URL" --visible

# Check if document is accessible
python tencent_doc_api_tester.py
```