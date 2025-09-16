# 数据流和API接口规格书

## 1. 数据流总体设计

### 1.1 端到端数据流管道

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        完整数据处理流水线                                      │
│                                                                            │
│  UI参数输入     文档采集     自适应对比     AI语义分析     Excel标记     文档上传 │
│      ↓            ↓           ↓            ↓            ↓           ↓    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │动态参数 │  │N个表格  │  │智能匹配  │  │Claude API│  │MCP标记  │  │腾讯文档│ │
│  │配置体系 │  │并发下载 │  │风险评估  │  │语义判断  │  │可视化   │  │自动上传│ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────┘ │
│      │            │           │            │            │           │    │
│      └────────────┼───────────┼────────────┼────────────┼───────────┘    │
│                   │           │            │            │                │
│              ┌─────▼───────────▼────────────▼────────────▼─────┐          │
│              │             数据处理引擎                        │          │
│              │   - 格式标准化   - 风险分级   - 结果缓存     │          │
│              └─────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流阶段详细说明

#### 阶段1: UI参数配置和输入
```javascript
// 基于refer/ui参数.txt的5200+参数体系
const UIParameterFlow = {
  // 表格基础信息输入 (动态N个表格 × 8个字段 = N*8个参数)
  tableBasicInfo: {
    tableCount: documents.length,  // 动态文档数量
    tables: [
      {
        tableId: "table_001",
        tableName: "项目管理主计划表",
        tableUrl: "https://docs.qq.com/sheet/...",
        totalRows: 45,
        owner: "张三",
        department: "产品部"
      }
      // ... 根据配置动态加载更多表格
    ]
  },
  
  // 热力图核心数据配置 (N×19矩阵 = N*19个数据点)
  heatmapConfig: {
    matrixSize: [documents.length, 19],  // 动态矩阵大小
    standardColumns: [
      "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
      // ... 完整19列配置
    ],
    columnRiskLevels: {
      "来源": "L1", "目标对齐": "L1", // ... L1列配置
      "负责人": "L2", "具体计划内容": "L2", // ... L2列配置  
      "序号": "L3", "复盘时间": "L3" // ... L3列配置
    }
  },
  
  // 修改模式配置 (N个表格 × 19列的详细分布模式)
  modificationPatterns: {
    // 每个表格每列的修改分布详情
    "table_001": {
      "来源": {
        totalRows: 35,
        modifiedRows: 7,
        modificationRate: 0.2,
        modifiedRowNumbers: [2, 5, 8, 15, 23, 28, 33],
        pattern: "top_heavy",
        riskLevel: "L1"
      }
      // ... 其他列配置
    }
    // ... 其他表格配置
  }
};
```

#### 阶段2: 批量文档采集
```python
# 基于现有tencent_export_automation.py扩展
class EnhancedDocumentCollector:
    """增强的文档采集器"""
    
    async def batch_collect_documents(self, table_configs, user_cookies):
        """批量采集30+个腾讯文档"""
        tasks = []
        for table_config in table_configs:
            task = self.collect_single_document(
                url=table_config['tableUrl'],
                table_id=table_config['tableId'],
                expected_columns=table_config.get('expectedColumns'),
                cookies=user_cookies
            )
            tasks.append(task)
        
        # 并发处理，最大10个并发
        semaphore = asyncio.Semaphore(10)
        async def bounded_collect(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[bounded_collect(task) for task in tasks])
        return self.process_collection_results(results)
    
    async def collect_single_document(self, url, table_id, expected_columns, cookies):
        """单个文档采集增强版"""
        try:
            # Playwright自动化采集
            page = await self.browser.new_page()
            await page.goto(url)
            
            # Cookie认证
            if cookies:
                await self.login_with_cookies(page, cookies)
            
            # 多策略数据提取
            extraction_results = await self.multi_strategy_extraction(
                page, expected_columns
            )
            
            return {
                "table_id": table_id,
                "url": url,
                "data": extraction_results['data'],
                "actual_columns": extraction_results['columns'],
                "total_rows": extraction_results['row_count'],
                "extraction_method": extraction_results['method'],
                "quality_score": extraction_results['quality'],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "table_id": table_id,
                "error": str(e),
                "status": "failed"
            }
```

