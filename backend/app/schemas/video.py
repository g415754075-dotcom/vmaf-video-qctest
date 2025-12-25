"""视频相关 Pydantic 模式"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.video import VideoType, TaskStatus


# ============ 视频相关 ============

class VideoMetadata(BaseModel):
    """视频元信息"""
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    frame_rate: Optional[float] = None
    frame_count: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    pixel_format: Optional[str] = None


class VideoBase(BaseModel):
    """视频基础信息"""
    filename: str
    original_filename: str
    file_size: int
    video_type: VideoType = VideoType.DISTORTED


class VideoCreate(VideoBase):
    """创建视频"""
    file_path: str


class VideoResponse(VideoBase):
    """视频响应"""
    id: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    frame_rate: Optional[float] = None
    frame_count: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """视频列表响应"""
    videos: List[VideoResponse]
    total: int


# ============ 上传相关 ============

class ChunkUploadRequest(BaseModel):
    """分片上传请求"""
    filename: str
    chunk_index: int
    total_chunks: int
    file_size: int


class ChunkUploadResponse(BaseModel):
    """分片上传响应"""
    chunk_index: int
    uploaded: bool
    message: str


class UploadCompleteRequest(BaseModel):
    """上传完成请求"""
    filename: str
    total_chunks: int
    file_size: int
    original_filename: str


class UploadCompleteResponse(BaseModel):
    """上传完成响应"""
    video: VideoResponse
    message: str


class UploadProgressResponse(BaseModel):
    """上传进度响应"""
    filename: str
    uploaded_chunks: List[int]
    total_chunks: int
    progress: float


# ============ 评估任务相关 ============

class AssessmentCreate(BaseModel):
    """创建评估任务"""
    reference_video_id: int
    distorted_video_id: int


class AssessmentResponse(BaseModel):
    """评估任务响应"""
    id: int
    batch_id: Optional[str] = None  # 批量评估标识
    reference_video_id: int
    distorted_video_id: int
    status: TaskStatus
    progress: float
    current_frame: int
    total_frames: int
    error_message: Optional[str] = None
    vmaf_score: Optional[float] = None
    vmaf_min: Optional[float] = None
    vmaf_max: Optional[float] = None
    ssim_score: Optional[float] = None
    psnr_score: Optional[float] = None
    ms_ssim_score: Optional[float] = None
    vmaf_model: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """评估任务详情响应（包含关联视频信息）"""
    reference_video: VideoResponse
    distorted_video: VideoResponse


class AssessmentListResponse(BaseModel):
    """评估任务列表响应"""
    assessments: List[AssessmentDetailResponse]
    total: int


# ============ 逐帧数据 ============

class FrameQuality(BaseModel):
    """单帧质量数据"""
    frame_num: int
    timestamp: float
    vmaf: Optional[float] = None
    ssim: Optional[float] = None
    psnr: Optional[float] = None
    ms_ssim: Optional[float] = None


class FrameDataResponse(BaseModel):
    """逐帧数据响应"""
    assessment_id: int
    frames: List[FrameQuality]
    total_frames: int


# ============ 统计数据 ============

class QualityStatistics(BaseModel):
    """质量统计数据"""
    mean: float
    min: float
    max: float
    median: float
    std: float
    p5: float  # 5% 百分位
    p95: float  # 95% 百分位


class AssessmentStatistics(BaseModel):
    """评估统计摘要"""
    assessment_id: int
    vmaf: Optional[QualityStatistics] = None
    ssim: Optional[QualityStatistics] = None
    psnr: Optional[QualityStatistics] = None


# ============ 对比分析 ============

class ComparisonRequest(BaseModel):
    """对比分析请求"""
    assessment_ids: List[int] = Field(..., min_length=2, max_length=5)


class ComparisonItem(BaseModel):
    """对比项"""
    assessment_id: int
    video_name: str
    vmaf_score: Optional[float] = None
    ssim_score: Optional[float] = None
    psnr_score: Optional[float] = None
    bitrate: Optional[int] = None
    resolution: str
    codec: Optional[str] = None


class ComparisonResponse(BaseModel):
    """对比分析响应"""
    items: List[ComparisonItem]
    reference_video: VideoResponse


# ============ 报告相关 ============

class ReportCreate(BaseModel):
    """创建报告"""
    name: str
    assessment_ids: List[int]
    include_sections: List[str] = Field(
        default=["summary", "charts", "statistics", "problem_frames"]
    )


class ReportResponse(BaseModel):
    """报告响应"""
    id: int
    name: str
    report_type: str
    pdf_path: Optional[str] = None
    excel_path: Optional[str] = None
    json_path: Optional[str] = None
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[ReportResponse]
    total: int


class ShareLinkResponse(BaseModel):
    """分享链接响应"""
    share_url: str
    expires_at: datetime


# ============ 批量评估相关 ============

class BatchAssessmentCreate(BaseModel):
    """创建批量评估任务"""
    reference_video_id: int
    distorted_video_ids: List[int] = Field(..., min_length=1, max_length=10)


class BatchAssessmentResponse(BaseModel):
    """批量评估响应"""
    batch_id: str
    reference_video: VideoResponse
    assessments: List[AssessmentDetailResponse]
    total_count: int
    completed_count: int
    failed_count: int
    progress: float  # 整体进度 0-100

    class Config:
        from_attributes = True


class BatchAssessmentListResponse(BaseModel):
    """批量评估列表响应"""
    batches: List[BatchAssessmentResponse]
    total: int
