#!/usr/bin/env node
/**
 * 完整的腾讯文档EJS格式解密工具
 * 能够处理真实的业务数据文档
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { promisify } = require('util');
const inflateAsync = promisify(zlib.inflate);

class TencentEJSDecoder {
    constructor() {
        this.debugMode = true;
    }

    /**
     * 完整解密流程
     */
    async decodeEJSFile(filePath) {
        console.log('\n' + '='.repeat(60));
        console.log(`开始解密EJS文件: ${path.basename(filePath)}`);
        console.log('='.repeat(60));

        try {
            // 1. 读取EJS文件
            const content = fs.readFileSync(filePath, 'utf8');
            const lines = content.split('\n');
            
            console.log(`文件行数: ${lines.length}`);
            
            // 2. 解析EJS结构
            const ejsData = this.parseEJSStructure(lines);
            
            // 3. 提取workbook数据
            if (ejsData.workbook) {
                const decodedData = await this.decodeWorkbook(ejsData.workbook);
                
                // 4. 解析表格数据
                const tableData = this.parseTableData(decodedData, ejsData);
                
                // 5. 生成CSV文件
                const csvFile = this.generateCSV(tableData, filePath);
                
                return {
                    success: true,
                    csvFile: csvFile,
                    rows: ejsData.max_row,
                    cols: ejsData.max_col,
                    cellCount: tableData.cells ? tableData.cells.length : 0
                };
            } else {
                throw new Error('未找到workbook数据');
            }
            
        } catch (error) {
            console.error(`解密失败: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 解析EJS文件结构
     */
    parseEJSStructure(lines) {
        const result = {
            metadata: null,
            workbook: null,
            max_row: 0,
            max_col: 0
        };

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // 查找JSON元数据
            if (line === 'json' && i + 2 < lines.length) {
                const length = parseInt(lines[i + 1]);
                const jsonStr = lines[i + 2];
                
                try {
                    result.metadata = JSON.parse(jsonStr);
                    console.log('✅ 找到JSON元数据');
                    
                    if (result.metadata.bodyData) {
                        console.log(`  文档标题: ${result.metadata.bodyData.initialTitle || 'N/A'}`);
                    }
                } catch (e) {
                    console.log('JSON解析失败');
                }
            }
            
            // 查找workbook数据
            if (line.startsWith('%7B%22workbook%22') || line.includes('workbook')) {
                console.log('✅ 找到workbook数据');
                
                try {
                    // URL解码
                    const decoded = decodeURIComponent(line);
                    const data = JSON.parse(decoded);
                    
                    result.workbook = data.workbook;
                    result.related_sheet = data.related_sheet;
                    result.max_row = data.max_row || 0;
                    result.max_col = data.max_col || 0;
                    result.end_row_index = data.end_row_index || 0;
                    result.end_col_index = data.end_col_index || 0;
                    
                    console.log(`  表格大小: ${result.max_row} 行 × ${result.max_col} 列`);
                    
                } catch (e) {
                    console.log(`URL解码失败: ${e.message}`);
                }
            }
        }
        
        return result;
    }

    /**
     * 解码workbook数据
     */
    async decodeWorkbook(workbookBase64) {
        console.log('\n解码workbook数据...');
        
        // Base64解码
        const buffer = Buffer.from(workbookBase64, 'base64');
        console.log(`  Base64解码: ${buffer.length} bytes`);
        console.log(`  前4字节: ${buffer.slice(0, 4).toString('hex')}`);
        
        // 检查压缩类型
        if (buffer[0] === 0x78) {
            console.log('  检测到zlib压缩');
            
            try {
                // zlib解压
                const decompressed = await inflateAsync(buffer);
                console.log(`  ✅ 解压成功: ${decompressed.length} bytes`);
                
                return decompressed;
                
            } catch (error) {
                console.log(`  ❌ zlib解压失败: ${error.message}`);
                
                // 尝试其他解压方法
                const methods = [
                    { name: 'inflateRaw', func: zlib.inflateRawSync },
                    { name: 'gunzip', func: zlib.gunzipSync }
                ];
                
                for (const method of methods) {
                    try {
                        console.log(`  尝试 ${method.name}...`);
                        const result = method.func(buffer);
                        console.log(`  ✅ ${method.name} 成功: ${result.length} bytes`);
                        return result;
                    } catch (e) {
                        console.log(`  ❌ ${method.name} 失败`);
                    }
                }
            }
        }
        
        // 如果不是压缩数据，直接返回
        return buffer;
    }

    /**
     * 解析表格数据（从protobuf或其他格式）
     */
    parseTableData(decodedBuffer, ejsData) {
        console.log('\n解析表格数据...');
        
        const result = {
            cells: [],
            styles: [],
            formulas: []
        };
        
        // 方法1：尝试解析protobuf结构
        result.cells = this.extractCellsFromProtobuf(decodedBuffer);
        
        // 方法2：提取文本内容
        if (result.cells.length === 0) {
            result.cells = this.extractTextContent(decodedBuffer);
        }
        
        // 方法3：使用related_sheet数据
        if (ejsData.related_sheet) {
            console.log('  处理related_sheet数据...');
            try {
                const relatedBuffer = Buffer.from(ejsData.related_sheet, 'base64');
                const relatedCells = this.extractTextContent(relatedBuffer);
                result.cells = result.cells.concat(relatedCells);
            } catch (e) {
                console.log(`  related_sheet处理失败: ${e.message}`);
            }
        }
        
        console.log(`  ✅ 提取了 ${result.cells.length} 个单元格`);
        
        return result;
    }

    /**
     * 从protobuf提取单元格
     */
    extractCellsFromProtobuf(buffer) {
        const cells = [];
        
        // 提取所有可打印的字符串
        let currentString = '';
        let stringStart = 0;
        
        for (let i = 0; i < buffer.length; i++) {
            const byte = buffer[i];
            
            if (byte >= 32 && byte <= 126) { // 可打印ASCII
                if (!currentString) stringStart = i;
                currentString += String.fromCharCode(byte);
            } else if (byte >= 0x4e00 && byte <= 0x9fff) { // 中文范围
                if (!currentString) stringStart = i;
                currentString += String.fromCharCode(byte);
            } else {
                if (currentString.length > 0) {
                    // 过滤系统信息
                    if (!this.isSystemString(currentString)) {
                        cells.push({
                            position: stringStart,
                            content: currentString,
                            type: 'text'
                        });
                    }
                    currentString = '';
                }
            }
        }
        
        // 尝试UTF-8解码
        try {
            const text = buffer.toString('utf8');
            const lines = text.split(/[\n\r\x00]+/);
            
            for (const line of lines) {
                const cleaned = line.trim();
                if (cleaned && !this.isSystemString(cleaned)) {
                    // 检查是否包含实际数据
                    if (cleaned.length > 1 && cleaned.length < 1000) {
                        cells.push({
                            content: cleaned,
                            type: 'utf8'
                        });
                    }
                }
            }
        } catch (e) {
            // 忽略UTF-8解码错误
        }
        
        return cells;
    }

    /**
     * 提取文本内容
     */
    extractTextContent(buffer) {
        const cells = [];
        
        // 尝试多种编码
        const encodings = ['utf8', 'utf16le', 'gbk'];
        
        for (const encoding of encodings) {
            try {
                let text;
                if (encoding === 'gbk') {
                    // Node.js原生不支持GBK，使用UTF-8替代
                    continue;
                } else {
                    text = buffer.toString(encoding);
                }
                
                // 查找有意义的文本
                const matches = text.match(/[\w\u4e00-\u9fff]+/g);
                if (matches) {
                    for (const match of matches) {
                        if (match.length > 1 && !this.isSystemString(match)) {
                            cells.push({
                                content: match,
                                type: encoding
                            });
                        }
                    }
                }
            } catch (e) {
                // 忽略编码错误
            }
        }
        
        return cells;
    }

    /**
     * 判断是否是系统字符串
     */
    isSystemString(str) {
        const systemKeywords = [
            'calibri', 'arial', 'times', 'font',
            '000000', 'ffffff', 'color',
            'style', 'format', 'sheet',
            'xmlns', 'http', 'version'
        ];
        
        const lower = str.toLowerCase();
        return systemKeywords.some(keyword => lower.includes(keyword));
    }

    /**
     * 生成CSV文件
     */
    generateCSV(tableData, originalFile) {
        console.log('\n生成CSV文件...');
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const csvFile = originalFile.replace(/\.(csv|xlsx)$/, `_decoded_${timestamp}.csv`);
        
        const cells = tableData.cells || [];
        
        if (cells.length === 0) {
            console.log('  ⚠️  没有找到单元格数据');
            return null;
        }
        
        // 尝试组织成表格
        const rows = [];
        let currentRow = [];
        
        for (const cell of cells) {
            currentRow.push(cell.content);
            
            // 简单规则：每20个单元格一行（可以根据实际调整）
            if (currentRow.length >= 20) {
                rows.push(currentRow);
                currentRow = [];
            }
        }
        
        if (currentRow.length > 0) {
            rows.push(currentRow);
        }
        
        // 生成CSV内容
        const csvContent = rows.map(row => 
            row.map(cell => `"${(cell || '').replace(/"/g, '""')}"`).join(',')
        ).join('\n');
        
        // 写入文件
        fs.writeFileSync(csvFile, csvContent, 'utf8');
        
        console.log(`  ✅ CSV文件已生成: ${csvFile}`);
        console.log(`  包含 ${rows.length} 行, ${cells.length} 个单元格`);
        
        return csvFile;
    }
}

