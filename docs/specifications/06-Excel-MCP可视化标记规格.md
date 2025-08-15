# Excel MCP可视化标记规格书

## 1. Excel MCP集成架构

### 1.1 基于CLAUDE.md Excel MCP指南的实现

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Excel MCP可视化标记系统架构                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  数据输入层                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 对比分析结果     │  │ AI语义分析       │  │ 风险等级数据     │              │
│  │ - 字段修改详情   │  │ - L2级别判断     │  │ - L1/L2/L3分类   │              │
│  │ - 修改位置坐标   │  │ - 置信度评分     │  │ - 风险分数       │              │
│  │ - 变更上下文     │  │ - 建议操作       │  │ - 业务影响评估   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Excel MCP处理层                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 工作簿创建器     │  │ 半填充标记器     │  │ 格式化引擎       │              │
│  │ - 多工作表布局   │  │ - lightUp图案    │  │ - 颜色编码       │              │
│  │ - 标准化矩阵     │  │ - 对角线纹理     │  │ - 边框样式       │              │
│  │ - 数据导入       │  │ - 透明度设置     │  │ - 字体加粗       │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
├─────────────────────────────────────────────────────────────────────────────┤
│  可视化渲染层                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 批注系统         │  │ 图表集成         │  │ 总览仪表板       │              │
│  │ - 详细说明       │  │ - 风险分布图     │  │ - 统计摘要       │              │
│  │ - 修改建议       │  │ - 趋势分析       │  │ - 热点识别       │              │
│  │ - 审批流程       │  │ - 对比图表       │  │ - 快速导航       │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

1. **基于现有MCP指南**: 严格遵循CLAUDE.md中的Excel MCP使用规范
2. **半填充对角线专业标记**: 使用lightUp图案实现专业的视觉标记
3. **风险等级色彩编码**: L1红色、L2橙色、L3绿色的直观区分
4. **批注详细说明**: 每个标记位置提供详细的修改说明和建议
5. **多层次信息展示**: 从单元格级别到工作表级别的完整信息层次

## 2. Excel MCP API集成实现

