"""应用配置"""
from pathlib import Path
from typing import List, Union

from pydantic import field_validator
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

    # CORS 配置 - 支持逗号分隔的字符串或 JSON 数组
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """解析 CORS origins，支持逗号分隔的字符串"""
        if isinstance(v, str):
            # 如果是 JSON 格式的字符串，尝试解析
            if v.startswith("["):
                import json
                return json.loads(v)
            # 否则按逗号分隔
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

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