#### 阶段3: 自适应表格对比
```python
# 基于现有document_change_analyzer.py的智能扩展
class AdaptiveTableComparator:
    """自适应表格对比引擎"""
    
    def __init__(self):
        self.column_standardizer = ColumnStandardizer()
        self.intelligent_matcher = IntelligentColumnMatcher()
        self.risk_assessor = RiskAssessmentEngine()
    
    def adaptive_compare_tables(self, current_data_batch, reference_data_batch):
        """自适应对比N个表格的批量处理（动态数量）"""
        comparison_results = []
        
        for i, (current_table, reference_table) in enumerate(
            zip(current_data_batch, reference_data_batch)
        ):
            # 步骤1: 智能列匹配
            column_mapping = self.intelligent_matcher.match_columns(
                current_columns=current_table['actual_columns'],
                expected_columns=self.standard_columns,
                table_name=current_table.get('table_name', f'表格{i+1}')
            )
            
            # 步骤2: 数据标准化 
            standardized_current = self.column_standardizer.standardize(
                data=current_table['data'],
                column_mapping=column_mapping,
                fill_missing=True
            )
            
            standardized_reference = self.column_standardizer.standardize(
                data=reference_table['data'] if reference_table else None,
                column_mapping=column_mapping,
                fill_missing=True
            )
            
            # 步骤3: 深度对比分析
            comparison_result = self.deep_compare_analysis(
                current=standardized_current,
                reference=standardized_reference,
                table_id=current_table['table_id'],
                column_mapping=column_mapping
            )
            
            comparison_results.append(comparison_result)
        
        return {
            "batch_comparison_results": comparison_results,
            "global_statistics": self.calculate_global_stats(comparison_results),
            "processing_summary": self.generate_processing_summary(comparison_results)
        }
    
    def deep_compare_analysis(self, current, reference, table_id, column_mapping):
        """深度对比分析单个表格"""
        modifications = []
        
        for col_index, column_name in enumerate(self.standard_columns):
            if column_name not in column_mapping:
                continue
                
            current_col_data = current[:, col_index] if current.shape[1] > col_index else None
            reference_col_data = reference[:, col_index] if reference and reference.shape[1] > col_index else None
            
            # 列级别对比
            column_changes = self.compare_column_data(
                current_data=current_col_data,
                reference_data=reference_col_data,
                column_name=column_name,
                risk_level=self.column_risk_levels.get(column_name, 'L2')
            )
            
            if column_changes['has_changes']:
                modifications.extend(column_changes['change_details'])
        
        return {
            "table_id": table_id,
            "total_modifications": len(modifications),
            "modifications_by_risk": self.group_by_risk_level(modifications),
            "modification_details": modifications,
            "table_risk_score": self.calculate_table_risk_score(modifications),
            "requires_ai_analysis": self.check_ai_analysis_requirement(modifications)
        }
```

