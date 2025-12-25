"""质量评估 API"""
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models.video import TaskStatus, Assessment
from app.schemas.video import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    FrameDataResponse,
    FrameQuality,
    AssessmentStatistics,
    ComparisonRequest,
    ComparisonResponse,
    ComparisonItem,
    BatchAssessmentCreate,
    BatchAssessmentResponse,
    VideoResponse,
)
from app.services.assessment_service import assessment_service

router = APIRouter(prefix="/assessments", tags=["评估"])


@router.post("", response_model=AssessmentResponse)
async def create_assessment(
    data: AssessmentCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    创建评估任务

    - **reference_video_id**: 参考视频 ID
    - **distorted_video_id**: 待测视频 ID
    """
    try:
        assessment = await assessment_service.create_assessment(
            session,
            data.reference_video_id,
            data.distorted_video_id
        )

        # 在后台启动评估任务
        background_tasks.add_task(
            assessment_service.start_assessment,
            session,
            assessment.id
        )

        return AssessmentResponse.model_validate(assessment)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取评估任务列表"""
    assessments, total = await assessment_service.list_assessments(session, skip, limit)

    return AssessmentListResponse(
        assessments=[
            AssessmentDetailResponse(
                **AssessmentResponse.model_validate(a).model_dump(),
                reference_video=a.reference_video,
                distorted_video=a.distorted_video
            )
            for a in assessments
        ],
        total=total
    )


# 注意：以下静态路由必须在 /{assessment_id} 动态路由之前定义

@router.post("/compare", response_model=ComparisonResponse)
async def compare_assessments(
    data: ComparisonRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    对比多个评估结果

    - **assessment_ids**: 评估任务 ID 列表（2-5 个）
    """
    items = []
    reference_video = None

    for aid in data.assessment_ids:
        assessment = await assessment_service.get_assessment(session, aid)

        if not assessment:
            raise HTTPException(status_code=404, detail=f"评估任务 {aid} 不存在")

        if assessment.status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=f"评估任务 {aid} 尚未完成")

        # 使用第一个评估的参考视频
        if reference_video is None:
            reference_video = assessment.reference_video

        dist_video = assessment.distorted_video
        items.append(ComparisonItem(
            assessment_id=aid,
            video_name=dist_video.original_filename,
            vmaf_score=assessment.vmaf_score,
            ssim_score=assessment.ssim_score,
            psnr_score=assessment.psnr_score,
            bitrate=dist_video.bitrate,
            resolution=f"{dist_video.width}x{dist_video.height}",
            codec=dist_video.codec
        ))

    return ComparisonResponse(
        items=items,
        reference_video=reference_video
    )


# ============ 批量评估 API ============

@router.post("/batch", response_model=BatchAssessmentResponse)
async def create_batch_assessment(
    data: BatchAssessmentCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    创建批量评估任务

    - **reference_video_id**: 参考视频 ID
    - **distorted_video_ids**: 待测视频 ID 列表（1-10 个）

    批量评估中的任务将按顺序依次执行，完成一个后自动启动下一个。
    """
    try:
        # 创建批量评估任务
        batch_id, assessments = await assessment_service.create_batch_assessment(
            session,
            data.reference_video_id,
            data.distorted_video_ids
        )

        # 在后台启动第一个任务
        background_tasks.add_task(
            assessment_service.start_batch_assessment,
            session,
            batch_id
        )

        # 获取批量评估状态
        batch_status = await assessment_service.get_batch_status(session, batch_id)

        # 构建响应
        return BatchAssessmentResponse(
            batch_id=batch_id,
            reference_video=VideoResponse.model_validate(batch_status["reference_video"]),
            assessments=[
                AssessmentDetailResponse(
                    **AssessmentResponse.model_validate(a).model_dump(),
                    reference_video=a.reference_video,
                    distorted_video=a.distorted_video
                )
                for a in batch_status["assessments"]
            ],
            total_count=batch_status["total_count"],
            completed_count=batch_status["completed_count"],
            failed_count=batch_status["failed_count"],
            progress=batch_status["progress"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/batch/{batch_id}", response_model=BatchAssessmentResponse)
async def get_batch_status(
    batch_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    获取批量评估状态

    - **batch_id**: 批量评估 ID

    返回批量评估的整体进度和各子任务状态。
    """
    batch_status = await assessment_service.get_batch_status(session, batch_id)

    if batch_status is None:
        raise HTTPException(status_code=404, detail="批量评估不存在")

    return BatchAssessmentResponse(
        batch_id=batch_id,
        reference_video=VideoResponse.model_validate(batch_status["reference_video"]),
        assessments=[
            AssessmentDetailResponse(
                **AssessmentResponse.model_validate(a).model_dump(),
                reference_video=a.reference_video,
                distorted_video=a.distorted_video
            )
            for a in batch_status["assessments"]
        ],
        total_count=batch_status["total_count"],
        completed_count=batch_status["completed_count"],
        failed_count=batch_status["failed_count"],
        progress=batch_status["progress"]
    )


@router.post("/batch/{batch_id}/report")
async def create_batch_report(
    batch_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    为批量评估生成合并报告

    - **batch_id**: 批量评估 ID

    将批量评估中所有已完成的任务合并为一个报告，包含：
    - 执行摘要和结论表格
    - 散点对比图（码率 vs 质量）
    - 详细评估数据
    """
    from app.services.report_service import report_service

    batch_status = await assessment_service.get_batch_status(session, batch_id)

    if batch_status is None:
        raise HTTPException(status_code=404, detail="批量评估不存在")

    # 获取已完成的评估任务 ID
    completed_ids = [
        a.id for a in batch_status["assessments"]
        if a.status == TaskStatus.COMPLETED
    ]

    if not completed_ids:
        raise HTTPException(status_code=400, detail="没有已完成的评估任务")

    try:
        report = await report_service.create_batch_report(
            session,
            batch_id,
            completed_ids,
            batch_status["reference_video"]
        )

        return {
            "report_id": report.id,
            "name": report.name,
            "message": f"成功生成包含 {len(completed_ids)} 个评估的合并报告"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.post("/batch-delete")
async def batch_delete_assessments(
    assessment_ids: List[int] = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    """
    批量删除评估任务

    - **assessment_ids**: 要删除的评估任务 ID 列表
    """
    deleted_count = 0
    failed_ids = []

    for assessment_id in assessment_ids:
        assessment = await session.get(Assessment, assessment_id)

        if not assessment:
            failed_ids.append(assessment_id)
            continue

        # 跳过运行中的任务
        if assessment.status == TaskStatus.RUNNING:
            failed_ids.append(assessment_id)
            continue

        try:
            await session.delete(assessment)
            deleted_count += 1
        except Exception:
            failed_ids.append(assessment_id)

    await session.commit()

    return {
        "message": f"成功删除 {deleted_count} 个评估任务",
        "deleted_count": deleted_count,
        "failed_ids": failed_ids
    }


@router.delete("/clear-all")
async def clear_all_assessments(
    session: AsyncSession = Depends(get_session)
):
    """
    清空所有评估任务

    删除所有评估任务记录（运行中的任务除外）。
    注意：这是一个危险操作，无法恢复。
    """
    # 查询所有非运行中的任务
    result = await session.execute(
        select(Assessment).where(Assessment.status != TaskStatus.RUNNING)
    )
    assessments = result.scalars().all()

    deleted_count = 0
    skipped_count = 0

    for assessment in assessments:
        try:
            await session.delete(assessment)
            deleted_count += 1
        except Exception:
            skipped_count += 1

    await session.commit()

    # 检查是否还有运行中的任务
    running_result = await session.execute(
        select(Assessment).where(Assessment.status == TaskStatus.RUNNING)
    )
    running_count = len(running_result.scalars().all())

    return {
        "message": f"成功清空 {deleted_count} 个评估任务",
        "deleted_count": deleted_count,
        "skipped_count": skipped_count,
        "running_count": running_count
    }


# 以下是带 {assessment_id} 参数的动态路由

@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取评估任务详情"""
    assessment = await assessment_service.get_assessment(session, assessment_id)

    if not assessment:
        raise HTTPException(status_code=404, detail="评估任务不存在")

    return AssessmentDetailResponse(
        **AssessmentResponse.model_validate(assessment).model_dump(),
        reference_video=assessment.reference_video,
        distorted_video=assessment.distorted_video
    )


@router.post("/{assessment_id}/start")
async def start_assessment(
    assessment_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """手动启动评估任务"""
    try:
        background_tasks.add_task(
            assessment_service.start_assessment,
            session,
            assessment_id
        )
        return {"message": "评估任务已启动"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{assessment_id}/cancel")
async def cancel_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """取消评估任务"""
    try:
        await assessment_service.cancel_assessment(session, assessment_id)
        return {"message": "评估任务已取消"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{assessment_id}/frames", response_model=FrameDataResponse)
async def get_frame_data(
    assessment_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    session: AsyncSession = Depends(get_session)
):
    """
    获取逐帧质量数据

    - **skip**: 跳过帧数
    - **limit**: 返回帧数
    """
    frame_data = await assessment_service.get_frame_data(session, assessment_id)

    if frame_data is None:
        raise HTTPException(status_code=404, detail="逐帧数据不存在")

    # 分页
    total = len(frame_data)
    frames = frame_data[skip:skip + limit]

    return FrameDataResponse(
        assessment_id=assessment_id,
        frames=[
            FrameQuality(
                frame_num=f.get("frame_num", 0),
                timestamp=f.get("frame_num", 0) / 30.0,  # 假设 30fps
                vmaf=f.get("vmaf"),
                ssim=f.get("ssim"),
                psnr=f.get("psnr")
            )
            for f in frames
        ],
        total_frames=total
    )


@router.get("/{assessment_id}/statistics", response_model=AssessmentStatistics)
async def get_statistics(
    assessment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取质量统计数据"""
    stats = await assessment_service.get_statistics(session, assessment_id)

    if stats is None:
        raise HTTPException(status_code=404, detail="统计数据不存在")

    return AssessmentStatistics(**stats)


@router.get("/{assessment_id}/problem-frames")
async def get_problem_frames(
    assessment_id: int,
    threshold: float = Query(70, ge=0, le=100),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    获取质量较差的帧

    - **threshold**: VMAF 阈值，低于此值的帧被认为是问题帧
    - **limit**: 返回数量
    """
    frames = await assessment_service.get_problem_frames(
        session, assessment_id, threshold, limit
    )

    return {
        "assessment_id": assessment_id,
        "threshold": threshold,
        "frames": frames
    }
