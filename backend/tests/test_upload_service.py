"""上传服务单元测试"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.upload_service import UploadService


class TestUploadService:
    """上传服务测试类"""

    @pytest.fixture
    def upload_service(self, temp_upload_dir: Path) -> UploadService:
        """创建带临时目录的上传服务实例"""
        service = UploadService()
        service.upload_dir = temp_upload_dir
        service.chunk_dir = temp_upload_dir / "chunks"
        service.chunk_dir.mkdir(parents=True, exist_ok=True)
        return service

    def test_get_file_hash_一致性(self, upload_service: UploadService):
        """测试相同文件名和大小生成相同哈希"""
        hash1 = upload_service._get_file_hash("test.mp4", 1024)
        hash2 = upload_service._get_file_hash("test.mp4", 1024)
        assert hash1 == hash2

    def test_get_file_hash_不同文件(self, upload_service: UploadService):
        """测试不同文件生成不同哈希"""
        hash1 = upload_service._get_file_hash("test1.mp4", 1024)
        hash2 = upload_service._get_file_hash("test2.mp4", 1024)
        assert hash1 != hash2

    def test_get_file_hash_不同大小(self, upload_service: UploadService):
        """测试相同文件名不同大小生成不同哈希"""
        hash1 = upload_service._get_file_hash("test.mp4", 1024)
        hash2 = upload_service._get_file_hash("test.mp4", 2048)
        assert hash1 != hash2

    def test_validate_file_extension_有效格式(self, upload_service: UploadService):
        """测试有效视频格式验证"""
        valid_extensions = [".mp4", ".mkv", ".mov", ".avi", ".webm", ".y4m"]
        for ext in valid_extensions:
            assert upload_service.validate_file_extension(f"video{ext}") is True

    def test_validate_file_extension_无效格式(self, upload_service: UploadService):
        """测试无效视频格式验证"""
        invalid_extensions = [".txt", ".jpg", ".pdf", ".exe", ".zip"]
        for ext in invalid_extensions:
            assert upload_service.validate_file_extension(f"file{ext}") is False

    def test_validate_file_extension_大小写不敏感(self, upload_service: UploadService):
        """测试扩展名大小写不敏感"""
        assert upload_service.validate_file_extension("video.MP4") is True
        assert upload_service.validate_file_extension("video.Mp4") is True

    def test_validate_file_size_有效大小(self, upload_service: UploadService):
        """测试有效文件大小验证"""
        # 4GB 以下应该有效
        assert upload_service.validate_file_size(1024) is True
        assert upload_service.validate_file_size(1024 * 1024 * 1024) is True  # 1GB
        assert upload_service.validate_file_size(4 * 1024 * 1024 * 1024) is True  # 4GB

    def test_validate_file_size_超出限制(self, upload_service: UploadService):
        """测试超出限制的文件大小验证"""
        # 超过 4GB 应该失败
        assert upload_service.validate_file_size(5 * 1024 * 1024 * 1024) is False

    def test_generate_unique_filename_保留扩展名(self, upload_service: UploadService):
        """测试生成唯一文件名时保留原扩展名"""
        unique_name = upload_service.generate_unique_filename("original.mp4")
        assert unique_name.endswith(".mp4")

    def test_generate_unique_filename_唯一性(self, upload_service: UploadService):
        """测试生成的文件名唯一"""
        names = set()
        for _ in range(100):
            name = upload_service.generate_unique_filename("test.mp4")
            names.add(name)
        assert len(names) == 100

    @pytest.mark.asyncio
    async def test_save_chunk_保存分片(
        self, upload_service: UploadService, sample_chunk_data: bytes
    ):
        """测试保存分片"""
        result = await upload_service.save_chunk(
            filename="test.mp4",
            file_size=10000,
            chunk_index=0,
            chunk_data=sample_chunk_data
        )
        assert result is True

        # 验证分片文件存在
        file_hash = upload_service._get_file_hash("test.mp4", 10000)
        chunk_path = upload_service._get_chunk_path(file_hash, 0)
        assert chunk_path.exists()

    @pytest.mark.asyncio
    async def test_get_uploaded_chunks_返回已上传分片(
        self, upload_service: UploadService, sample_chunk_data: bytes
    ):
        """测试获取已上传分片列表"""
        # 保存多个分片
        await upload_service.save_chunk("test.mp4", 10000, 0, sample_chunk_data)
        await upload_service.save_chunk("test.mp4", 10000, 2, sample_chunk_data)
        await upload_service.save_chunk("test.mp4", 10000, 5, sample_chunk_data)

        # 获取已上传分片
        uploaded = await upload_service.get_uploaded_chunks("test.mp4", 10000)

        assert uploaded == [0, 2, 5]

    @pytest.mark.asyncio
    async def test_get_uploaded_chunks_空列表(self, upload_service: UploadService):
        """测试无分片时返回空列表"""
        uploaded = await upload_service.get_uploaded_chunks("nonexistent.mp4", 1000)
        assert uploaded == []

    @pytest.mark.asyncio
    async def test_merge_chunks_合并分片(
        self, upload_service: UploadService
    ):
        """测试合并分片为完整文件"""
        # 准备分片数据
        chunk1 = b"part1"
        chunk2 = b"part2"
        chunk3 = b"part3"

        await upload_service.save_chunk("test.mp4", 15, 0, chunk1)
        await upload_service.save_chunk("test.mp4", 15, 1, chunk2)
        await upload_service.save_chunk("test.mp4", 15, 2, chunk3)

        # 合并分片
        target_path = await upload_service.merge_chunks(
            filename="test.mp4",
            file_size=15,
            total_chunks=3,
            target_filename="merged.mp4"
        )

        # 验证合并结果
        assert target_path.exists()
        with open(target_path, "rb") as f:
            content = f.read()
        assert content == b"part1part2part3"

    @pytest.mark.asyncio
    async def test_merge_chunks_缺少分片时抛出异常(
        self, upload_service: UploadService, sample_chunk_data: bytes
    ):
        """测试缺少分片时合并应失败"""
        # 只保存部分分片
        await upload_service.save_chunk("test.mp4", 10000, 0, sample_chunk_data)
        await upload_service.save_chunk("test.mp4", 10000, 2, sample_chunk_data)

        # 尝试合并应失败（缺少分片 1）
        with pytest.raises(FileNotFoundError):
            await upload_service.merge_chunks(
                filename="test.mp4",
                file_size=10000,
                total_chunks=3,
                target_filename="merged.mp4"
            )

    @pytest.mark.asyncio
    async def test_cleanup_chunks_清理分片(
        self, upload_service: UploadService, sample_chunk_data: bytes
    ):
        """测试清理分片文件"""
        # 保存分片
        await upload_service.save_chunk("test.mp4", 10000, 0, sample_chunk_data)

        file_hash = upload_service._get_file_hash("test.mp4", 10000)
        chunk_dir = upload_service._get_chunk_dir(file_hash)
        assert chunk_dir.exists()

        # 清理分片
        await upload_service.cleanup_chunks("test.mp4", 10000)

        # 验证分片目录已删除
        assert not chunk_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_file_删除存在的文件(self, upload_service: UploadService):
        """测试删除存在的文件"""
        # 创建临时文件
        temp_file = upload_service.upload_dir / "temp_test.txt"
        temp_file.write_text("test content")

        assert temp_file.exists()

        # 删除文件
        result = await upload_service.delete_file(str(temp_file))

        assert result is True
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_delete_file_删除不存在的文件(self, upload_service: UploadService):
        """测试删除不存在的文件"""
        result = await upload_service.delete_file("/nonexistent/file.mp4")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_upload_progress_计算进度(
        self, upload_service: UploadService, sample_chunk_data: bytes
    ):
        """测试获取上传进度"""
        # 保存部分分片
        await upload_service.save_chunk("test.mp4", 10000, 0, sample_chunk_data)
        await upload_service.save_chunk("test.mp4", 10000, 1, sample_chunk_data)

        # 获取进度（总共 4 个分片，已上传 2 个）
        progress = await upload_service.get_upload_progress("test.mp4", 10000, 4)

        assert progress["filename"] == "test.mp4"
        assert progress["uploaded_chunks"] == [0, 1]
        assert progress["total_chunks"] == 4
        assert progress["progress"] == 50.0
