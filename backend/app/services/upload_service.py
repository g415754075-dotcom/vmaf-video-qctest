"""文件上传服务 - 分片上传和断点续传"""
import hashlib
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict
import aiofiles
import aiofiles.os

from app.core.config import settings


class UploadService:
    """文件上传服务类"""

    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.chunk_dir = self.upload_dir / "chunks"
        self.chunk_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, filename: str, file_size: int) -> str:
        """生成文件唯一标识"""
        content = f"{filename}_{file_size}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_chunk_dir(self, file_hash: str) -> Path:
        """获取分片存储目录"""
        chunk_path = self.chunk_dir / file_hash
        chunk_path.mkdir(parents=True, exist_ok=True)
        return chunk_path

    def _get_chunk_path(self, file_hash: str, chunk_index: int) -> Path:
        """获取分片文件路径"""
        return self._get_chunk_dir(file_hash) / f"chunk_{chunk_index}"

    async def save_chunk(
        self,
        filename: str,
        file_size: int,
        chunk_index: int,
        chunk_data: bytes
    ) -> bool:
        """保存上传分片"""
        file_hash = self._get_file_hash(filename, file_size)
        chunk_path = self._get_chunk_path(file_hash, chunk_index)

        async with aiofiles.open(chunk_path, "wb") as f:
            await f.write(chunk_data)

        return True

    async def get_uploaded_chunks(self, filename: str, file_size: int) -> List[int]:
        """获取已上传的分片列表"""
        file_hash = self._get_file_hash(filename, file_size)
        chunk_dir = self._get_chunk_dir(file_hash)

        uploaded_chunks = []
        if chunk_dir.exists():
            for chunk_file in chunk_dir.iterdir():
                if chunk_file.name.startswith("chunk_"):
                    try:
                        chunk_index = int(chunk_file.name.split("_")[1])
                        uploaded_chunks.append(chunk_index)
                    except (ValueError, IndexError):
                        continue

        return sorted(uploaded_chunks)

    async def merge_chunks(
        self,
        filename: str,
        file_size: int,
        total_chunks: int,
        target_filename: str
    ) -> Path:
        """合并所有分片为完整文件"""
        file_hash = self._get_file_hash(filename, file_size)
        chunk_dir = self._get_chunk_dir(file_hash)

        # 生成目标文件路径
        target_path = self.upload_dir / target_filename

        # 合并分片
        async with aiofiles.open(target_path, "wb") as target_file:
            for i in range(total_chunks):
                chunk_path = self._get_chunk_path(file_hash, i)
                if not chunk_path.exists():
                    raise FileNotFoundError(f"分片 {i} 不存在")

                async with aiofiles.open(chunk_path, "rb") as chunk_file:
                    chunk_data = await chunk_file.read()
                    await target_file.write(chunk_data)

        # 清理分片目录
        shutil.rmtree(chunk_dir)

        return target_path

    async def cleanup_chunks(self, filename: str, file_size: int) -> None:
        """清理分片文件"""
        file_hash = self._get_file_hash(filename, file_size)
        chunk_dir = self._get_chunk_dir(file_hash)

        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)

    def validate_file_extension(self, filename: str) -> bool:
        """验证文件扩展名"""
        ext = Path(filename).suffix.lower()
        return ext in settings.allowed_extensions

    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小"""
        return file_size <= settings.max_file_size

    def generate_unique_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        import uuid
        ext = Path(original_filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return unique_name

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        path = Path(file_path)
        if path.exists():
            await aiofiles.os.remove(path)
            return True
        return False

    async def get_upload_progress(
        self,
        filename: str,
        file_size: int,
        total_chunks: int
    ) -> Dict:
        """获取上传进度"""
        uploaded_chunks = await self.get_uploaded_chunks(filename, file_size)
        progress = len(uploaded_chunks) / total_chunks * 100 if total_chunks > 0 else 0

        return {
            "filename": filename,
            "uploaded_chunks": uploaded_chunks,
            "total_chunks": total_chunks,
            "progress": progress
        }


# 创建服务实例
upload_service = UploadService()
