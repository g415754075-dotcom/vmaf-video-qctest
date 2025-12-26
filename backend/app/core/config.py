"""应用配置"""
import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本信息
    app_name: str = "VMAF Video QC Test"
    app_version: str = "0.1.0"
    debug: bool = True

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS 配置 - 使用字符串，支持逗号分隔或 JSON 格式
    cors_origins_str: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        """解析 CORS origins"""
        value = self.cors_origins_str
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    # 文件上传配置
    upload_dir: Path = Path("uploads")
    max_file_size: int = 4 * 1024 * 1024 * 1024  # 4GB
    allowed_extensions: List[str] = [".mp4", ".mkv", ".mov", ".avi", ".webm", ".y4m"]
    chunk_size: int = 10 * 1024 * 1024  # 10MB 分片大小

    # 报告配置
    reports_dir: Path = Path("reports")
    report_retention_days: int = 30

    # FFmpeg 配置
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    vmaf_model_path: str = "/usr/share/model/vmaf_v0.6.1.json"
    vmaf_4k_model_path: str = "/usr/share/model/vmaf_4k_v0.6.1.json"

    # 任务配置
    max_concurrent_tasks: int = 3
    task_timeout: int = 3600  # 1小时

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./vmaf_qctest.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保目录存在
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
