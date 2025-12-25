"""视频相关数据模型"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VideoType(enum.Enum):
    """视频类型"""
    REFERENCE = "reference"  # 参考视频
    DISTORTED = "distorted"  # 待测视频


class TaskStatus(enum.Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class Video(Base):
    """视频文件模型"""
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # 字节

    # 视频元信息
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 秒
    frame_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bps
    pixel_format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 缩略图
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 视频类型
    video_type: Mapped[VideoType] = mapped_column(
        Enum(VideoType), default=VideoType.DISTORTED
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关联的评估任务
    assessments_as_reference: Mapped[list["Assessment"]] = relationship(
        "Assessment", foreign_keys="Assessment.reference_video_id", back_populates="reference_video"
    )
    assessments_as_distorted: Mapped[list["Assessment"]] = relationship(
        "Assessment", foreign_keys="Assessment.distorted_video_id", back_populates="distorted_video"
    )


class Assessment(Base):
    """质量评估任务模型"""
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 批量评估标识（可选，用于关联同一批次的评估任务）
    batch_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    # 关联视频
    reference_video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id"), nullable=False
    )
    distorted_video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id"), nullable=False
    )

    # 任务状态
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    current_frame: Mapped[int] = mapped_column(Integer, default=0)
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 评估结果摘要
    vmaf_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vmaf_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vmaf_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ssim_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    psnr_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ms_ssim_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 逐帧数据文件路径
    frame_data_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 使用的 VMAF 模型
    vmaf_model: Mapped[str] = mapped_column(String(100), default="vmaf_v0.6.1")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    reference_video: Mapped["Video"] = relationship(
        "Video", foreign_keys=[reference_video_id], back_populates="assessments_as_reference"
    )
    distorted_video: Mapped["Video"] = relationship(
        "Video", foreign_keys=[distorted_video_id], back_populates="assessments_as_distorted"
    )


class Report(Base):
    """评估报告模型"""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # single / comparison

    # 包含的评估任务 ID 列表
    assessment_ids: Mapped[dict] = mapped_column(JSON, nullable=False)

    # 报告文件路径
    pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    excel_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    json_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 分享链接
    share_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    share_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
