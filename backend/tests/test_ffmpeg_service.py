"""FFmpeg 服务单元测试"""
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.ffmpeg_service import FFmpegService, VideoInfo, QualityResult


class TestFFmpegService:
    """FFmpeg 服务测试类"""

    @pytest.fixture
    def ffmpeg_service(self) -> FFmpegService:
        """创建 FFmpeg 服务实例"""
        return FFmpegService()

    def test_get_vmaf_model_标准分辨率(self, ffmpeg_service: FFmpegService):
        """测试标准分辨率使用标准 VMAF 模型"""
        model = ffmpeg_service._get_vmaf_model(1920, 1080)
        assert "vmaf_v0.6.1" in model
        assert "4k" not in model

    def test_get_vmaf_model_4K分辨率宽度(self, ffmpeg_service: FFmpegService):
        """测试 4K 分辨率（宽度）使用 4K 模型"""
        model = ffmpeg_service._get_vmaf_model(3840, 2160)
        assert "4k" in model

    def test_get_vmaf_model_4K分辨率高度(self, ffmpeg_service: FFmpegService):
        """测试超过 2160 高度使用 4K 模型"""
        model = ffmpeg_service._get_vmaf_model(1920, 2160)
        assert "4k" in model

    def test_get_vmaf_model_低于4K(self, ffmpeg_service: FFmpegService):
        """测试略低于 4K 使用标准模型"""
        model = ffmpeg_service._get_vmaf_model(3839, 2159)
        assert "4k" not in model

    @pytest.mark.asyncio
    async def test_get_video_info_成功解析(self, ffmpeg_service: FFmpegService):
        """测试成功解析视频信息"""
        mock_output = json.dumps({
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "nb_frames": "300",
                    "pix_fmt": "yuv420p",
                    "bit_rate": "5000000"
                }
            ],
            "format": {
                "duration": "10.0",
                "bit_rate": "5500000"
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output.encode(), b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            info = await ffmpeg_service.get_video_info("/path/to/video.mp4")

            assert info.width == 1920
            assert info.height == 1080
            assert info.duration == 10.0
            assert info.frame_rate == 30.0
            assert info.frame_count == 300
            assert info.codec == "h264"
            assert info.bitrate == 5500000
            assert info.pixel_format == "yuv420p"

    @pytest.mark.asyncio
    async def test_get_video_info_分数帧率解析(self, ffmpeg_service: FFmpegService):
        """测试分数帧率正确解析"""
        mock_output = json.dumps({
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "24000/1001",
                    "pix_fmt": "yuv420p"
                }
            ],
            "format": {
                "duration": "10.0"
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output.encode(), b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            info = await ffmpeg_service.get_video_info("/path/to/video.mp4")

            # 24000/1001 ≈ 23.976
            assert abs(info.frame_rate - 23.976) < 0.01

    @pytest.mark.asyncio
    async def test_get_video_info_无视频流抛出异常(self, ffmpeg_service: FFmpegService):
        """测试无视频流时抛出异常"""
        mock_output = json.dumps({
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac"
                }
            ],
            "format": {}
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output.encode(), b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            with pytest.raises(ValueError, match="未找到视频流"):
                await ffmpeg_service.get_video_info("/path/to/audio.mp3")

    @pytest.mark.asyncio
    async def test_get_video_info_ffprobe失败抛出异常(self, ffmpeg_service: FFmpegService):
        """测试 ffprobe 执行失败时抛出异常"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Error: file not found")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            with pytest.raises(RuntimeError, match="ffprobe 执行失败"):
                await ffmpeg_service.get_video_info("/nonexistent/video.mp4")

    @pytest.mark.asyncio
    async def test_get_video_info_自动计算帧数(self, ffmpeg_service: FFmpegService):
        """测试从时长和帧率自动计算帧数"""
        mock_output = json.dumps({
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "nb_frames": "0",  # 帧数为0，需要自动计算
                    "pix_fmt": "yuv420p"
                }
            ],
            "format": {
                "duration": "10.0"
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output.encode(), b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            info = await ffmpeg_service.get_video_info("/path/to/video.mp4")

            # 10秒 * 30fps = 300帧
            assert info.frame_count == 300

    @pytest.mark.asyncio
    async def test_generate_thumbnail_成功(self, ffmpeg_service: FFmpegService):
        """测试成功生成缩略图"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await ffmpeg_service.generate_thumbnail(
                video_path="/path/to/video.mp4",
                output_path="/path/to/thumb.jpg",
                time_offset=2.0,
                width=320
            )

            assert result == "/path/to/thumb.jpg"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_thumbnail_失败抛出异常(self, ffmpeg_service: FFmpegService):
        """测试生成缩略图失败时抛出异常"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Error generating thumbnail")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            with pytest.raises(RuntimeError, match="生成缩略图失败"):
                await ffmpeg_service.generate_thumbnail(
                    video_path="/path/to/video.mp4",
                    output_path="/path/to/thumb.jpg"
                )

    @pytest.mark.asyncio
    async def test_parse_vmaf_json_正确解析结果(self, ffmpeg_service: FFmpegService):
        """测试正确解析 VMAF JSON 结果"""
        vmaf_data = {
            "frames": [
                {"frameNum": 0, "metrics": {"vmaf": 90.5, "float_ssim": 0.98, "psnr": 40.0}},
                {"frameNum": 1, "metrics": {"vmaf": 91.0, "float_ssim": 0.97, "psnr": 39.5}},
                {"frameNum": 2, "metrics": {"vmaf": 89.0, "float_ssim": 0.99, "psnr": 41.0}},
            ],
            "pooled_metrics": {
                "vmaf": {"mean": 90.17, "min": 89.0, "max": 91.0}
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(vmaf_data, f)
            temp_path = f.name

        try:
            result = await ffmpeg_service._parse_vmaf_json(temp_path)

            assert result.vmaf_score == 90.17
            assert result.vmaf_min == 89.0
            assert result.vmaf_max == 91.0
            assert abs(result.ssim_score - 0.98) < 0.01
            assert abs(result.psnr_score - 40.17) < 0.01
            assert len(result.frame_data) == 3
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_parse_vmaf_json_帧数据结构正确(self, ffmpeg_service: FFmpegService):
        """测试解析后的帧数据结构正确"""
        vmaf_data = {
            "frames": [
                {"frameNum": 0, "metrics": {"vmaf": 90.0, "float_ssim": 0.98, "psnr": 40.0}},
            ],
            "pooled_metrics": {
                "vmaf": {"mean": 90.0, "min": 90.0, "max": 90.0}
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(vmaf_data, f)
            temp_path = f.name

        try:
            result = await ffmpeg_service._parse_vmaf_json(temp_path)

            assert len(result.frame_data) == 1
            frame = result.frame_data[0]
            assert frame["frame_num"] == 0
            assert frame["vmaf"] == 90.0
            assert frame["ssim"] == 0.98
            assert frame["psnr"] == 40.0
        finally:
            Path(temp_path).unlink()


class TestVideoInfo:
    """VideoInfo 数据类测试"""

    def test_video_info_创建(self):
        """测试 VideoInfo 创建"""
        info = VideoInfo(
            width=1920,
            height=1080,
            duration=120.5,
            frame_rate=30.0,
            frame_count=3615,
            codec="h264",
            bitrate=5000000,
            pixel_format="yuv420p"
        )

        assert info.width == 1920
        assert info.height == 1080
        assert info.duration == 120.5
        assert info.frame_rate == 30.0
        assert info.frame_count == 3615
        assert info.codec == "h264"
        assert info.bitrate == 5000000
        assert info.pixel_format == "yuv420p"


class TestQualityResult:
    """QualityResult 数据类测试"""

    def test_quality_result_创建(self):
        """测试 QualityResult 创建"""
        result = QualityResult(
            vmaf_score=90.5,
            vmaf_min=85.0,
            vmaf_max=95.0,
            ssim_score=0.98,
            psnr_score=40.5,
            ms_ssim_score=0.97,
            frame_data=[{"frame_num": 0, "vmaf": 90.5}]
        )

        assert result.vmaf_score == 90.5
        assert result.vmaf_min == 85.0
        assert result.vmaf_max == 95.0
        assert result.ssim_score == 0.98
        assert result.psnr_score == 40.5
        assert result.ms_ssim_score == 0.97
        assert len(result.frame_data) == 1

    def test_quality_result_可选字段为None(self):
        """测试 ms_ssim_score 可以为 None"""
        result = QualityResult(
            vmaf_score=90.0,
            vmaf_min=85.0,
            vmaf_max=95.0,
            ssim_score=0.98,
            psnr_score=40.0,
            ms_ssim_score=None,
            frame_data=[]
        )

        assert result.ms_ssim_score is None