/**
 * 测试真实文档
 */
async function testRealDocument() {
    const decoder = new TencentEJSDecoder();
    
    // 测试文件列表
    const testFiles = [
        '/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv',
        '/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_Excel格式_20250827_231720.xlsx'
    ];
    
    console.log('🚀 开始测试真实文档解密');
    console.log('='.repeat(60));
    
    const results = [];
    
    for (const file of testFiles) {
        if (fs.existsSync(file)) {
            const result = await decoder.decodeEJSFile(file);
            results.push({
                file: file,
                ...result
            });
        } else {
            console.log(`❌ 文件不存在: ${file}`);
        }
    }
    
    // 显示结果
    console.log('\n' + '='.repeat(60));
    console.log('测试结果总结');
    console.log('='.repeat(60));
    
    let successCount = 0;
    
    for (const result of results) {
        if (result.success) {
            console.log(`✅ ${path.basename(result.file)}`);
            console.log(`   表格: ${result.rows}×${result.cols}`);
            console.log(`   单元格: ${result.cellCount}个`);
            console.log(`   输出: ${result.csvFile}`);
            successCount++;
        } else {
            console.log(`❌ ${path.basename(result.file)}: ${result.error}`);
        }
    }
    
    if (successCount > 0) {
        console.log(`\n🎉 成功率: ${successCount}/${results.length}`);
        
        // 验证CSV文件
        for (const result of results) {
            if (result.csvFile && fs.existsSync(result.csvFile)) {
                const csvContent = fs.readFileSync(result.csvFile, 'utf8');
                const lines = csvContent.split('\n');
                console.log(`\n📄 ${path.basename(result.csvFile)} 预览:`);
                console.log(`   前3行:`);
                for (let i = 0; i < Math.min(3, lines.length); i++) {
                    console.log(`   ${i+1}: ${lines[i].substring(0, 100)}...`);
                }
            }
        }
    } else {
        console.log('\n❌ 所有测试都失败了，需要改进算法');
    }
    
    return results;
}

// 主函数
if (require.main === module) {
    testRealDocument()
        .then(results => {
            console.log('\n✅ 测试完成');
            process.exit(results.some(r => r.success) ? 0 : 1);
        })
        .catch(err => {
            console.error('❌ 测试失败:', err);
            process.exit(1);
        });
}

module.exports = TencentEJSDecoder;