# 任务清单

## 后端任务

- [ ] 在 `assessments.py` 添加 `POST /api/assessments/batch/{batch_id}/report` API 端点
- [ ] 在 `report_service.py` 添加 `create_batch_report()` 方法
- [ ] 添加 `_generate_scatter_chart()` 方法使用 matplotlib 生成散点图
- [ ] 添加 `_generate_conclusion_table()` 方法生成易懂结论表格
- [ ] 添加 `_calculate_efficiency()` 方法计算码率效率
- [ ] 优化 PDF 报告生成，包含执行摘要、散点图、结论表格
- [ ] 优化 Excel 报告生成，增加结论表格 Sheet

## 前端任务

- [ ] 安装 recharts 依赖（如未安装）
- [ ] 创建 `ScatterChart.tsx` 散点图组件
- [ ] 创建 `ConclusionTable.tsx` 结论表格组件（带星级评分和图标）
- [ ] 修改 `BatchAssessmentPage.tsx` 集成散点图和结论表格
- [ ] 修改报告生成逻辑，调用新的批量报告 API
- [ ] 添加报告生成成功后的提示和跳转

## 测试任务

- [ ] 测试批量评估报告生成 API
- [ ] 测试散点图数据正确性
- [ ] 测试结论表格的质量评级逻辑
- [ ] 测试报告的 PDF、Excel、JSON 导出
- [ ] 验证 PDF 中图表显示正常
