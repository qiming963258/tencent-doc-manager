
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// 导入解密器
const TencentEJSDecoder = require('/root/projects/tencent-doc-manager/complete_ejs_decoder.js');

async function decryptSingleFile() {
    const decoder = new TencentEJSDecoder();
    const result = await decoder.decodeEJSFile('/root/projects/tencent-doc-manager/real_test_results/DRHZrS1hOS3pwRGZB_CSV_20250828_102630.ejs');
    
    if (result.success) {
        console.log(`✅ 解密成功: ${result.csvFile}`);
    } else {
        console.log(`❌ 解密失败: ${result.error}`);
    }
}

decryptSingleFile().catch(console.error);