#### 阶段4: AI语义分析
```python
# Claude Sonnet API集成的语义分析服务
class AISemanticAnalysisService:
    """AI语义分析服务"""
    
    def __init__(self, claude_api_key):
        self.claude_client = ClaudeAPIClient(api_key=claude_api_key)
        self.prompt_engine = SemanticAnalysisPromptEngine()
        self.result_cache = Redis(host='localhost', port=6379, db=1)
    
    async def batch_semantic_analysis(self, l2_modifications):
        """批量处理L2级别修改的语义分析"""
        analysis_tasks = []
        
        for modification in l2_modifications:
            if modification['risk_level'] == 'L2':
                # 检查缓存
                cache_key = self.generate_cache_key(modification)
                cached_result = self.result_cache.get(cache_key)
                
                if cached_result:
                    analysis_tasks.append(json.loads(cached_result))
                else:
                    # 创建AI分析任务
                    task = self.analyze_single_modification(modification)
                    analysis_tasks.append(task)
        
        # 并发执行AI分析（限制并发数避免API限流）
        semaphore = asyncio.Semaphore(5)  # 最大5个并发AI请求
        
        async def bounded_analysis(task_or_result):
            if asyncio.iscoroutine(task_or_result):
                async with semaphore:
                    return await task_or_result
            else:
                return task_or_result  # 已缓存的结果
        
        analysis_results = await asyncio.gather(
            *[bounded_analysis(task) for task in analysis_tasks]
        )
        
        return self.consolidate_analysis_results(analysis_results)
    
    async def analyze_single_modification(self, modification):
        """单个修改的语义分析"""
        # 构建专业的分析提示词
        analysis_prompt = self.prompt_engine.build_semantic_analysis_prompt(
            table_name=modification['table_name'],
            column_name=modification['column_name'],
            original_value=modification['original_value'],
            new_value=modification['new_value'],
            change_context=modification['context'],
            business_rules=self.get_business_rules(modification['column_name'])
        )
        
        try:
            # 调用Claude API
            response = await self.claude_client.analyze_text(
                prompt=analysis_prompt,
                max_tokens=500,
                temperature=0.1  # 低温度确保分析的一致性
            )
            
            analysis_result = self.parse_ai_response(response, modification)
            
            # 缓存结果 (24小时TTL)
            cache_key = self.generate_cache_key(modification)
            self.result_cache.setex(
                cache_key, 
                86400,  # 24小时
                json.dumps(analysis_result)
            )
            
            return analysis_result
            
        except Exception as e:
            # AI服务失败时的降级处理
            return self.fallback_rule_based_analysis(modification)
    
    def parse_ai_response(self, ai_response, original_modification):
        """解析AI分析响应"""
        try:
            # 假设AI返回结构化的分析结果
            parsed_response = json.loads(ai_response['content'])
            
            return {
                "modification_id": original_modification['id'],
                "ai_recommendation": parsed_response.get('recommendation', 'REVIEW'),  # APPROVE/REJECT/REVIEW
                "confidence_score": parsed_response.get('confidence', 0.5),
                "reasoning": parsed_response.get('reasoning', ''),
                "business_impact": parsed_response.get('business_impact', 'MEDIUM'),
                "suggested_action": parsed_response.get('suggested_action', ''),
                "analysis_timestamp": datetime.now().isoformat(),
                "ai_model": "claude-sonnet"
            }
        except Exception:
            # 解析失败时的安全默认值
            return {
                "modification_id": original_modification['id'],
                "ai_recommendation": "REVIEW",
                "confidence_score": 0.0,
                "reasoning": "AI分析解析失败，需要人工审核",
                "analysis_timestamp": datetime.now().isoformat(),
                "error": "parsing_failed"
            }
```