### 2.1 基础MCP客户端
```python
# 基于CLAUDE.md Excel MCP指南的实现
class ExcelMCPVisualizationClient:
    """Excel MCP可视化标记客户端"""
    
    def __init__(self):
        # 根据CLAUDE.md指南，确保正确的参数使用
        self.mcp_functions = {
            "get_workbook_metadata": self._get_metadata,
            "read_data_from_excel": self._read_data,
            "write_data_to_excel": self._write_data,
            "format_range": self._format_range,
            "create_table": self._create_table,  # 注意：使用data_range参数！
            "add_comment": self._add_comment
        }
        
        # 风险等级的专业颜色配置
        self.risk_color_scheme = {
            "L1": {
                "fill_color": "DC2626",      # 深红色
                "pattern_color": "FFFFFF",    # 白色对角线
                "border_color": "DC2626",
                "font_color": "DC2626"
            },
            "L2": {
                "fill_color": "F59E0B",      # 橙色  
                "pattern_color": "FFFFFF",    # 白色对角线
                "border_color": "F59E0B",
                "font_color": "F59E0B"
            },
            "L3": {
                "fill_color": "10B981",      # 绿色
                "pattern_color": "FFFFFF",    # 白色对角线  
                "border_color": "10B981",
                "font_color": "10B981"
            }
        }
        
    async def create_comprehensive_risk_report(self, analysis_data, output_path):
        """
        创建全面的风险分析报告
        
        Args:
            analysis_data: {
                "comparison_results": [...],
                "ai_analysis_results": [...],
                "table_metadata": [...]
            }
            output_path: 输出Excel文件路径
        
        Returns:
            {
                "report_path": "生成的报告路径",
                "marked_cells_count": "标记的单元格数量",  
                "risk_summary": "风险汇总信息"
            }
        """
        
        # 步骤1: 创建工作簿并设置基础结构
        await self._initialize_workbook(output_path)
        
        # 步骤2: 创建总览工作表
        await self._create_overview_sheet(analysis_data, output_path)
        
        # 步骤3: 为每个表格创建详细分析工作表
        marked_cells_count = 0
        for table_result in analysis_data["comparison_results"]:
            table_marked_count = await self._create_table_analysis_sheet(
                table_result, 
                analysis_data["ai_analysis_results"].get(table_result["table_id"], {}),
                output_path
            )
            marked_cells_count += table_marked_count
        
        # 步骤4: 创建风险分布图表工作表
        await self._create_risk_charts_sheet(analysis_data, output_path)
        
        # 步骤5: 应用全局格式化
        await self._apply_global_formatting(output_path)
        
        # 生成报告摘要
        risk_summary = self._generate_risk_summary(analysis_data, marked_cells_count)
        
        return {
            "report_path": output_path,
            "marked_cells_count": marked_cells_count,
            "risk_summary": risk_summary,
            "generation_timestamp": datetime.now().isoformat()
        }
    
    async def _initialize_workbook(self, file_path):
        """初始化工作簿基础结构"""
        
        # 创建基础工作簿（根据MCP指南，使用正确的路径格式）
        normalized_path = file_path.replace('/', '\\')  # Windows路径格式
        
        # 创建总览工作表
        await self.mcp_functions["write_data_to_excel"]({
            "filepath": normalized_path,
            "sheet_name": "风险总览",
            "data": [
                ["表格名称", "L1风险数", "L2风险数", "L3风险数", "AI建议", "总体状态", "最后更新"]
            ]
        })
        
        # 设置工作表标题格式
        await self.mcp_functions["format_range"]({
            "filepath": normalized_path,
            "sheet_name": "风险总览",
            "range": "A1:G1",
            "format_options": {
                "font": {"bold": True, "color": "FFFFFF"},
                "fill": {"start_color": "4472C4"},
                "border": {
                    "style": "medium",
                    "color": "000000"
                }
            }
        })
    
    async def _create_table_analysis_sheet(self, table_result, ai_results, file_path):
        """为单个表格创建详细分析工作表"""
        
        sheet_name = f"{table_result['table_id'][:8]}_分析"
        normalized_path = file_path.replace('/', '\\')
        
        # 准备表格数据矩阵（30行×19列标准格式）
        analysis_matrix = self._build_table_analysis_matrix(table_result, ai_results)
        
        # 写入分析矩阵数据
        await self.mcp_functions["write_data_to_excel"]({
            "filepath": normalized_path,
            "sheet_name": sheet_name,
            "data": analysis_matrix
        })
        
        # 应用半填充对角线标记
        marked_cells_count = await self._apply_diagonal_marking(
            normalized_path, sheet_name, table_result["modification_details"]
        )
        
        # 添加图表和统计信息
        await self._add_table_statistics_chart(normalized_path, sheet_name, table_result)
        
        return marked_cells_count
    
    async def _apply_diagonal_marking(self, file_path, sheet_name, modifications):
        """应用半填充对角线标记"""
        
        marked_count = 0
        
        for mod in modifications:
            if mod["risk_level"] in ["L1", "L2"]:  # 只标记高风险修改
                
                # 计算单元格位置
                cell_address = f"{self._column_index_to_letter(mod['column_index'])}{mod['row_number']}"
                
                # 获取风险等级对应的颜色配置
                color_config = self.risk_color_scheme[mod["risk_level"]]
                
                # 根据CLAUDE.md指南，使用正确的格式选项
                format_options = {
                    "fill": {
                        "pattern_type": "lightUp",  # 关键：半填充对角线图案
                        "start_color": color_config["fill_color"],
                        "pattern_color": color_config["pattern_color"]
                    },
                    "border": {
                        "style": "thick" if mod["risk_level"] == "L1" else "medium",
                        "color": color_config["border_color"]
                    },
                    "font": {
                        "bold": True,
                        "color": color_config["font_color"]
                    }
                }\n                \n                # 应用格式化\n                await self.mcp_functions[\"format_range\"]({\n                    \"filepath\": file_path,\n                    \"sheet_name\": sheet_name,\n                    \"range\": cell_address,\n                    \"format_options\": format_options\n                })\n                \n                # 添加详细批注\n                comment_text = self._generate_modification_comment(mod)\n                await self.mcp_functions[\"add_comment\"]({\n                    \"filepath\": file_path,\n                    \"sheet_name\": sheet_name,\n                    \"cell\": cell_address,\n                    \"comment\": comment_text\n                })\n                \n                marked_count += 1\n        \n        return marked_count\n    \n    def _generate_modification_comment(self, modification):\n        \"\"\"生成修改说明批注\"\"\"\n        \n        comment_template = \"\"\"\n🚨 {risk_level}级别修改检测\n\n📝 修改详情:\n• 字段: {column_name}\n• 原值: {original_value}\n• 新值: {new_value}\n• 修改时间: {modification_time}\n• 修改人: {modifier}\n\n⚠️ 风险评估:\n• 风险等级: {risk_level}\n• 影响程度: {impact_level}\n• 置信度: {confidence:.1%}\n\n🤖 AI分析结果:\n{ai_recommendation}\n\n📋 建议操作:\n{suggested_actions}\n\n🔍 审批要求:\n{approval_requirements}\n        \"\"\"\n        \n        return comment_template.format(\n            risk_level=modification[\"risk_level\"],\n            column_name=modification[\"column_name\"],\n            original_value=modification.get(\"original_value\", \"未知\"),\n            new_value=modification.get(\"new_value\", \"未知\"), \n            modification_time=modification.get(\"modification_time\", \"未知\"),\n            modifier=modification.get(\"modifier\", \"未知\"),\n            impact_level=modification.get(\"business_impact\", \"中等\"),\n            confidence=modification.get(\"confidence\", 0.5),\n            ai_recommendation=modification.get(\"ai_analysis\", {}).get(\"reasoning\", \"暂无AI分析\"),\n            suggested_actions=self._format_suggested_actions(modification.get(\"ai_analysis\", {})),\n            approval_requirements=self._format_approval_requirements(modification)\n        ).strip()\n    \n    def _format_suggested_actions(self, ai_analysis):\n        \"\"\"格式化建议操作\"\"\"\n        if not ai_analysis:\n            return \"• 需要人工审核确认\"\n        \n        actions = []\n        if ai_analysis.get(\"recommendation\") == \"APPROVE\":\n            actions.append(\"• ✅ AI建议：批准此修改\")\n        elif ai_analysis.get(\"recommendation\") == \"REJECT\":\n            actions.append(\"• ❌ AI建议：拒绝此修改\")\n        else:\n            actions.append(\"• 🔍 AI建议：需要进一步审核\")\n        \n        if ai_analysis.get(\"suggested_action\"):\n            actions.append(f\"• 📋 具体建议：{ai_analysis['suggested_action']}\")\n        \n        return \"\\n\".join(actions) if actions else \"• 需要人工审核确认\"\n    \n    def _format_approval_requirements(self, modification):\n        \"\"\"格式化审批要求\"\"\"\n        risk_level = modification[\"risk_level\"]\n        \n        if risk_level == \"L1\":\n            return \"• 🔴 L1级别：需要部门经理和总监双重审批\\n• ⏱️ 紧急处理：24小时内必须审批完成\"\n        elif risk_level == \"L2\":\n            return \"• 🟠 L2级别：需要项目经理审批\\n• ⏱️ 标准处理：72小时内完成审批\"\n        else:\n            return \"• 🟢 L3级别：可自动批准或团队负责人确认\"\n```\n\n### 2.2 高级可视化功能\n\n```python\nclass AdvancedExcelVisualization:\n    \"\"\"高级Excel可视化功能\"\"\"\n    \n    def __init__(self, mcp_client):\n        self.mcp_client = mcp_client\n        \n    async def create_risk_heatmap_visualization(self, file_path, heatmap_data):\n        \"\"\"创建风险热力图可视化\"\"\"\n        \n        sheet_name = \"风险热力图\"\n        normalized_path = file_path.replace('/', '\\\\')\n        \n        # 创建30×19的热力图数据\n        heatmap_matrix = self._convert_to_excel_heatmap(heatmap_data)\n        \n        # 写入热力图数据\n        await self.mcp_client.mcp_functions[\"write_data_to_excel\"]({\n            \"filepath\": normalized_path,\n            \"sheet_name\": sheet_name,\n            \"data\": heatmap_matrix\n        })\n        \n        # 应用热力图颜色渐变\n        await self._apply_heatmap_conditional_formatting(normalized_path, sheet_name)\n        \n        # 添加图例和说明\n        await self._add_heatmap_legend(normalized_path, sheet_name)\n    \n    async def _apply_heatmap_conditional_formatting(self, file_path, sheet_name):\n        \"\"\"应用热力图条件格式\"\"\"\n        \n        # 为不同风险级别应用渐变色\n        risk_ranges = {\n            \"A1:S10\": {\"gradient\": \"red_scale\", \"description\": \"高风险区域\"},\n            \"A11:S20\": {\"gradient\": \"orange_scale\", \"description\": \"中风险区域\"},\n            \"A21:S30\": {\"gradient\": \"green_scale\", \"description\": \"低风险区域\"}\n        }\n        \n        for cell_range, config in risk_ranges.items():\n            # 应用条件格式（这里需要根据实际MCP API调整）\n            await self._apply_conditional_formatting(file_path, sheet_name, cell_range, config)\n    \n    async def create_interactive_dashboard(self, file_path, dashboard_data):\n        \"\"\"创建交互式仪表板\"\"\"\n        \n        sheet_name = \"交互式仪表板\"\n        normalized_path = file_path.replace('/', '\\\\')\n        \n        # 创建仪表板布局\n        dashboard_layout = [\n            [\"🎯 风险分析仪表板\", \"\", \"\", \"\", \"\", f\"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"],\n            [\"\", \"\", \"\", \"\", \"\", \"\"],\n            [\"📊 总体统计\", \"\", \"🔥 热点表格\", \"\", \"⚠️ 高风险修改\", \"\"],\n            [f\"总表格数: {dashboard_data.get('total_tables', 0)}\", \"\", \n             dashboard_data.get('hotspot_table', '未知'), \"\",\n             f\"{dashboard_data.get('high_risk_count', 0)}个\", \"\"],\n            [f\"总修改数: {dashboard_data.get('total_modifications', 0)}\", \"\", \"\", \"\", \"\", \"\"],\n            [f\"L1修改: {dashboard_data.get('l1_count', 0)}个\", \"\", \"\", \"\", \"\", \"\"],\n            [f\"L2修改: {dashboard_data.get('l2_count', 0)}个\", \"\", \"\", \"\", \"\", \"\"],\n            [f\"L3修改: {dashboard_data.get('l3_count', 0)}个\", \"\", \"\", \"\", \"\", \"\"],\n            [\"\", \"\", \"\", \"\", \"\", \"\"],\n            [\"🚀 快速导航\", \"\", \"\", \"\", \"\", \"\"],\n            [\"🔗 查看风险总览\", \"=HYPERLINK(\\\"风险总览!A1\\\", \\\"点击跳转\\\")\", \"\", \"\", \"\", \"\"],\n            [\"🔗 查看热力图\", \"=HYPERLINK(\\\"风险热力图!A1\\\", \\\"点击跳转\\\")\", \"\", \"\", \"\", \"\"],\n            [\"🔗 查看详细分析\", \"=HYPERLINK(\\\"详细分析!A1\\\", \\\"点击跳转\\\")\", \"\", \"\", \"\", \"\"]\n        ]\n        \n        # 写入仪表板数据\n        await self.mcp_client.mcp_functions[\"write_data_to_excel\"]({\n            \"filepath\": normalized_path,\n            \"sheet_name\": sheet_name,\n            \"data\": dashboard_layout\n        })\n        \n        # 应用仪表板格式化\n        await self._format_dashboard(normalized_path, sheet_name)\n    \n    async def _format_dashboard(self, file_path, sheet_name):\n        \"\"\"格式化仪表板样式\"\"\"\n        \n        # 格式化标题\n        await self.mcp_client.mcp_functions[\"format_range\"]({\n            \"filepath\": file_path,\n            \"sheet_name\": sheet_name,\n            \"range\": \"A1:F1\",\n            \"format_options\": {\n                \"font\": {\"bold\": True, \"size\": 16, \"color\": \"FFFFFF\"},\n                \"fill\": {\"start_color\": \"2563EB\"},\n                \"alignment\": {\"horizontal\": \"center\"}\n            }\n        })\n        \n        # 格式化统计区域\n        await self.mcp_client.mcp_functions[\"format_range\"]({\n            \"filepath\": file_path,\n            \"sheet_name\": sheet_name,\n            \"range\": \"A3:F8\",\n            \"format_options\": {\n                \"border\": {\"style\": \"thin\", \"color\": \"D1D5DB\"},\n                \"fill\": {\"start_color\": \"F9FAFB\"}\n            }\n        })\n        \n        # 格式化导航区域\n        await self.mcp_client.mcp_functions[\"format_range\"]({\n            \"filepath\": file_path,\n            \"sheet_name\": sheet_name,\n            \"range\": \"A10:F13\",\n            \"format_options\": {\n                \"font\": {\"color\": \"2563EB\"},\n                \"border\": {\"style\": \"thin\", \"color\": \"2563EB\"}\n            }\n        })\n```\n\n### 2.3 批量标记优化\n\n```python\nclass BatchMarkingOptimizer:\n    \"\"\"批量标记优化器\"\"\"\n    \n    def __init__(self, mcp_client):\n        self.mcp_client = mcp_client\n        self.batch_size = 50  # 批次大小\n        \n    async def optimize_batch_marking(self, file_path, all_modifications):\n        \"\"\"优化批量标记性能\"\"\"\n        \n        # 按工作表分组修改\n        modifications_by_sheet = self._group_modifications_by_sheet(all_modifications)\n        \n        total_marked = 0\n        \n        for sheet_name, sheet_modifications in modifications_by_sheet.items():\n            # 批量处理单个工作表的标记\n            marked_count = await self._batch_mark_sheet(\n                file_path, sheet_name, sheet_modifications\n            )\n            total_marked += marked_count\n            \n            # 添加处理进度日志\n            logger.info(f\"工作表 {sheet_name} 完成标记：{marked_count}个单元格\")\n        \n        return total_marked\n    \n    async def _batch_mark_sheet(self, file_path, sheet_name, modifications):\n        \"\"\"批量标记单个工作表\"\"\"\n        \n        marked_count = 0\n        \n        # 将修改分批处理\n        for i in range(0, len(modifications), self.batch_size):\n            batch = modifications[i:i + self.batch_size]\n            \n            # 并发处理批次内的标记\n            batch_tasks = [\n                self._mark_single_cell(file_path, sheet_name, mod)\n                for mod in batch\n            ]\n            \n            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)\n            \n            # 统计成功标记数量\n            successful_marks = sum(1 for result in batch_results if result is True)\n            marked_count += successful_marks\n            \n            # 批次间的短暂延迟，避免MCP API过载\n            await asyncio.sleep(0.1)\n        \n        return marked_count\n    \n    async def _mark_single_cell(self, file_path, sheet_name, modification):\n        \"\"\"标记单个单元格\"\"\"\n        try:\n            # 应用格式化\n            await self._apply_cell_formatting(file_path, sheet_name, modification)\n            \n            # 添加批注\n            await self._add_cell_comment(file_path, sheet_name, modification)\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"单元格标记失败 {sheet_name}:{modification.get('cell_address')}: {e}\")\n            return False\n```\n\n## 3. 专业格式化标准\n\n### 3.1 企业级格式化规范\n\n```python\nclass EnterpriseFormattingStandards:\n    \"\"\"企业级格式化标准\"\"\"\n    \n    def __init__(self):\n        self.corporate_theme = {\n            \"primary_color\": \"2563EB\",      # 企业蓝\n            \"secondary_color\": \"64748B\",    # 灰色\n            \"success_color\": \"059669\",      # 绿色\n            \"warning_color\": \"D97706\",      # 橙色\n            \"danger_color\": \"DC2626\",       # 红色\n            \"light_bg\": \"F8FAFC\",          # 浅灰背景\n            \"border_color\": \"E2E8F0\"       # 边框色\n        }\n        \n        self.standard_fonts = {\n            \"header\": {\"name\": \"Calibri\", \"size\": 14, \"bold\": True},\n            \"subheader\": {\"name\": \"Calibri\", \"size\": 12, \"bold\": True}, \n            \"body\": {\"name\": \"Calibri\", \"size\": 11, \"bold\": False},\n            \"caption\": {\"name\": \"Calibri\", \"size\": 9, \"bold\": False}\n        }\n    \n    def get_risk_level_format(self, risk_level, cell_type=\"data\"):\n        \"\"\"获取风险等级对应的格式配置\"\"\"\n        \n        base_formats = {\n            \"L1\": {\n                \"fill\": {\n                    \"pattern_type\": \"lightUp\",\n                    \"start_color\": self.corporate_theme[\"danger_color\"],\n                    \"pattern_color\": \"FFFFFF\"\n                },\n                \"border\": {\"style\": \"thick\", \"color\": self.corporate_theme[\"danger_color\"]},\n                \"font\": {\"bold\": True, \"color\": self.corporate_theme[\"danger_color\"]}\n            },\n            \"L2\": {\n                \"fill\": {\n                    \"pattern_type\": \"lightUp\", \n                    \"start_color\": self.corporate_theme[\"warning_color\"],\n                    \"pattern_color\": \"FFFFFF\"\n                },\n                \"border\": {\"style\": \"medium\", \"color\": self.corporate_theme[\"warning_color\"]},\n                \"font\": {\"bold\": True, \"color\": self.corporate_theme[\"warning_color\"]}\n            },\n            \"L3\": {\n                \"fill\": {\n                    \"pattern_type\": \"lightUp\",\n                    \"start_color\": self.corporate_theme[\"success_color\"],\n                    \"pattern_color\": \"FFFFFF\"\n                },\n                \"border\": {\"style\": \"thin\", \"color\": self.corporate_theme[\"success_color\"]},\n                \"font\": {\"color\": self.corporate_theme[\"success_color\"]}\n            }\n        }\n        \n        return base_formats.get(risk_level, base_formats[\"L3\"])\n    \n    def get_header_format(self, level=\"main\"):\n        \"\"\"获取标题格式\"\"\"\n        header_formats = {\n            \"main\": {\n                \"font\": {**self.standard_fonts[\"header\"], \"color\": \"FFFFFF\"},\n                \"fill\": {\"start_color\": self.corporate_theme[\"primary_color\"]},\n                \"alignment\": {\"horizontal\": \"center\", \"vertical\": \"center\"},\n                \"border\": {\"style\": \"medium\", \"color\": \"000000\"}\n            },\n            \"sub\": {\n                \"font\": {**self.standard_fonts[\"subheader\"], \"color\": self.corporate_theme[\"primary_color\"]},\n                \"fill\": {\"start_color\": self.corporate_theme[\"light_bg\"]},\n                \"border\": {\"style\": \"thin\", \"color\": self.corporate_theme[\"border_color\"]}\n            }\n        }\n        \n        return header_formats.get(level, header_formats[\"main\"])\n```\n\n## 4. 质量保证和测试\n\n### 4.1 可视化质量检查\n\n```python\nclass VisualizationQualityChecker:\n    \"\"\"可视化质量检查器\"\"\"\n    \n    def __init__(self, mcp_client):\n        self.mcp_client = mcp_client\n        \n    async def verify_visualization_quality(self, file_path):\n        \"\"\"验证可视化质量\"\"\"\n        \n        quality_report = {\n            \"file_accessibility\": await self._check_file_accessibility(file_path),\n            \"sheet_integrity\": await self._check_sheet_integrity(file_path),\n            \"formatting_consistency\": await self._check_formatting_consistency(file_path),\n            \"comment_completeness\": await self._check_comment_completeness(file_path),\n            \"chart_functionality\": await self._check_chart_functionality(file_path),\n            \"overall_quality_score\": 0.0\n        }\n        \n        # 计算总体质量分数\n        quality_score = sum([\n            quality_report[\"file_accessibility\"][\"score\"],\n            quality_report[\"sheet_integrity\"][\"score\"],\n            quality_report[\"formatting_consistency\"][\"score\"],\n            quality_report[\"comment_completeness\"][\"score\"],\n            quality_report[\"chart_functionality\"][\"score\"]\n        ]) / 5\n        \n        quality_report[\"overall_quality_score\"] = quality_score\n        \n        return quality_report\n    \n    async def _check_formatting_consistency(self, file_path):\n        \"\"\"检查格式化一致性\"\"\"\n        try:\n            # 读取文件元数据检查格式\n            metadata = await self.mcp_client.mcp_functions[\"get_workbook_metadata\"]({\n                \"filepath\": file_path.replace('/', '\\\\')\n            })\n            \n            # 检查工作表格式一致性\n            consistency_issues = []\n            \n            # 这里需要根据实际MCP API功能进行格式检查\n            # ...\n            \n            return {\n                \"score\": 0.9,  # 示例分数\n                \"issues\": consistency_issues,\n                \"recommendations\": [\"格式化总体一致，建议优化颜色对比度\"]\n            }\n            \n        except Exception as e:\n            return {\n                \"score\": 0.0,\n                \"issues\": [f\"格式检查失败: {e}\"],\n                \"recommendations\": [\"需要检查文件格式和MCP连接\"]\n            }\n```\n\n---\n\n**文档版本**: v1.0  \n**创建时间**: 2025-01-15  \n**基于指南**: CLAUDE.md Excel MCP使用指南  \n**维护人员**: 可视化开发团队