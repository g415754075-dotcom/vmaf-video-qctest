"""FFmpeg 服务 - 视频处理和质量评估"""
import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class VideoInfo:
    """视频信息"""
    width: int
    height: int
    duration: float
    frame_rate: float
    frame_count: int
    codec: str
    bitrate: int
    pixel_format: str


@dataclass
class QualityResult:
    """质量评估结果"""
    vmaf_score: float
    vmaf_min: float
    vmaf_max: float
    ssim_score: float
    psnr_score: float
    ms_ssim_score: Optional[float]
    frame_data: list[dict]


class FFmpegService:
    """FFmpeg 服务类"""

    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
        self.ffprobe_path = settings.ffprobe_path
        self.vmaf_model_path = settings.vmaf_model_path
        self.vmaf_4k_model_path = settings.vmaf_4k_model_path

    async def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频元信息"""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"ffprobe 执行失败: {stderr.decode()}")

        data = json.loads(stdout.decode())

        # 查找视频流
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            raise ValueError("未找到视频流")

        # 解析帧率
        frame_rate_str = video_stream.get("r_frame_rate", "30/1")
        if "/" in frame_rate_str:
            num, den = map(int, frame_rate_str.split("/"))
            frame_rate = num / den if den > 0 else 30.0
        else:
            frame_rate = float(frame_rate_str)

        # 计算帧数
        duration = float(data.get("format", {}).get("duration", 0))
        frame_count = int(video_stream.get("nb_frames", 0))
        if frame_count == 0:
            frame_count = int(duration * frame_rate)

        # 计算比特率
        bitrate = int(data.get("format", {}).get("bit_rate", 0))
        if bitrate == 0:
            bitrate = int(video_stream.get("bit_rate", 0))

        return VideoInfo(
            width=int(video_stream.get("width", 0)),
            height=int(video_stream.get("height", 0)),
            duration=duration,
            frame_rate=frame_rate,
            frame_count=frame_count,
            codec=video_stream.get("codec_name", "unknown"),
            bitrate=bitrate,
            pixel_format=video_stream.get("pix_fmt", "unknown")
        )

    async def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time_offset: float = 1.0,
        width: int = 320
    ) -> str:
        """生成视频缩略图"""
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", str(time_offset),
            "-i", video_path,
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"生成缩略图失败: {stderr.decode()}")

        return output_path

    def _get_vmaf_model(self, width: int, height: int) -> str:
        """根据分辨率选择 VMAF 模型"""
        if width >= 3840 or height >= 2160:
            return self.vmaf_4k_model_path
        return self.vmaf_model_path

    async def assess_quality(
        self,
        reference_path: str,
        distorted_path: str,
        output_json_path: str,
        progress_callback: Optional[callable] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行质量评估（VMAF、SSIM、PSNR）
        使用生成器返回进度和最终结果
        """
        # 获取视频信息
        ref_info = await self.get_video_info(reference_path)
        dist_info = await self.get_video_info(distorted_path)

        # 选择 VMAF 模型
        vmaf_model = self._get_vmaf_model(ref_info.width, ref_info.height)

        # 构建缩放滤镜（如果分辨率不匹配）
        scale_filter = ""
        if dist_info.width != ref_info.width or dist_info.height != ref_info.height:
            scale_filter = f"scale={ref_info.width}:{ref_info.height}:flags=bicubic,"

        # 构建 FFmpeg 命令
        # FFmpeg 8.x 使用 model=path=xxx 格式，旧版本使用 model_path=xxx
        # libvmaf 输入顺序: #0=main(distorted), #1=reference
        # feature 使用 | 分隔多个特征：psnr 输出 psnr_y/psnr_cb/psnr_cr
        filter_complex = (
            f"[0:v]{scale_filter}setpts=PTS-STARTPTS[distorted];"
            f"[1:v]setpts=PTS-STARTPTS[reference];"
            f"[distorted][reference]libvmaf="
            f"log_fmt=json:"
            f"log_path={output_json_path}:"
            f"model=path={vmaf_model}:"
            f"n_threads=4:"
            f"feature=name=psnr|name=float_ssim"
        )

        cmd = [
            self.ffmpeg_path,
            "-i", distorted_path,
            "-i", reference_path,
            "-lavfi", filter_complex,
            "-f", "null",
            "-"
        ]

        # 执行命令，使用 -progress 参数输出进度到 stdout
        cmd_with_progress = cmd + ["-progress", "pipe:1"]

        process = await asyncio.create_subprocess_exec(
            *cmd_with_progress,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        total_frames = ref_info.frame_count
        current_frame = 0
        last_reported_frame = -1

        # 从 stdout 读取进度信息（-progress pipe:1 输出）
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode("utf-8", errors="ignore").strip()

            # 解析 -progress 输出的 frame=N 格式
            if line_str.startswith("frame="):
                try:
                    current_frame = int(line_str.split("=")[1])
                    # 避免重复报告相同帧
                    if current_frame != last_reported_frame:
                        last_reported_frame = current_frame
                        progress = (current_frame / total_frames * 100) if total_frames > 0 else 0

                        yield {
                            "type": "progress",
                            "current_frame": current_frame,
                            "total_frames": total_frames,
                            "progress": min(progress, 100)
                        }
                except (ValueError, IndexError):
                    pass

        await process.wait()

        if process.returncode != 0:
            raise RuntimeError("FFmpeg 质量评估失败")

        # 解析结果
        result = await self._parse_vmaf_json(output_json_path)

        yield {
            "type": "complete",
            "result": result
        }

    async def _parse_vmaf_json(self, json_path: str) -> QualityResult:
        """解析 VMAF JSON 输出"""
        with open(json_path, "r") as f:
            data = json.load(f)

        frames = data.get("frames", [])
        pooled_metrics = data.get("pooled_metrics", {})

        # 提取逐帧数据
        frame_data = []
        vmaf_scores = []
        ssim_scores = []
        psnr_scores = []

        for frame in frames:
            frame_num = frame.get("frameNum", 0)
            metrics = frame.get("metrics", {})

            vmaf = metrics.get("vmaf")
            ssim = metrics.get("float_ssim")
            # PSNR Y 通道（亮度）是最常用的 PSNR 指标
            psnr = metrics.get("psnr_y")

            if vmaf is not None:
                vmaf_scores.append(vmaf)
            if ssim is not None:
                ssim_scores.append(ssim)
            if psnr is not None:
                psnr_scores.append(psnr)

            frame_data.append({
                "frame_num": frame_num,
                "vmaf": vmaf,
                "ssim": ssim,
                "psnr": psnr
            })

        # 计算汇总指标
        vmaf_mean = pooled_metrics.get("vmaf", {}).get("mean", 0)
        vmaf_min = pooled_metrics.get("vmaf", {}).get("min", 0)
        vmaf_max = pooled_metrics.get("vmaf", {}).get("max", 0)

        ssim_mean = sum(ssim_scores) / len(ssim_scores) if ssim_scores else 0
        psnr_mean = sum(psnr_scores) / len(psnr_scores) if psnr_scores else 0

        return QualityResult(
            vmaf_score=vmaf_mean,
            vmaf_min=vmaf_min,
            vmaf_max=vmaf_max,
            ssim_score=ssim_mean,
            psnr_score=psnr_mean,
            ms_ssim_score=None,
            frame_data=frame_data
        )


# 创建服务实例
ffmpeg_service = FFmpegService()