#### 阶段5: Excel MCP可视化标记
```python
# 基于CLAUDE.md Excel MCP指南的可视化标记实现
class ExcelMCPVisualizationService:
    """Excel MCP可视化标记服务"""
    
    def __init__(self):
        self.excel_mcp_client = self.initialize_excel_mcp()
        self.marking_engine = HalfDiagonalMarkingEngine()
        
    async def create_visualization_report(self, comparison_results, ai_analysis_results):
        """创建可视化标记报告"""
        
        # 步骤1: 创建新的Excel工作簿
        report_filepath = f"./downloads/风险分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 使用Excel MCP创建工作簿
        await self.excel_mcp_client.write_data_to_excel({
            "filepath": report_filepath.replace('/', '\\'),  # Windows路径格式
            "sheet_name": "风险总览",
            "data": [["表格名称", "L1风险", "L2风险", "L3风险", "AI建议", "总体状态"]]
        })
        
        # 步骤2: 生成各表格的详细标记
        for table_result in comparison_results['batch_comparison_results']:
            await self.create_table_risk_sheet(
                filepath=report_filepath,
                table_result=table_result,
                ai_results=ai_analysis_results.get(table_result['table_id'], {})
            )
        
        # 步骤3: 应用专业的视觉格式化
        await self.apply_professional_formatting(report_filepath)
        
        return {
            "report_filepath": report_filepath,
            "total_tables": len(comparison_results['batch_comparison_results']),
            "high_risk_count": self.count_high_risk_tables(comparison_results),
            "ai_analysis_count": len(ai_analysis_results)
        }
    
    async def create_table_risk_sheet(self, filepath, table_result, ai_results):
        """为单个表格创建风险标记工作表"""
        sheet_name = f"{table_result['table_id'][:10]}_风险分析"
        
        # 准备基础数据矩阵 (30行 × 19列标准格式)
        risk_matrix = self.build_risk_matrix(table_result, ai_results)
        
        # 写入数据
        await self.excel_mcp_client.write_data_to_excel({
            "filepath": filepath.replace('/', '\\'),
            "sheet_name": sheet_name,
            "data": risk_matrix
        })
        
        # 应用半填充对角线标记
        await self.apply_half_diagonal_marking(
            filepath=filepath,
            sheet_name=sheet_name,
            modifications=table_result['modification_details']
        )
    
    async def apply_half_diagonal_marking(self, filepath, sheet_name, modifications):
        """应用半填充对角线图案标记"""
        
        for mod in modifications:
            if mod['risk_level'] in ['L1', 'L2']:  # 只标记高风险修改
                cell_range = f"{self.column_index_to_letter(mod['column_index'])}{mod['row_number']}"
                
                # 根据风险等级选择颜色和图案
                if mod['risk_level'] == 'L1':
                    # L1: 深红色半填充对角线
                    format_options = {
                        "fill": {
                            "pattern_type": "lightUp",  # 对角线图案
                            "start_color": "DC2626",    # 深红色
                            "pattern_color": "FFFFFF"   # 白色对角线
                        },
                        "border": {
                            "style": "thick",
                            "color": "DC2626"
                        },
                        "font": {
                            "bold": True,
                            "color": "DC2626"
                        }
                    }
                else:  # L2
                    # L2: 橙色半填充对角线
                    format_options = {
                        "fill": {
                            "pattern_type": "lightUp",
                            "start_color": "F59E0B",    # 橙色
                            "pattern_color": "FFFFFF"
                        },
                        "border": {
                            "style": "medium", 
                            "color": "F59E0B"
                        },
                        "font": {
                            "bold": True,
                            "color": "F59E0B"
                        }
                    }
                
                # 应用格式化
                await self.excel_mcp_client.format_range({
                    "filepath": filepath.replace('/', '\\'),
                    "sheet_name": sheet_name,
                    "range": cell_range,
                    "format_options": format_options
                })
                
                # 添加批注说明
                comment_text = self.generate_modification_comment(mod)
                await self.excel_mcp_client.add_comment({
                    "filepath": filepath.replace('/', '\\'),
                    "sheet_name": sheet_name, 
                    "cell": cell_range,
                    "comment": comment_text
                })
```

#### 阶段6: 腾讯文档自动上传
```python
# 基于现有tencent_upload_automation.py扩展
class EnhancedTencentDocUploader:
    """增强的腾讯文档上传服务"""
    
    async def upload_marked_reports_batch(self, report_files, user_credentials):
        """批量上传标记后的Excel报告到腾讯文档"""
        
        upload_results = []
        
        for report_file in report_files:
            try:
                # 上传单个报告文件
                upload_result = await self.upload_single_report(
                    file_path=report_file['filepath'],
                    target_folder="风险分析报告",
                    user_cookies=user_credentials['cookies'],
                    description=f"自动生成的风险分析报告 - {report_file['timestamp']}"
                )
                
                upload_results.append({
                    "local_filepath": report_file['filepath'],
                    "tencent_doc_url": upload_result['document_url'],
                    "upload_status": "success",
                    "upload_timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                upload_results.append({
                    "local_filepath": report_file['filepath'],
                    "error": str(e),
                    "upload_status": "failed"
                })
        
        return {
            "total_reports": len(report_files),
            "successful_uploads": len([r for r in upload_results if r.get('upload_status') == 'success']),
            "failed_uploads": len([r for r in upload_results if r.get('upload_status') == 'failed']),
            "upload_details": upload_results
        }
```

## 2. API接口详细规格

### 2.1 核心API端点设计

