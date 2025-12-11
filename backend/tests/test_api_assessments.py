"""评估任务 API 集成测试"""
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, Assessment, VideoType, TaskStatus


class TestAssessmentsAPI:
    """评估任务 API 测试类"""

    @pytest.fixture
    async def reference_video(self, test_db: AsyncSession) -> Video:
        """创建参考视频"""
        video = Video(
            filename="reference.mp4",
            original_filename="参考视频.mp4",
            file_path="/uploads/reference.mp4",
            file_size=10240000,
            width=1920,
            height=1080,
            duration=60.0,
            frame_rate=30.0,
            frame_count=1800,
            codec="h264",
            bitrate=5000000,
            video_type=VideoType.REFERENCE
        )
        test_db.add(video)
        await test_db.commit()
        await test_db.refresh(video)
        return video

    @pytest.fixture
    async def distorted_video(self, test_db: AsyncSession) -> Video:
        """创建待测视频"""
        video = Video(
            filename="distorted.mp4",
            original_filename="待测视频.mp4",
            file_path="/uploads/distorted.mp4",
            file_size=5120000,
            width=1920,
            height=1080,
            duration=60.0,
            frame_rate=30.0,
            frame_count=1800,
            codec="h264",
            bitrate=2500000,
            video_type=VideoType.DISTORTED
        )
        test_db.add(video)
        await test_db.commit()
        await test_db.refresh(video)
        return video

    @pytest.fixture
    async def completed_assessment(
        self, test_db: AsyncSession, reference_video: Video, distorted_video: Video
    ) -> Assessment:
        """创建已完成的评估任务"""
        assessment = Assessment(
            reference_video_id=reference_video.id,
            distorted_video_id=distorted_video.id,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            current_frame=1800,
            total_frames=1800,
            vmaf_score=90.5,
            vmaf_min=85.0,
            vmaf_max=95.0,
            ssim_score=0.98,
            psnr_score=40.5,
            vmaf_model="vmaf_v0.6.1",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)
        return assessment

    @pytest.fixture
    async def multiple_assessments(
        self, test_db: AsyncSession, reference_video: Video
    ) -> list[Assessment]:
        """创建多个评估任务"""
        assessments = []

        for i in range(3):
            # 创建待测视频
            dist_video = Video(
                filename=f"distorted{i}.mp4",
                original_filename=f"待测视频{i}.mp4",
                file_path=f"/uploads/distorted{i}.mp4",
                file_size=5120000,
                width=1920,
                height=1080,
                duration=60.0,
                codec="h264",
                bitrate=2500000 * (i + 1),
                video_type=VideoType.DISTORTED
            )
            test_db.add(dist_video)
            await test_db.flush()

            # 创建评估任务
            assessment = Assessment(
                reference_video_id=reference_video.id,
                distorted_video_id=dist_video.id,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                current_frame=1800,
                total_frames=1800,
                vmaf_score=90.0 - i * 5,  # 90, 85, 80
                vmaf_min=85.0 - i * 5,
                vmaf_max=95.0 - i * 5,
                ssim_score=0.98 - i * 0.02,
                psnr_score=40.0 - i * 2,
                vmaf_model="vmaf_v0.6.1"
            )
            test_db.add(assessment)
            assessments.append(assessment)

        await test_db.commit()
        for a in assessments:
            await test_db.refresh(a)

        return assessments

    @pytest.mark.asyncio
    async def test_create_assessment_成功(
        self,
        client: AsyncClient,
        reference_video: Video,
        distorted_video: Video
    ):
        """测试创建评估任务成功"""
        with patch(
            "app.services.assessment_service.assessment_service.create_assessment"
        ) as mock_create:
            # 模拟创建返回
            mock_assessment = Assessment(
                id=1,
                reference_video_id=reference_video.id,
                distorted_video_id=distorted_video.id,
                status=TaskStatus.PENDING,
                progress=0.0,
                current_frame=0,
                total_frames=0,
                vmaf_model="vmaf_v0.6.1"
            )
            mock_create.return_value = mock_assessment

            response = await client.post(
                "/api/assessments",
                json={
                    "reference_video_id": reference_video.id,
                    "distorted_video_id": distorted_video.id
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["reference_video_id"] == reference_video.id
            assert data["distorted_video_id"] == distorted_video.id
            assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_assessment_视频不存在(self, client: AsyncClient):
        """测试创建评估任务时视频不存在"""
        with patch(
            "app.services.assessment_service.assessment_service.create_assessment"
        ) as mock_create:
            mock_create.side_effect = ValueError("视频不存在")

            response = await client.post(
                "/api/assessments",
                json={
                    "reference_video_id": 99999,
                    "distorted_video_id": 99998
                }
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_assessments_空列表(self, client: AsyncClient):
        """测试获取空评估任务列表"""
        with patch(
            "app.services.assessment_service.assessment_service.list_assessments"
        ) as mock_list:
            mock_list.return_value = ([], 0)

            response = await client.get("/api/assessments")

            assert response.status_code == 200
            data = response.json()
            assert data["assessments"] == []
            assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_assessment_存在(
        self, client: AsyncClient, completed_assessment: Assessment
    ):
        """测试获取存在的评估任务"""
        with patch(
            "app.services.assessment_service.assessment_service.get_assessment"
        ) as mock_get:
            mock_get.return_value = completed_assessment

            response = await client.get(f"/api/assessments/{completed_assessment.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == completed_assessment.id
            assert data["vmaf_score"] == 90.5
            assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_assessment_不存在(self, client: AsyncClient):
        """测试获取不存在的评估任务"""
        with patch(
            "app.services.assessment_service.assessment_service.get_assessment"
        ) as mock_get:
            mock_get.return_value = None

            response = await client.get("/api/assessments/99999")

            assert response.status_code == 404
            assert "评估任务不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_assessment_成功(
        self, client: AsyncClient, completed_assessment: Assessment
    ):
        """测试取消评估任务"""
        with patch(
            "app.services.assessment_service.assessment_service.cancel_assessment"
        ) as mock_cancel:
            mock_cancel.return_value = None

            response = await client.post(
                f"/api/assessments/{completed_assessment.id}/cancel"
            )

            assert response.status_code == 200
            assert response.json()["message"] == "评估任务已取消"

    @pytest.mark.asyncio
    async def test_cancel_assessment_不存在(self, client: AsyncClient):
        """测试取消不存在的评估任务"""
        with patch(
            "app.services.assessment_service.assessment_service.cancel_assessment"
        ) as mock_cancel:
            mock_cancel.side_effect = ValueError("评估任务不存在")

            response = await client.post("/api/assessments/99999/cancel")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_frame_data_存在(
        self, client: AsyncClient, completed_assessment: Assessment
    ):
        """测试获取逐帧数据"""
        frame_data = [
            {"frame_num": 0, "vmaf": 90.0, "ssim": 0.98, "psnr": 40.0},
            {"frame_num": 1, "vmaf": 91.0, "ssim": 0.97, "psnr": 39.5},
            {"frame_num": 2, "vmaf": 89.0, "ssim": 0.99, "psnr": 41.0},
        ]

        with patch(
            "app.services.assessment_service.assessment_service.get_frame_data"
        ) as mock_frames:
            mock_frames.return_value = frame_data

            response = await client.get(
                f"/api/assessments/{completed_assessment.id}/frames"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["assessment_id"] == completed_assessment.id
            assert data["total_frames"] == 3
            assert len(data["frames"]) == 3

    @pytest.mark.asyncio
    async def test_get_frame_data_不存在(self, client: AsyncClient):
        """测试获取不存在的逐帧数据"""
        with patch(
            "app.services.assessment_service.assessment_service.get_frame_data"
        ) as mock_frames:
            mock_frames.return_value = None

            response = await client.get("/api/assessments/99999/frames")

            assert response.status_code == 404
            assert "逐帧数据不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_statistics_存在(
        self, client: AsyncClient, completed_assessment: Assessment
    ):
        """测试获取统计数据"""
        stats = {
            "assessment_id": completed_assessment.id,
            "vmaf": {
                "mean": 90.0, "min": 85.0, "max": 95.0,
                "median": 90.0, "std": 2.5, "p5": 86.0, "p95": 94.0
            },
            "ssim": {
                "mean": 0.98, "min": 0.95, "max": 0.99,
                "median": 0.98, "std": 0.01, "p5": 0.96, "p95": 0.99
            },
            "psnr": {
                "mean": 40.0, "min": 35.0, "max": 45.0,
                "median": 40.0, "std": 2.0, "p5": 36.0, "p95": 44.0
            }
        }

        with patch(
            "app.services.assessment_service.assessment_service.get_statistics"
        ) as mock_stats:
            mock_stats.return_value = stats

            response = await client.get(
                f"/api/assessments/{completed_assessment.id}/statistics"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["assessment_id"] == completed_assessment.id
            assert data["vmaf"]["mean"] == 90.0
            assert data["ssim"]["mean"] == 0.98

    @pytest.mark.asyncio
    async def test_get_problem_frames(
        self, client: AsyncClient, completed_assessment: Assessment
    ):
        """测试获取问题帧"""
        problem_frames = [
            {"frame_num": 100, "vmaf": 65.0, "ssim": 0.92, "psnr": 32.0},
            {"frame_num": 200, "vmaf": 68.0, "ssim": 0.93, "psnr": 33.0},
        ]

        with patch(
            "app.services.assessment_service.assessment_service.get_problem_frames"
        ) as mock_problems:
            mock_problems.return_value = problem_frames

            response = await client.get(
                f"/api/assessments/{completed_assessment.id}/problem-frames?threshold=70&limit=10"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["assessment_id"] == completed_assessment.id
            assert data["threshold"] == 70
            assert len(data["frames"]) == 2

    @pytest.mark.asyncio
    async def test_compare_assessments_成功(
        self, client: AsyncClient, multiple_assessments: list[Assessment]
    ):
        """测试对比评估结果"""
        assessment_ids = [a.id for a in multiple_assessments[:2]]

        with patch(
            "app.services.assessment_service.assessment_service.get_assessment"
        ) as mock_get:
            # 模拟返回评估任务
            async def side_effect(session, aid):
                for a in multiple_assessments:
                    if a.id == aid:
                        return a
                return None

            mock_get.side_effect = side_effect

            response = await client.post(
                "/api/assessments/compare",
                json={"assessment_ids": assessment_ids}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_compare_assessments_少于两个(self, client: AsyncClient):
        """测试对比评估数量少于两个"""
        response = await client.post(
            "/api/assessments/compare",
            json={"assessment_ids": [1]}
        )

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_compare_assessments_超过五个(self, client: AsyncClient):
        """测试对比评估数量超过五个"""
        response = await client.post(
            "/api/assessments/compare",
            json={"assessment_ids": [1, 2, 3, 4, 5, 6]}
        )

        assert response.status_code == 422  # 验证错误
