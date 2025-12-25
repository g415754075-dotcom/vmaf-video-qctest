"""视频管理 API"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.video import Video, VideoType
from app.schemas.video import VideoResponse, VideoListResponse
from app.services.upload_service import upload_service

router = APIRouter(prefix="/videos", tags=["视频"])


@router.get("", response_model=VideoListResponse)
async def list_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    video_type: Optional[str] = Query(None, description="视频类型: reference/distorted"),
    session: AsyncSession = Depends(get_session)
):
    """
    获取视频列表

    - **skip**: 跳过数量
    - **limit**: 返回数量
    - **video_type**: 筛选视频类型
    """
    query = select(Video)

    if video_type:
        query = query.where(Video.video_type == VideoType(video_type))

    # 查询总数
    count_result = await session.execute(query)
    total = len(count_result.scalars().all())

    # 查询列表
    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    videos = result.scalars().all()

    return VideoListResponse(
        videos=[VideoResponse.model_validate(v) for v in videos],
        total=total
    )


# 注意：以下静态路由必须在 /{video_id} 动态路由之前定义

@router.post("/batch-delete")
async def batch_delete_videos(
    video_ids: List[int] = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    """
    批量删除视频

    - **video_ids**: 要删除的视频 ID 列表
    """
    deleted_count = 0
    failed_ids = []

    for video_id in video_ids:
        video = await session.get(Video, video_id)

        if not video:
            failed_ids.append(video_id)
            continue

        try:
            # 删除文件
            await upload_service.delete_file(video.file_path)
            if video.thumbnail_path:
                await upload_service.delete_file(video.thumbnail_path)

            # 删除数据库记录
            await session.delete(video)
            deleted_count += 1
        except Exception:
            failed_ids.append(video_id)

    await session.commit()

    return {
        "message": f"成功删除 {deleted_count} 个视频",
        "deleted_count": deleted_count,
        "failed_ids": failed_ids
    }


@router.delete("/clear-all")
async def clear_all_videos(
    session: AsyncSession = Depends(get_session)
):
    """
    清空所有视频

    删除所有上传的视频文件和数据库记录。
    注意：这是一个危险操作，无法恢复。
    """
    # 查询所有视频
    result = await session.execute(select(Video))
    videos = result.scalars().all()

    deleted_count = 0
    failed_count = 0

    for video in videos:
        try:
            # 删除文件
            await upload_service.delete_file(video.file_path)
            if video.thumbnail_path:
                await upload_service.delete_file(video.thumbnail_path)

            # 删除数据库记录
            await session.delete(video)
            deleted_count += 1
        except Exception:
            failed_count += 1

    await session.commit()

    return {
        "message": f"成功清空 {deleted_count} 个视频",
        "deleted_count": deleted_count,
        "failed_count": failed_count
    }


# 以下是带 {video_id} 参数的动态路由

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取视频详情"""
    video = await session.get(Video, video_id)

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    return VideoResponse.model_validate(video)


@router.patch("/{video_id}/type", response_model=VideoResponse)
async def update_video_type(
    video_id: int,
    video_type: str,
    session: AsyncSession = Depends(get_session)
):
    """
    更新视频类型

    - **video_id**: 视频 ID
    - **video_type**: 新类型 (reference/distorted)
    """
    video = await session.get(Video, video_id)

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    try:
        video.video_type = VideoType(video_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的视频类型")

    await session.commit()
    await session.refresh(video)

    return VideoResponse.model_validate(video)


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除视频"""
    video = await session.get(Video, video_id)

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 删除文件
    await upload_service.delete_file(video.file_path)
    if video.thumbnail_path:
        await upload_service.delete_file(video.thumbnail_path)

    # 删除数据库记录
    await session.delete(video)
    await session.commit()

    return {"message": "删除成功"}