#### 2.1.1 热力图数据API
```python
@app.route('/api/v1/heatmap/data', methods=['GET'])
def get_heatmap_data():
    """
    获取N×19动态热力图数据矩阵
    
    Query Parameters:
    - user_id: 用户ID (必需)
    - time_range: 时间范围 (可选, 默认24h)
    - table_filter: 表格过滤条件 (可选)
    
    Response:
    {
        "success": true,
        "data": {
            "matrix_data": [[0.85, 0.65, ...], ...],  // N×19动态矩阵
            "table_names": ["项目管理主计划表", ...],
            "column_names": ["序号", "项目类型", ...],
            "risk_levels": {"来源": "L1", ...},
            "statistics": {
                "total_modifications": 156,
                "l1_modifications": 12,
                "l2_modifications": 45, 
                "l3_modifications": 99,
                "highest_risk_table": "项目管理主计划表",
                "most_modified_column": "具体计划内容"
            }
        },
        "generated_at": "2025-01-15T10:30:00Z",
        "cache_expires": "2025-01-15T11:30:00Z"
    }
    """
    
@app.route('/api/v1/heatmap/patterns', methods=['GET'])  
def get_modification_patterns():
    """
    获取表格内修改分布模式数据
    
    Query Parameters:
    - table_id: 特定表格ID (可选)
    - column_name: 特定列名 (可选)
    
    Response:
    {
        "success": true,
        "patterns": {
            "table_001": {
                "来源": {
                    "total_rows": 35,
                    "modified_rows": 7,
                    "modified_row_numbers": [2, 5, 8, 15, 23, 28, 33],
                    "row_intensities": {2: 0.8, 5: 0.6, ...},
                    "pattern": "top_heavy",
                    "median_row": 15,
                    "risk_level": "L1"
                }
            }
        },
        "global_max_rows": 50
    }
    """
```

#### 2.1.2 自适应对比API
```python
@app.route('/api/v1/adaptive/compare', methods=['POST'])
def adaptive_table_compare():
    """
    自适应表格对比分析
    
    Request Body:
    {
        "table_urls": ["https://docs.qq.com/sheet/...", ...],
        "reference_data": {...},  // 可选基准数据
        "comparison_config": {
            "enable_intelligent_matching": true,
            "tolerance_threshold": 0.1,
            "include_ai_analysis": true
        },
        "user_credentials": {
            "username": "user123",
            "encrypted_cookies": "..."
        }
    }
    
    Response:
    {
        "success": true,
        "job_id": "comp_20250115_103000",
        "estimated_duration": "5-10分钟",
        "tables_count": 30,
        "status": "processing",
        "progress_endpoint": "/api/v1/adaptive/compare/status/comp_20250115_103000"
    }
    """
    
@app.route('/api/v1/adaptive/compare/status/<job_id>', methods=['GET'])
def get_comparison_status(job_id):
    """
    获取对比任务状态
    
    Response:
    {
        "success": true,
        "job_id": "comp_20250115_103000",
        "status": "completed",  // processing/completed/failed
        "progress": 1.0,
        "tables_processed": 30,
        "total_tables": 30,
        "results": {
            "total_modifications": 156,
            "high_risk_modifications": 12,
            "ai_analysis_required": 45,
            "processing_summary": {
                "successful_tables": 29,
                "failed_tables": 1,
                "column_matching_accuracy": 0.96
            }
        },
        "download_urls": {
            "detailed_report": "/api/v1/reports/download/comp_20250115_103000",
            "excel_visualization": "/api/v1/visualizations/download/comp_20250115_103000"
        }
    }
    """
```

#### 2.1.3 AI语义分析API
```python
@app.route('/api/v1/ai/semantic-analysis', methods=['POST'])
def ai_semantic_analysis():
    """
    AI语义分析服务
    
    Request Body:
    {
        "modifications": [
            {
                "id": "mod_001",
                "table_name": "项目管理主计划表",
                "column_name": "负责人",
                "original_value": "张三",
                "new_value": "李四",
                "change_context": "项目重新分配",
                "risk_level": "L2"
            }
        ],
        "analysis_config": {
            "enable_cache": true,
            "confidence_threshold": 0.7,
            "business_rules": {...}
        }
    }
    
    Response:
    {
        "success": true,
        "analysis_results": [
            {
                "modification_id": "mod_001",
                "ai_recommendation": "APPROVE",  // APPROVE/REJECT/REVIEW
                "confidence_score": 0.85,
                "reasoning": "负责人变更符合项目管理流程，新负责人具备相应权限",
                "business_impact": "LOW",
                "suggested_action": "自动批准，记录变更日志",
                "analysis_timestamp": "2025-01-15T10:35:00Z"
            }
        ],
        "batch_statistics": {
            "total_analyzed": 1,
            "auto_approved": 0,
            "requires_review": 1,
            "rejected": 0,
            "average_confidence": 0.85
        }
    }
    """
```

