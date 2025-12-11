"""质量评估 API"""
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.video import TaskStatus
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
