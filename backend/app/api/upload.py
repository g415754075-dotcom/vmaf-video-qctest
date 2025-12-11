"""视频上传 API"""
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.video import Video, VideoType
from app.schemas.video import (
    VideoResponse,
    VideoListResponse,
    ChunkUploadResponse,
    UploadCompleteResponse,
    UploadProgressResponse,
)
from app.services.upload_service import upload_service
from app.services.ffmpeg_service import ffmpeg_service

router = APIRouter(prefix="/upload", tags=["上传"])


@router.post("/chunk", response_model=ChunkUploadResponse)
async def upload_chunk(
    file: UploadFile = File(...),
    filename: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file_size: int = Form(...),
):
    """
    上传文件分片

    - **file**: 分片文件数据
    - **filename**: 原始文件名
    - **chunk_index**: 分片索引（从 0 开始）
    - **total_chunks**: 总分片数
    - **file_size**: 文件总大小
    """
    # 验证文件扩展名
    if not upload_service.validate_file_extension(filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，请上传 {', '.join(settings.allowed_extensions)} 格式"
        )

    # 验证文件大小
    if not upload_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大 {settings.max_file_size // (1024**3)}GB）"
        )

    # 读取分片数据
    chunk_data = await file.read()

    # 保存分片
    await upload_service.save_chunk(filename, file_size, chunk_index, chunk_data)

    return ChunkUploadResponse(
        chunk_index=chunk_index,
        uploaded=True,
        message=f"分片 {chunk_index + 1}/{total_chunks} 上传成功"
    )


@router.get("/progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    filename: str,
    file_size: int,
    total_chunks: int
):
    """
    获取上传进度

    - **filename**: 原始文件名
    - **file_size**: 文件总大小
    - **total_chunks**: 总分片数
    """
    progress = await upload_service.get_upload_progress(filename, file_size, total_chunks)
    return UploadProgressResponse(**progress)


@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    filename: str = Form(...),
    total_chunks: int = Form(...),
    file_size: int = Form(...),
    original_filename: str = Form(...),
    video_type: str = Form("distorted"),
    session: AsyncSession = Depends(get_session)
):
    """
    完成上传（合并分片）

    - **filename**: 原始文件名（用于查找分片）
    - **total_chunks**: 总分片数
    - **file_size**: 文件总大小
    - **original_filename**: 原始文件名（显示用）
    - **video_type**: 视频类型（reference/distorted）
    """
    # 验证所有分片已上传
    uploaded_chunks = await upload_service.get_uploaded_chunks(filename, file_size)
    if len(uploaded_chunks) != total_chunks:
        missing = set(range(total_chunks)) - set(uploaded_chunks)
        raise HTTPException(
            status_code=400,
            detail=f"分片不完整，缺少: {sorted(missing)}"
        )

    # 生成唯一文件名并合并
    unique_filename = upload_service.generate_unique_filename(original_filename)

    try:
        file_path = await upload_service.merge_chunks(
            filename, file_size, total_chunks, unique_filename
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 获取视频元信息
    try:
        video_info = await ffmpeg_service.get_video_info(str(file_path))
    except Exception as e:
        # 删除已上传的文件
        await upload_service.delete_file(str(file_path))
        raise HTTPException(status_code=400, detail=f"视频文件无效: {str(e)}")

    # 生成缩略图
    thumbnail_path = None
    try:
        thumb_filename = f"{Path(unique_filename).stem}_thumb.jpg"
        thumb_path = settings.upload_dir / thumb_filename
        await ffmpeg_service.generate_thumbnail(str(file_path), str(thumb_path))
        thumbnail_path = str(thumb_path)
    except Exception:
        pass  # 缩略图生成失败不影响上传

    # 保存到数据库
    video = Video(
        filename=unique_filename,
        original_filename=original_filename,
        file_path=str(file_path),
        file_size=file_size,
        width=video_info.width,
        height=video_info.height,
        duration=video_info.duration,
        frame_rate=video_info.frame_rate,
        frame_count=video_info.frame_count,
        codec=video_info.codec,
        bitrate=video_info.bitrate,
        pixel_format=video_info.pixel_format,
        thumbnail_path=thumbnail_path,
        video_type=VideoType(video_type)
    )

    session.add(video)
    await session.commit()
    await session.refresh(video)

    return UploadCompleteResponse(
        video=VideoResponse.model_validate(video),
        message="上传完成"
    )


@router.post("/simple", response_model=VideoResponse)
async def simple_upload(
    file: UploadFile = File(...),
    video_type: str = Form("distorted"),
    session: AsyncSession = Depends(get_session)
):
    """
    简单上传（适用于小文件）

    - **file**: 视频文件
    - **video_type**: 视频类型（reference/distorted）
    """
    # 验证文件扩展名
    if not upload_service.validate_file_extension(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，请上传 {', '.join(settings.allowed_extensions)} 格式"
        )

    # 读取文件
    content = await file.read()
    file_size = len(content)

    # 验证文件大小
    if not upload_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大 {settings.max_file_size // (1024**3)}GB）"
        )

    # 保存文件
    unique_filename = upload_service.generate_unique_filename(file.filename or "video.mp4")
    file_path = settings.upload_dir / unique_filename

    with open(file_path, "wb") as f:
        f.write(content)

    # 获取视频元信息
    try:
        video_info = await ffmpeg_service.get_video_info(str(file_path))
    except Exception as e:
        await upload_service.delete_file(str(file_path))
        raise HTTPException(status_code=400, detail=f"视频文件无效: {str(e)}")

    # 生成缩略图
    thumbnail_path = None
    try:
        thumb_filename = f"{Path(unique_filename).stem}_thumb.jpg"
        thumb_path = settings.upload_dir / thumb_filename
        await ffmpeg_service.generate_thumbnail(str(file_path), str(thumb_path))
        thumbnail_path = str(thumb_path)
    except Exception:
        pass

    # 保存到数据库
    video = Video(
        filename=unique_filename,
        original_filename=file.filename or "video.mp4",
        file_path=str(file_path),
        file_size=file_size,
        width=video_info.width,
        height=video_info.height,
        duration=video_info.duration,
        frame_rate=video_info.frame_rate,
        frame_count=video_info.frame_count,
        codec=video_info.codec,
        bitrate=video_info.bitrate,
        pixel_format=video_info.pixel_format,
        thumbnail_path=thumbnail_path,
        video_type=VideoType(video_type)
    )

    session.add(video)
    await session.commit()
    await session.refresh(video)

    return VideoResponse.model_validate(video)