#### 2.1.4 Excel可视化标记API
```python
@app.route('/api/v1/excel/create-visualization', methods=['POST'])
def create_excel_visualization():
    """
    创建Excel可视化标记报告
    
    Request Body:
    {
        "comparison_results": {...},
        "ai_analysis_results": {...},
        "visualization_config": {
            "include_heatmap": true,
            "mark_high_risk_only": false,
            "add_summary_charts": true,
            "format_style": "professional"
        }
    }
    
    Response:
    {
        "success": true,
        "report_info": {
            "filepath": "./downloads/风险分析报告_20250115_103500.xlsx",
            "file_size": "2.5MB",
            "sheet_count": documents.length + 1,  // N个表格 + 1个总览
            "total_markings": 67,
            "high_risk_markings": 12
        },
        "download_url": "/api/v1/excel/download/风险分析报告_20250115_103500.xlsx",
        "preview_url": "/api/v1/excel/preview/风险分析报告_20250115_103500.xlsx"
    }
    """
```

#### 2.1.5 批量上传API
```python
@app.route('/api/v1/tencent-docs/upload-reports', methods=['POST'])
def upload_reports_to_tencent():
    """
    批量上传报告到腾讯文档
    
    Request Body:
    {
        "report_files": [
            {
                "filepath": "./downloads/风险分析报告_20250115_103500.xlsx",
                "target_folder": "风险分析报告",
                "description": "2025-01-15 自动生成的风险分析报告"
            }
        ],
        "user_credentials": {
            "username": "user123",
            "encrypted_cookies": "..."
        },
        "upload_config": {
            "overwrite_existing": true,
            "notify_on_completion": true
        }
    }
    
    Response:
    {
        "success": true,
        "upload_job_id": "upload_20250115_104000",
        "total_files": 1,
        "estimated_duration": "2-3分钟",
        "status_endpoint": "/api/v1/tencent-docs/upload-status/upload_20250115_104000"
    }
    """
```

### 2.2 实时状态和通知API

#### 2.2.1 WebSocket实时通信
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('subscribe_job_updates')
def handle_job_subscription(data):
    """订阅任务状态更新"""
    job_id = data['job_id']
    user_id = data['user_id']
    
    # 加入任务状态房间
    join_room(f"job_{job_id}")
    emit('subscription_confirmed', {
        'job_id': job_id,
        'status': 'subscribed'
    })

def notify_job_progress(job_id, progress_data):
    """通知任务进度更新"""
    socketio.emit('job_progress_update', {
        'job_id': job_id,
        'progress': progress_data['progress'],
        'current_step': progress_data['current_step'],
        'message': progress_data['message'],
        'timestamp': datetime.now().isoformat()
    }, room=f"job_{job_id}")
