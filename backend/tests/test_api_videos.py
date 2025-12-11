"""视频 API 集成测试"""
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoType


class TestVideosAPI:
    """视频 API 测试类"""

    @pytest.fixture
    async def sample_video(self, test_db: AsyncSession) -> Video:
        """创建测试视频"""
        video = Video(
            filename="test123.mp4",
            original_filename="测试视频.mp4",
            file_path="/uploads/test123.mp4",
            file_size=1024000,
            width=1920,
            height=1080,
            duration=120.0,
            frame_rate=30.0,
            frame_count=3600,
            codec="h264",
            bitrate=5000000,
            video_type=VideoType.DISTORTED
        )
        test_db.add(video)
        await test_db.commit()
        await test_db.refresh(video)
        return video

    @pytest.fixture
    async def multiple_videos(self, test_db: AsyncSession) -> list[Video]:
        """创建多个测试视频"""
        videos = []
        for i in range(5):
            video = Video(
                filename=f"video{i}.mp4",
                original_filename=f"视频{i}.mp4",
                file_path=f"/uploads/video{i}.mp4",
                file_size=1024000 * (i + 1),
                width=1920,
                height=1080,
                duration=60.0 * (i + 1),
                video_type=VideoType.REFERENCE if i % 2 == 0 else VideoType.DISTORTED
            )
            test_db.add(video)
            videos.append(video)

        await test_db.commit()
        for video in videos:
            await test_db.refresh(video)

        return videos

    @pytest.mark.asyncio
    async def test_list_videos_空列表(self, client: AsyncClient):
        """测试获取空视频列表"""
        response = await client.get("/api/videos")

        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_videos_有数据(
        self, client: AsyncClient, multiple_videos: list[Video]
    ):
        """测试获取视频列表"""
        response = await client.get("/api/videos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["videos"]) == 5

    @pytest.mark.asyncio
    async def test_list_videos_分页(
        self, client: AsyncClient, multiple_videos: list[Video]
    ):
        """测试视频列表分页"""
        response = await client.get("/api/videos?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["videos"]) == 2

    @pytest.mark.asyncio
    async def test_list_videos_按类型筛选参考视频(
        self, client: AsyncClient, multiple_videos: list[Video]
    ):
        """测试按参考视频类型筛选"""
        response = await client.get("/api/videos?video_type=reference")

        assert response.status_code == 200
        data = response.json()
        # 视频 0, 2, 4 是参考视频
        assert data["total"] == 3
        for video in data["videos"]:
            assert video["video_type"] == "reference"

    @pytest.mark.asyncio
    async def test_list_videos_按类型筛选待测视频(
        self, client: AsyncClient, multiple_videos: list[Video]
    ):
        """测试按待测视频类型筛选"""
        response = await client.get("/api/videos?video_type=distorted")

        assert response.status_code == 200
        data = response.json()
        # 视频 1, 3 是待测视频
        assert data["total"] == 2
        for video in data["videos"]:
            assert video["video_type"] == "distorted"

    @pytest.mark.asyncio
    async def test_get_video_存在(
        self, client: AsyncClient, sample_video: Video
    ):
        """测试获取存在的视频"""
        response = await client.get(f"/api/videos/{sample_video.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_video.id
        assert data["filename"] == "test123.mp4"
        assert data["original_filename"] == "测试视频.mp4"
        assert data["width"] == 1920
        assert data["height"] == 1080

    @pytest.mark.asyncio
    async def test_get_video_不存在(self, client: AsyncClient):
        """测试获取不存在的视频"""
        response = await client.get("/api/videos/99999")

        assert response.status_code == 404
        assert "视频不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_video_type_改为参考视频(
        self, client: AsyncClient, sample_video: Video
    ):
        """测试将视频类型改为参考视频"""
        response = await client.patch(
            f"/api/videos/{sample_video.id}/type?video_type=reference"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["video_type"] == "reference"

    @pytest.mark.asyncio
    async def test_update_video_type_改为待测视频(
        self, client: AsyncClient, sample_video: Video
    ):
        """测试将视频类型改为待测视频"""
        response = await client.patch(
            f"/api/videos/{sample_video.id}/type?video_type=distorted"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["video_type"] == "distorted"

    @pytest.mark.asyncio
    async def test_update_video_type_无效类型(
        self, client: AsyncClient, sample_video: Video
    ):
        """测试无效的视频类型"""
        response = await client.patch(
            f"/api/videos/{sample_video.id}/type?video_type=invalid"
        )

        assert response.status_code == 400
        assert "无效的视频类型" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_video_type_视频不存在(self, client: AsyncClient):
        """测试更新不存在的视频类型"""
        response = await client.patch("/api/videos/99999/type?video_type=reference")

        assert response.status_code == 404
        assert "视频不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_video_存在(
        self, client: AsyncClient, sample_video: Video
    ):
        """测试删除存在的视频"""
        response = await client.delete(f"/api/videos/{sample_video.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "删除成功"

        # 验证视频已被删除
        response = await client.get(f"/api/videos/{sample_video.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_video_不存在(self, client: AsyncClient):
        """测试删除不存在的视频"""
        response = await client.delete("/api/videos/99999")

        assert response.status_code == 404
        assert "视频不存在" in response.json()["detail"]
