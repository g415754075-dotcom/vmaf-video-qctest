"""报告 API"""
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.video import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
    ShareLinkResponse,
)
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["报告"])


@router.post("", response_model=ReportResponse)
async def create_report(
    data: ReportCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    创建评估报告

    - **name**: 报告名称
    - **assessment_ids**: 评估任务 ID 列表
    - **include_sections**: 包含的章节 (summary, charts, statistics, problem_frames)
    """
    try:
        report = await report_service.create_report(
            session,
            data.name,
            data.assessment_ids,
            data.include_sections
        )
        return ReportResponse.model_validate(report)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ReportListResponse)
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取报告列表"""
    reports, total = await report_service.list_reports(session, skip, limit)

    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total
    )


@router.post("/batch-delete")
async def batch_delete_reports(
    report_ids: List[int] = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    """
    批量删除报告

    - **report_ids**: 要删除的报告 ID 列表
    """
    deleted_count = 0
    failed_ids = []

    for report_id in report_ids:
        try:
            success = await report_service.delete_report(session, report_id)
            if success:
                deleted_count += 1
            else:
                failed_ids.append(report_id)
        except Exception:
            failed_ids.append(report_id)

    return {
        "message": f"成功删除 {deleted_count} 个报告",
        "deleted_count": deleted_count,
        "failed_ids": failed_ids
    }


@router.delete("/clear-all")
async def clear_all_reports(
    session: AsyncSession = Depends(get_session)
):
    """
    清空所有报告

    删除所有报告及其关联文件。
    注意：这是一个危险操作，无法恢复。
    """
    from app.models.video import Report
    from sqlalchemy import select

    # 查询所有报告
    result = await session.execute(select(Report))
    reports = result.scalars().all()

    deleted_count = 0
    failed_count = 0

    for report in reports:
        try:
            success = await report_service.delete_report(session, report.id)
            if success:
                deleted_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    return {
        "message": f"成功清空 {deleted_count} 个报告",
        "deleted_count": deleted_count,
        "failed_count": failed_count
    }


@router.get("/shared/{token}", response_model=ReportResponse)
async def get_shared_report(
    token: str,
    session: AsyncSession = Depends(get_session)
):
    """通过分享链接获取报告"""
    report = await report_service.get_report_by_token(session, token)

    if not report:
        raise HTTPException(status_code=404, detail="链接无效或已过期")

    return ReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取报告详情"""
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download/pdf")
async def download_pdf(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """下载 PDF 报告"""
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    if not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF 文件不存在")

    pdf_path = Path(report.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF 文件不存在")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{report.name}.pdf"
    )


@router.get("/{report_id}/download/excel")
async def download_excel(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """下载 Excel 报告"""
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    if not report.excel_path:
        raise HTTPException(status_code=404, detail="Excel 文件不存在")

    excel_path = Path(report.excel_path)
    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Excel 文件不存在")

    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{report.name}.xlsx"
    )


@router.get("/{report_id}/download/json")
async def download_json(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """下载 JSON 报告"""
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    if not report.json_path:
        raise HTTPException(status_code=404, detail="JSON 文件不存在")

    json_path = Path(report.json_path)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="JSON 文件不存在")

    return FileResponse(
        json_path,
        media_type="application/json",
        filename=f"{report.name}.json"
    )


@router.post("/{report_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    report_id: int,
    expires_days: int = Query(7, ge=1, le=30),
    session: AsyncSession = Depends(get_session)
):
    """
    生成分享链接

    - **expires_days**: 有效期（天数，1-30）
    """
    try:
        token = await report_service.generate_share_link(session, report_id, expires_days)

        from app.models.video import Report
        report = await session.get(Report, report_id)

        return ShareLinkResponse(
            share_url=f"/api/reports/shared/{token}",
            expires_at=report.share_expires_at
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{report_id}/download/image/{image_type}")
async def download_image(
    report_id: int,
    image_type: str,
    session: AsyncSession = Depends(get_session)
):
    """
    下载报告图片

    - **image_type**: 图片类型
        - combined: 合并的三张散点图
        - bitrate_vs_size: 码率 vs 文件大小
        - bitrate_vs_vmaf: 码率 vs VMAF
        - vmaf_vs_size: VMAF vs 文件大小
    """
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 确定图片文件名
    image_files = {
        "combined": "scatter_chart.png",
        "bitrate_vs_size": "chart_bitrate_vs_size.png",
        "bitrate_vs_vmaf": "chart_bitrate_vs_vmaf.png",
        "vmaf_vs_size": "chart_vmaf_vs_size.png",
    }

    if image_type not in image_files:
        raise HTTPException(
            status_code=400,
            detail=f"无效的图片类型，可选值: {', '.join(image_files.keys())}"
        )

    # 获取报告目录
    report_dir = Path(report.pdf_path).parent if report.pdf_path else None

    if not report_dir:
        raise HTTPException(status_code=404, detail="报告文件目录不存在")

    image_path = report_dir / image_files[image_type]

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")

    # 生成友好的文件名
    filename_prefix = {
        "combined": "质量对比分析图",
        "bitrate_vs_size": "码率vs文件大小",
        "bitrate_vs_vmaf": "码率vsVMAF",
        "vmaf_vs_size": "VMAFvs文件大小",
    }

    return FileResponse(
        image_path,
        media_type="image/png",
        filename=f"{report.name}_{filename_prefix[image_type]}.png"
    )


@router.get("/{report_id}/images")
async def list_report_images(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    获取报告的可用图片列表

    返回报告中包含的所有图片信息
    """
    from app.models.video import Report

    report = await session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 获取报告目录
    report_dir = Path(report.pdf_path).parent if report.pdf_path else None

    if not report_dir:
        raise HTTPException(status_code=404, detail="报告文件目录不存在")

    # 检查各图片是否存在
    image_info = [
        {
            "type": "combined",
            "name": "质量对比分析图（合并）",
            "description": "三张散点图并排显示",
            "filename": "scatter_chart.png",
        },
        {
            "type": "bitrate_vs_size",
            "name": "码率 vs 文件大小",
            "description": "查看不同码率下文件大小的变化",
            "filename": "chart_bitrate_vs_size.png",
        },
        {
            "type": "bitrate_vs_vmaf",
            "name": "码率 vs VMAF",
            "description": "查看码率与画质之间的对应关系",
            "filename": "chart_bitrate_vs_vmaf.png",
        },
        {
            "type": "vmaf_vs_size",
            "name": "VMAF vs 文件大小",
            "description": "查看画质提升带来的体积成本",
            "filename": "chart_vmaf_vs_size.png",
        },
    ]

    available_images = []
    for img in image_info:
        image_path = report_dir / img["filename"]
        if image_path.exists():
            available_images.append({
                "type": img["type"],
                "name": img["name"],
                "description": img["description"],
                "download_url": f"/api/reports/{report_id}/download/image/{img['type']}"
            })

    return {
        "report_id": report_id,
        "report_name": report.name,
        "images": available_images
    }


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除报告"""
    success = await report_service.delete_report(session, report_id)

    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")

    return {"message": "删除成功"}
