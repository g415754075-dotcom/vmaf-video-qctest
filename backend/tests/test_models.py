"""数据模型单元测试"""
from datetime import datetime

import pytest

from app.models.video import Video, Assessment, Report, VideoType, TaskStatus


class TestVideoType:
    """VideoType 枚举测试"""

    def test_video_type_参考视频(self):
        """测试参考视频类型"""
        assert VideoType.REFERENCE.value == "reference"

    def test_video_type_待测视频(self):
        """测试待测视频类型"""
        assert VideoType.DISTORTED.value == "distorted"

    def test_video_type_枚举值唯一(self):
        """测试枚举值唯一性"""
        values = [vt.value for vt in VideoType]
        assert len(values) == len(set(values))


class TestTaskStatus:
    """TaskStatus 枚举测试"""

    def test_task_status_所有状态(self):
        """测试所有任务状态"""
        expected_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        actual_statuses = [ts.value for ts in TaskStatus]
        assert sorted(actual_statuses) == sorted(expected_statuses)

    def test_task_status_等待中(self):
        """测试等待中状态"""
        assert TaskStatus.PENDING.value == "pending"

    def test_task_status_运行中(self):
        """测试运行中状态"""
        assert TaskStatus.RUNNING.value == "running"

    def test_task_status_已完成(self):
        """测试已完成状态"""
        assert TaskStatus.COMPLETED.value == "completed"

    def test_task_status_失败(self):
        """测试失败状态"""
        assert TaskStatus.FAILED.value == "failed"

    def test_task_status_已取消(self):
        """测试已取消状态"""
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestVideoModel:
    """Video 模型测试"""

    def test_video_必填字段(self):
        """测试视频模型必填字段"""
        # 通过检查模型列定义验证必填字段
        from app.models.video import Video

        required_fields = ["filename", "original_filename", "file_path", "file_size"]
        for field in required_fields:
            column = getattr(Video, field).property.columns[0]
            assert not column.nullable, f"{field} 应该是必填字段"

    def test_video_可选字段(self):
        """测试视频模型可选字段"""
        optional_fields = [
            "width", "height", "duration", "frame_rate",
            "frame_count", "codec", "bitrate", "pixel_format", "thumbnail_path"
        ]
        for field in optional_fields:
            column = getattr(Video, field).property.columns[0]
            assert column.nullable, f"{field} 应该是可选字段"

    def test_video_默认类型(self):
        """测试视频默认类型为待测视频"""
        column = Video.video_type.property.columns[0]
        assert column.default.arg == VideoType.DISTORTED


class TestAssessmentModel:
    """Assessment 模型测试"""

    def test_assessment_必填字段(self):
        """测试评估任务必填字段"""
        required_fields = ["reference_video_id", "distorted_video_id"]
        for field in required_fields:
            column = getattr(Assessment, field).property.columns[0]
            assert not column.nullable, f"{field} 应该是必填字段"

    def test_assessment_默认状态(self):
        """测试评估任务默认状态为等待中"""
        column = Assessment.status.property.columns[0]
        assert column.default.arg == TaskStatus.PENDING

    def test_assessment_默认进度为零(self):
        """测试评估任务默认进度为 0"""
        column = Assessment.progress.property.columns[0]
        assert column.default.arg == 0.0

    def test_assessment_结果字段可选(self):
        """测试评估结果字段都是可选的"""
        result_fields = [
            "vmaf_score", "vmaf_min", "vmaf_max",
            "ssim_score", "psnr_score", "ms_ssim_score"
        ]
        for field in result_fields:
            column = getattr(Assessment, field).property.columns[0]
            assert column.nullable, f"{field} 应该是可选字段"


class TestReportModel:
    """Report 模型测试"""

    def test_report_必填字段(self):
        """测试报告必填字段"""
        required_fields = ["name", "report_type", "assessment_ids"]
        for field in required_fields:
            column = getattr(Report, field).property.columns[0]
            assert not column.nullable, f"{field} 应该是必填字段"

    def test_report_文件路径可选(self):
        """测试报告文件路径可选"""
        path_fields = ["pdf_path", "excel_path", "json_path"]
        for field in path_fields:
            column = getattr(Report, field).property.columns[0]
            assert column.nullable, f"{field} 应该是可选字段"

    def test_report_分享字段可选(self):
        """测试分享相关字段可选"""
        share_fields = ["share_token", "share_expires_at"]
        for field in share_fields:
            column = getattr(Report, field).property.columns[0]
            assert column.nullable, f"{field} 应该是可选字段"
