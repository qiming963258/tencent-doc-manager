#!/usr/bin/env node
/**
 * 测试是否能用标准EJS库解析腾讯文档的数据
 */

const fs = require('fs');
const path = require('path');

// 尝试不同的解析方法
function parseEJSFile(filePath) {
    console.log('\n' + '='.repeat(60));
    console.log(`解析文件: ${path.basename(filePath)}`);
    console.log('='.repeat(60));
    
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    console.log(`文件行数: ${lines.length}`);
    
    // 分析EJS格式结构
    let currentSection = '';
    let jsonData = null;
    let workbookData = null;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line === 'head') {
            console.log('找到: EJS头部标识');
            currentSection = 'head';
        } else if (line === 'json') {
            console.log('找到: JSON段标识');
            currentSection = 'json';
        } else if (line === 'text') {
            console.log('找到: 文本段标识');
            currentSection = 'text';
        } else if (/^\d+$/.test(line)) {
            const length = parseInt(line);
            console.log(`找到: 数据长度标识 (${length} 字符)`);
            
            // 读取下一行的数据
            if (i + 1 < lines.length) {
                const dataLine = lines[i + 1];
                
                if (currentSection === 'json' && dataLine.startsWith('{')) {
                    try {
                        jsonData = JSON.parse(dataLine);
                        console.log('✅ JSON解析成功');
                        console.log(`  Keys: ${Object.keys(jsonData).slice(0, 5).join(', ')}`);
                        
                        // 检查bodyData
                        if (jsonData.bodyData) {
                            console.log('  找到bodyData:');
                            console.log(`    标题: ${jsonData.bodyData.initialTitle || 'N/A'}`);
                        }
                    } catch (e) {
                        console.log('❌ JSON解析失败');
                    }
                } else if (dataLine.startsWith('%7B')) {
                    // URL编码的数据
                    console.log('找到: URL编码数据');
                    try {
                        const decoded = decodeURIComponent(dataLine);
                        const data = JSON.parse(decoded);
                        console.log('✅ URL解码并解析成功');
                        console.log(`  Keys: ${Object.keys(data).slice(0, 5).join(', ')}`);
                        
                        if (data.workbook) {
                            workbookData = data.workbook;
                            console.log(`  Workbook长度: ${workbookData.length}`);
                            
                            // 尝试Base64解码
                            try {
                                const buffer = Buffer.from(workbookData, 'base64');
                                console.log(`  Base64解码: ${buffer.length} bytes`);
                                
                                // 检查是否是zlib压缩
                                if (buffer[0] === 0x78) {
                                    console.log('  检测到zlib压缩标志');
                                    
                                    // 尝试zlib解压
                                    const zlib = require('zlib');
                                    try {
                                        const uncompressed = zlib.inflateSync(buffer);
                                        console.log(`  ✅ zlib解压成功: ${uncompressed.length} bytes`);
                                        
                                        // 尝试转换为字符串
                                        const text = uncompressed.toString('utf8');
                                        console.log(`  数据预览: ${text.substring(0, 200)}...`);
                                        
                                        // 保存解压后的数据
                                        const outputFile = filePath.replace(/\.(csv|xlsx)$/, '_nodejs_decoded.txt');
                                        fs.writeFileSync(outputFile, text, 'utf8');
                                        console.log(`  💾 保存到: ${outputFile}`);
                                        
                                    } catch (zlibError) {
                                        console.log(`  ❌ zlib解压失败: ${zlibError.message}`);
                                        
                                        // 尝试其他zlib选项
                                        const methods = [
                                            { name: 'inflateRawSync', func: zlib.inflateRawSync },
                                            { name: 'gunzipSync', func: zlib.gunzipSync },
                                            { name: 'brotliDecompressSync', func: zlib.brotliDecompressSync }
                                        ];
                                        
                                        for (const method of methods) {
                                            try {
                                                console.log(`  尝试 ${method.name}...`);
                                                const result = method.func(buffer);
                                                console.log(`  ✅ ${method.name} 成功: ${result.length} bytes`);
                                                
                                                const outputFile = filePath.replace(/\.(csv|xlsx)$/, `_${method.name}.txt`);
                                                fs.writeFileSync(outputFile, result.toString('utf8'), 'utf8');
                                                console.log(`  💾 保存到: ${outputFile}`);
                                                break;
                                                
                                            } catch (e) {
                                                console.log(`  ❌ ${method.name} 失败`);
                                            }
                                        }
                                    }
                                }
                            } catch (e) {
                                console.log(`  Base64解码失败: ${e.message}`);
                            }
                        }
                        
                        // 检查其他字段
                        if (data.max_row && data.max_col) {
                            console.log(`  表格大小: ${data.max_row} × ${data.max_col}`);
                        }
                        
                    } catch (e) {
                        console.log(`❌ URL解码失败: ${e.message}`);
                    }
                }
            }
        }
    }
    
    return { jsonData, workbookData };
}

// 主函数
function main() {
    const testFiles = [
        '/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv',
        '/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_Excel格式_20250827_231720.xlsx'
    ];
    
    for (const file of testFiles) {
        if (fs.existsSync(file)) {
            parseEJSFile(file);
        } else {
            console.log(`❌ 文件不存在: ${file}`);
        }
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('测试完成');
    console.log('='.repeat(60));
}

// 运行
main();