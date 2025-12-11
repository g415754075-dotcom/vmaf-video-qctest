"""Pydantic 模式单元测试"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.video import (
    VideoMetadata,
    VideoBase,
    VideoCreate,
    VideoResponse,
    ChunkUploadRequest,
    UploadCompleteRequest,
    AssessmentCreate,
    AssessmentResponse,
    FrameQuality,
    QualityStatistics,
    ComparisonRequest,
    ReportCreate,
)
from app.models.video import VideoType, TaskStatus


class TestVideoMetadata:
    """VideoMetadata 模式测试"""

    def test_video_metadata_全部可选(self):
        """测试所有字段都是可选的"""
        metadata = VideoMetadata()
        assert metadata.width is None
        assert metadata.height is None
        assert metadata.duration is None

    def test_video_metadata_完整数据(self):
        """测试完整数据创建"""
        metadata = VideoMetadata(
            width=1920,
            height=1080,
            duration=120.5,
            frame_rate=30.0,
            frame_count=3615,
            codec="h264",
            bitrate=5000000,
            pixel_format="yuv420p"
        )
        assert metadata.width == 1920
        assert metadata.height == 1080


class TestVideoBase:
    """VideoBase 模式测试"""

    def test_video_base_必填字段(self):
        """测试必填字段验证"""
        with pytest.raises(ValidationError):
            VideoBase()

    def test_video_base_有效数据(self):
        """测试有效数据创建"""
        video = VideoBase(
            filename="abc123.mp4",
            original_filename="test.mp4",
            file_size=1024000,
            video_type=VideoType.REFERENCE
        )
        assert video.filename == "abc123.mp4"
        assert video.original_filename == "test.mp4"
        assert video.file_size == 1024000
        assert video.video_type == VideoType.REFERENCE

    def test_video_base_默认类型(self):
        """测试默认视频类型为待测视频"""
        video = VideoBase(
            filename="abc123.mp4",
            original_filename="test.mp4",
            file_size=1024000
        )
        assert video.video_type == VideoType.DISTORTED


class TestVideoCreate:
    """VideoCreate 模式测试"""

    def test_video_create_包含文件路径(self):
        """测试创建时需要文件路径"""
        video = VideoCreate(
            filename="abc123.mp4",
            original_filename="test.mp4",
            file_size=1024000,
            file_path="/uploads/abc123.mp4"
        )
        assert video.file_path == "/uploads/abc123.mp4"


class TestChunkUploadRequest:
    """ChunkUploadRequest 模式测试"""

    def test_chunk_upload_有效请求(self):
        """测试有效的分片上传请求"""
        request = ChunkUploadRequest(
            filename="test.mp4",
            chunk_index=0,
            total_chunks=10,
            file_size=10485760
        )
        assert request.filename == "test.mp4"
        assert request.chunk_index == 0
        assert request.total_chunks == 10
        assert request.file_size == 10485760

    def test_chunk_upload_缺少字段(self):
        """测试缺少字段时验证失败"""
        with pytest.raises(ValidationError):
            ChunkUploadRequest(filename="test.mp4")


class TestUploadCompleteRequest:
    """UploadCompleteRequest 模式测试"""

    def test_upload_complete_有效请求(self):
        """测试有效的上传完成请求"""
        request = UploadCompleteRequest(
            filename="abc123",
            total_chunks=10,
            file_size=10485760,
            original_filename="test.mp4"
        )
        assert request.filename == "abc123"
        assert request.original_filename == "test.mp4"


class TestAssessmentCreate:
    """AssessmentCreate 模式测试"""

    def test_assessment_create_有效请求(self):
        """测试有效的评估创建请求"""
        assessment = AssessmentCreate(
            reference_video_id=1,
            distorted_video_id=2
        )
        assert assessment.reference_video_id == 1
        assert assessment.distorted_video_id == 2

    def test_assessment_create_缺少字段(self):
        """测试缺少字段时验证失败"""
        with pytest.raises(ValidationError):
            AssessmentCreate(reference_video_id=1)


class TestAssessmentResponse:
    """AssessmentResponse 模式测试"""

    def test_assessment_response_完整数据(self):
        """测试完整评估响应"""
        now = datetime.utcnow()
        response = AssessmentResponse(
            id=1,
            reference_video_id=1,
            distorted_video_id=2,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            current_frame=300,
            total_frames=300,
            vmaf_score=90.5,
            vmaf_min=85.0,
            vmaf_max=95.0,
            ssim_score=0.98,
            psnr_score=40.5,
            vmaf_model="vmaf_v0.6.1",
            created_at=now
        )
        assert response.id == 1
        assert response.status == TaskStatus.COMPLETED
        assert response.vmaf_score == 90.5


class TestFrameQuality:
    """FrameQuality 模式测试"""

    def test_frame_quality_有效数据(self):
        """测试有效的帧质量数据"""
        frame = FrameQuality(
            frame_num=0,
            timestamp=0.0,
            vmaf=90.5,
            ssim=0.98,
            psnr=40.5
        )
        assert frame.frame_num == 0
        assert frame.vmaf == 90.5

    def test_frame_quality_可选字段(self):
        """测试可选字段可以为 None"""
        frame = FrameQuality(
            frame_num=0,
            timestamp=0.0
        )
        assert frame.vmaf is None
        assert frame.ssim is None
        assert frame.psnr is None


class TestQualityStatistics:
    """QualityStatistics 模式测试"""

    def test_quality_statistics_有效数据(self):
        """测试有效的质量统计数据"""
        stats = QualityStatistics(
            mean=90.0,
            min=85.0,
            max=95.0,
            median=90.5,
            std=2.5,
            p5=86.0,
            p95=94.0
        )
        assert stats.mean == 90.0
        assert stats.min == 85.0
        assert stats.max == 95.0
        assert stats.p5 == 86.0
        assert stats.p95 == 94.0


class TestComparisonRequest:
    """ComparisonRequest 模式测试"""

    def test_comparison_request_有效请求(self):
        """测试有效的对比请求"""
        request = ComparisonRequest(assessment_ids=[1, 2, 3])
        assert len(request.assessment_ids) == 3

    def test_comparison_request_最少两个(self):
        """测试至少需要两个评估任务"""
        with pytest.raises(ValidationError):
            ComparisonRequest(assessment_ids=[1])

    def test_comparison_request_最多五个(self):
        """测试最多五个评估任务"""
        with pytest.raises(ValidationError):
            ComparisonRequest(assessment_ids=[1, 2, 3, 4, 5, 6])

    def test_comparison_request_边界值(self):
        """测试边界值"""
        # 两个应该成功
        request2 = ComparisonRequest(assessment_ids=[1, 2])
        assert len(request2.assessment_ids) == 2

        # 五个应该成功
        request5 = ComparisonRequest(assessment_ids=[1, 2, 3, 4, 5])
        assert len(request5.assessment_ids) == 5


class TestReportCreate:
    """ReportCreate 模式测试"""

    def test_report_create_有效请求(self):
        """测试有效的报告创建请求"""
        report = ReportCreate(
            name="测试报告",
            assessment_ids=[1, 2]
        )
        assert report.name == "测试报告"
        assert report.assessment_ids == [1, 2]

    def test_report_create_默认章节(self):
        """测试默认包含的报告章节"""
        report = ReportCreate(
            name="测试报告",
            assessment_ids=[1]
        )
        assert "summary" in report.include_sections
        assert "charts" in report.include_sections
        assert "statistics" in report.include_sections
        assert "problem_frames" in report.include_sections

    def test_report_create_自定义章节(self):
        """测试自定义报告章节"""
        report = ReportCreate(
            name="测试报告",
            assessment_ids=[1],
            include_sections=["summary", "charts"]
        )
        assert report.include_sections == ["summary", "charts"]