```

#### 2.2.2 任务状态查询API
```python
@app.route('/api/v1/jobs/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """通用任务状态查询"""
    
@app.route('/api/v1/jobs/list', methods=['GET'])
def list_user_jobs():
    """用户任务列表"""
    
@app.route('/api/v1/jobs/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """取消任务"""
```

### 2.3 配置和管理API

#### 2.3.1 系统配置API
```python
@app.route('/api/v1/config/ui-parameters', methods=['GET', 'POST'])
def manage_ui_parameters():
    """管理UI参数配置"""
    
@app.route('/api/v1/config/risk-levels', methods=['GET', 'POST'])
def manage_risk_level_config():
    """管理风险等级配置"""
    
@app.route('/api/v1/config/ai-settings', methods=['GET', 'POST']) 
def manage_ai_settings():
    """管理AI分析设置"""
```

#### 2.3.2 链接管理API（支持软删除）
```python
@app.route('/api/save-download-links', methods=['POST'])
def save_download_links():
    """保存下载链接配置（支持软删除）
    
    功能特性：
    - 保留历史链接记录
    - 软删除机制：删除的链接移至deleted_links数组
    - 自动记录删除时间戳
    
    请求体：
    {
        "links": [
            {"url": "string", "name": "string", "enabled": boolean}
        ]
    }
    
    响应：
    {
        "success": boolean,
        "message": "string",
        "links_count": integer
    }
    
    存储格式：
    {
        "document_links": [...],     # 活跃链接
        "deleted_links": [...],       # 软删除的链接（带deleted_at时间戳）
        "last_updated": "ISO8601"
    }
    """
    
@app.route('/api/get-download-links', methods=['GET'])
def get_download_links():
    """获取下载链接配置（仅返回活跃链接）"""
```

#### 2.3.3 基线文件管理API
```python
@app.route('/api/baseline-files', methods=['GET', 'POST', 'DELETE'])
def handle_baseline_files():
    """处理基线文件的CRUD操作
    
    GET - 获取基线文件列表
    响应：
    {
        "success": boolean,
        "files": [
            {
                "name": "string",
                "path": "string",
                "size": integer,
                "modified": "ISO8601"
            }
        ],
        "week": integer,        # 当前ISO周数
        "path": "string"        # 基线文件夹路径
    }
    
    POST - 下载并保存基线文件
    请求体：
    {
        "url": "string",        # 腾讯文档URL（支持多行输入）
        "urls": ["string"],     # 批量URL数组（可选）
        "cookie": "string",     # 认证Cookie
        "week": integer         # 指定周数（可选）
    }
    响应：
    {
        "success": boolean,
        "file": {
            "name": "string",
            "path": "string"
        },
        "error": "string"       # 失败时的错误信息
    }

    DELETE - 软删除基线文件
    请求体：
    {
        "filename": "string"
    }
    响应：
    {
        "success": boolean,
        "message": "string"
    }
    
    存储路径：
    /root/projects/tencent-doc-manager/csv_versions/
    └── 2025_W{周数}/
        └── baseline/
            ├── tencent_{文档名}_{时间戳}_baseline_W{周数}.csv
            ├── tencent_{文档名}_{时间戳}_baseline_W{周数}.xlsx
            └── .deleted/       # 软删除文件夹（隐藏目录）
                └── deleted_{YYYYMMDD_HHMMSS}_{原文件名}

    软删除机制：
    - 新文件下载时自动检查同名文件
    - 旧文件移动到.deleted文件夹并添加删除时间戳
    - 软删除文件不被查找函数发现
    - 支持历史版本追溯
    """

## 3. 数据格式规范

### 3.1 标准数据交换格式

#### 3.1.1 表格数据格式
```json
{
  "table_metadata": {
    "table_id": "string",
    "table_name": "string", 
    "table_url": "string",
    "total_rows": "integer",
    "actual_columns": ["string"],
    "extraction_timestamp": "ISO8601",
    "data_quality_score": "float[0-1]"
  },
  "table_data": [
    ["序号", "项目类型", "来源", ...],  // 标题行
    ["1", "新产品开发", "产品部", ...],  // 数据行
    // ...
  ],
  "column_mapping": {
    "actual_column_name": "standard_column_name"
  }
}
```

#### 3.1.2 修改记录格式
```json
{
  "modification_id": "string",
  "table_id": "string",
  "column_name": "string",
  "row_number": "integer", 
  "original_value": "any",
  "new_value": "any",
  "change_type": "enum[insert|update|delete]",
  "risk_level": "enum[L1|L2|L3]",
  "modification_intensity": "float[0-1]",
  "change_timestamp": "ISO8601",
  "modifier": "string",
  "context": {
    "surrounding_changes": "array",
    "business_context": "string"
  }
}
```

### 3.2 API响应标准格式

#### 3.2.1 成功响应格式
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "ISO8601",
    "request_id": "string",
    "processing_time_ms": "integer"
  }
}
```

#### 3.2.2 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {},
    "suggestion": "建议解决方案"
  },
  "meta": {
    "timestamp": "ISO8601",
    "request_id": "string"
  }
}
```

## 4. 性能和扩展性考虑

### 4.1 API性能指标
- **响应时间**: 
  - 简单查询API < 200ms
  - 复杂分析API < 5秒
  - 批量处理 < 10分钟/30表格
  
- **并发处理能力**:
  - 同时处理用户数: 50+
  - API请求并发: 500/秒
  - 文档处理并发: 10个/用户

### 4.2 数据缓存策略
- **Redis缓存层级**:
  - L1: 热力图数据 (TTL: 1小时)
  - L2: AI分析结果 (TTL: 24小时) 
  - L3: 用户会话 (TTL: 8小时)

### 4.3 API版本管理
- 使用语义化版本 (v1.0.0)
- 向后兼容保证
- 废弃API的迁移计划

---

**文档版本**: v1.0  
**创建时间**: 2025-01-15  
**基于组件**: Flask app.py + 自适应对比算法 + AI集成  
**维护人员**: API开发团队