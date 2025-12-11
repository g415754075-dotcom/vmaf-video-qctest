"""报告生成服务"""
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import LineChart, Reference
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.core.config import settings
from app.models.video import Assessment, Report, TaskStatus
from app.services.assessment_service import assessment_service


class ReportService:
    """报告生成服务类"""

    def __init__(self):
        self.reports_dir = settings.reports_dir

    async def create_report(
        self,
        session: AsyncSession,
        name: str,
        assessment_ids: List[int],
        include_sections: List[str]
    ) -> Report:
        """创建报告记录"""
        # 验证评估任务存在且已完成
        for aid in assessment_ids:
            assessment = await session.get(Assessment, aid)
            if not assessment:
                raise ValueError(f"评估任务 {aid} 不存在")
            if assessment.status != TaskStatus.COMPLETED:
                raise ValueError(f"评估任务 {aid} 尚未完成")

        # 确定报告类型
        report_type = "single" if len(assessment_ids) == 1 else "comparison"

        # 创建报告记录
        report = Report(
            name=name,
            report_type=report_type,
            assessment_ids={"ids": assessment_ids, "sections": include_sections}
        )

        session.add(report)
        await session.commit()
        await session.refresh(report)

        # 生成报告文件
        await self._generate_report_files(session, report)

        return report

    async def _generate_report_files(
        self,
        session: AsyncSession,
        report: Report
    ) -> None:
        """生成报告文件（PDF、Excel、JSON）"""
        report_dir = self.reports_dir / f"report_{report.id}"
        report_dir.mkdir(parents=True, exist_ok=True)

        assessment_ids = report.assessment_ids.get("ids", [])
        sections = report.assessment_ids.get("sections", [])

        # 获取评估数据
        assessments_data = []
        for aid in assessment_ids:
            # 使用 select 语句预加载关联的视频对象
            query = (
                select(Assessment)
                .where(Assessment.id == aid)
                .options(
                    selectinload(Assessment.reference_video),
                    selectinload(Assessment.distorted_video)
                )
            )
            result = await session.execute(query)
            assessment = result.scalar_one_or_none()
            if assessment:
                frame_data = await assessment_service.get_frame_data(session, aid)
                stats = await assessment_service.get_statistics(session, aid)
                assessments_data.append({
                    "assessment": assessment,
                    "frame_data": frame_data,
                    "statistics": stats
                })

        # 生成 JSON
        json_path = report_dir / "report.json"
        await self._generate_json(json_path, assessments_data)
        report.json_path = str(json_path)

        # 生成 Excel
        excel_path = report_dir / "report.xlsx"
        await self._generate_excel(excel_path, assessments_data, sections)
        report.excel_path = str(excel_path)

        # 生成 PDF
        pdf_path = report_dir / "report.pdf"
        await self._generate_pdf(pdf_path, assessments_data, sections, report.name)
        report.pdf_path = str(pdf_path)

        await session.commit()

    async def _generate_json(
        self,
        output_path: Path,
        assessments_data: List[Dict]
    ) -> None:
        """生成 JSON 报告"""
        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "assessments": []
        }

        for data in assessments_data:
            assessment = data["assessment"]
            report_data["assessments"].append({
                "id": assessment.id,
                "reference_video": {
                    "filename": assessment.reference_video.original_filename,
                    "resolution": f"{assessment.reference_video.width}x{assessment.reference_video.height}",
                    "codec": assessment.reference_video.codec
                },
                "distorted_video": {
                    "filename": assessment.distorted_video.original_filename,
                    "resolution": f"{assessment.distorted_video.width}x{assessment.distorted_video.height}",
                    "codec": assessment.distorted_video.codec,
                    "bitrate": assessment.distorted_video.bitrate
                },
                "scores": {
                    "vmaf": assessment.vmaf_score,
                    "vmaf_min": assessment.vmaf_min,
                    "vmaf_max": assessment.vmaf_max,
                    "ssim": assessment.ssim_score,
                    "psnr": assessment.psnr_score
                },
                "statistics": data["statistics"],
                "frame_data": data["frame_data"]
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    async def _generate_excel(
        self,
        output_path: Path,
        assessments_data: List[Dict],
        sections: List[str]
    ) -> None:
        """生成 Excel 报告"""
        wb = Workbook()

        # 样式定义
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # 摘要 Sheet
        ws_summary = wb.active
        ws_summary.title = "摘要"

        summary_headers = ["视频名称", "分辨率", "编码器", "码率(Mbps)", "VMAF", "SSIM", "PSNR", "质量等级"]
        ws_summary.append(summary_headers)

        for col, header in enumerate(summary_headers, 1):
            cell = ws_summary.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        for data in assessments_data:
            assessment = data["assessment"]
            dist_video = assessment.distorted_video

            # 质量等级判断
            vmaf = assessment.vmaf_score or 0
            if vmaf > 90:
                quality_level = "优秀"
            elif vmaf > 80:
                quality_level = "良好"
            elif vmaf > 70:
                quality_level = "可接受"
            else:
                quality_level = "差"

            bitrate_mbps = (dist_video.bitrate or 0) / 1_000_000

            row = [
                dist_video.original_filename,
                f"{dist_video.width}x{dist_video.height}",
                dist_video.codec or "N/A",
                f"{bitrate_mbps:.2f}",
                f"{assessment.vmaf_score:.2f}" if assessment.vmaf_score else "N/A",
                f"{assessment.ssim_score:.4f}" if assessment.ssim_score else "N/A",
                f"{assessment.psnr_score:.2f}" if assessment.psnr_score else "N/A",
                quality_level
            ]
            ws_summary.append(row)

        # 调整列宽
        for col in ws_summary.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws_summary.column_dimensions[col[0].column_letter].width = max_length + 2

        # 逐帧数据 Sheet
        if "charts" in sections or "statistics" in sections:
            for i, data in enumerate(assessments_data):
                assessment = data["assessment"]
                frame_data = data["frame_data"] or []

                ws_frames = wb.create_sheet(title=f"逐帧数据_{i+1}")

                frame_headers = ["帧号", "VMAF", "SSIM", "PSNR"]
                ws_frames.append(frame_headers)

                for col, header in enumerate(frame_headers, 1):
                    cell = ws_frames.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill

                for frame in frame_data:
                    ws_frames.append([
                        frame.get("frame_num", 0),
                        frame.get("vmaf"),
                        frame.get("ssim"),
                        frame.get("psnr")
                    ])

                # 添加图表
                if len(frame_data) > 0:
                    chart = LineChart()
                    chart.title = "VMAF 质量曲线"
                    chart.x_axis.title = "帧号"
                    chart.y_axis.title = "VMAF"
                    chart.y_axis.scaling.min = 0
                    chart.y_axis.scaling.max = 100

                    data_ref = Reference(ws_frames, min_col=2, min_row=1, max_row=len(frame_data)+1)
                    categories = Reference(ws_frames, min_col=1, min_row=2, max_row=len(frame_data)+1)

                    chart.add_data(data_ref, titles_from_data=True)
                    chart.set_categories(categories)
                    chart.width = 20
                    chart.height = 10

                    ws_frames.add_chart(chart, "F2")

        # 统计数据 Sheet
        if "statistics" in sections:
            ws_stats = wb.create_sheet(title="统计分析")

            stats_headers = ["指标", "平均值", "最小值", "最大值", "中位数", "标准差", "P5", "P95"]
            ws_stats.append(stats_headers)

            for col, header in enumerate(stats_headers, 1):
                cell = ws_stats.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill

            for data in assessments_data:
                stats = data["statistics"]
                if stats:
                    for metric in ["vmaf", "ssim", "psnr"]:
                        metric_stats = stats.get(metric)
                        if metric_stats:
                            ws_stats.append([
                                metric.upper(),
                                metric_stats.get("mean"),
                                metric_stats.get("min"),
                                metric_stats.get("max"),
                                metric_stats.get("median"),
                                metric_stats.get("std"),
                                metric_stats.get("p5"),
                                metric_stats.get("p95")
                            ])

        wb.save(output_path)

    async def _generate_pdf(
        self,
        output_path: Path,
        assessments_data: List[Dict],
        sections: List[str],
        report_name: str
    ) -> None:
        """生成 PDF 报告"""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        story = []

        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # 居中
        )
        story.append(Paragraph(report_name, title_style))
        story.append(Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # 摘要表格
        if "summary" in sections:
            story.append(Paragraph("评估摘要", styles['Heading2']))
            story.append(Spacer(1, 10))

            table_data = [["视频", "VMAF", "SSIM", "PSNR", "质量等级"]]

            for data in assessments_data:
                assessment = data["assessment"]
                vmaf = assessment.vmaf_score or 0

                if vmaf > 90:
                    level = "优秀"
                elif vmaf > 80:
                    level = "良好"
                elif vmaf > 70:
                    level = "可接受"
                else:
                    level = "差"

                table_data.append([
                    assessment.distorted_video.original_filename[:30],
                    f"{assessment.vmaf_score:.2f}" if assessment.vmaf_score else "N/A",
                    f"{assessment.ssim_score:.4f}" if assessment.ssim_score else "N/A",
                    f"{assessment.psnr_score:.2f}" if assessment.psnr_score else "N/A",
                    level
                ])

            table = Table(table_data, colWidths=[150, 60, 60, 60, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            story.append(table)
            story.append(Spacer(1, 20))

        # 统计信息
        if "statistics" in sections:
            story.append(Paragraph("统计分析", styles['Heading2']))
            story.append(Spacer(1, 10))

            for data in assessments_data:
                stats = data["statistics"]
                assessment = data["assessment"]

                if stats:
                    story.append(Paragraph(
                        f"视频: {assessment.distorted_video.original_filename}",
                        styles['Heading3']
                    ))

                    for metric in ["vmaf", "ssim", "psnr"]:
                        metric_stats = stats.get(metric)
                        if metric_stats:
                            text = (
                                f"{metric.upper()}: "
                                f"平均={metric_stats.get('mean', 0):.2f}, "
                                f"最小={metric_stats.get('min', 0):.2f}, "
                                f"最大={metric_stats.get('max', 0):.2f}, "
                                f"标准差={metric_stats.get('std', 0):.2f}"
                            )
                            story.append(Paragraph(text, styles['Normal']))

                    story.append(Spacer(1, 10))

        doc.build(story)

    async def generate_share_link(
        self,
        session: AsyncSession,
        report_id: int,
        expires_days: int = 7
    ) -> str:
        """生成分享链接"""
        report = await session.get(Report, report_id)

        if not report:
            raise ValueError("报告不存在")

        # 生成唯一 token
        share_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        report.share_token = share_token
        report.share_expires_at = expires_at

        await session.commit()

        return share_token

    async def get_report_by_token(
        self,
        session: AsyncSession,
        token: str
    ) -> Optional[Report]:
        """通过分享 token 获取报告"""
        query = select(Report).where(Report.share_token == token)
        result = await session.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            return None

        # 检查是否过期
        if report.share_expires_at and report.share_expires_at < datetime.utcnow():
            return None

        return report

    async def list_reports(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Report], int]:
        """获取报告列表"""
        count_query = select(Report)
        result = await session.execute(count_query)
        total = len(result.scalars().all())

        query = (
            select(Report)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        reports = result.scalars().all()

        return list(reports), total

    async def delete_report(
        self,
        session: AsyncSession,
        report_id: int
    ) -> bool:
        """删除报告"""
        report = await session.get(Report, report_id)

        if not report:
            return False

        # 删除报告文件
        report_dir = self.reports_dir / f"report_{report_id}"
        if report_dir.exists():
            import shutil
            shutil.rmtree(report_dir)

        await session.delete(report)
        await session.commit()

        return True


# 创建服务实例
report_service = ReportService()
