"""报告 API"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
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
