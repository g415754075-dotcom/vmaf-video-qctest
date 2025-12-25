"""质量评估服务 - 异步任务管理"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import statistics

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.video import Video, Assessment, TaskStatus
from app.services.ffmpeg_service import ffmpeg_service, QualityResult


class AssessmentService:
    """质量评估服务类"""

    def __init__(self):
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.max_concurrent = settings.max_concurrent_tasks

    async def create_assessment(
        self,
        session: AsyncSession,
        reference_video_id: int,
        distorted_video_id: int
    ) -> Assessment:
        """创建评估任务"""
        # 获取视频信息
        ref_video = await session.get(Video, reference_video_id)
        dist_video = await session.get(Video, distorted_video_id)

        if not ref_video or not dist_video:
            raise ValueError("视频不存在")

        # 创建评估任务
        assessment = Assessment(
            reference_video_id=reference_video_id,
            distorted_video_id=distorted_video_id,
            status=TaskStatus.PENDING,
            total_frames=ref_video.frame_count or 0
        )

        session.add(assessment)
        await session.commit()
        await session.refresh(assessment)

        return assessment

    async def start_assessment(
        self,
        session: AsyncSession,
        assessment_id: int
    ) -> None:
        """启动评估任务"""
        # 检查并发数
        running_count = len([t for t in self.running_tasks.values() if not t.done()])
        if running_count >= self.max_concurrent:
            raise RuntimeError(f"已达到最大并发任务数 ({self.max_concurrent})")

        # 获取评估任务
        assessment = await session.get(
            Assessment,
            assessment_id,
            options=[selectinload(Assessment.reference_video),
                     selectinload(Assessment.distorted_video)]
        )

        if not assessment:
            raise ValueError("评估任务不存在")

        if assessment.status == TaskStatus.RUNNING:
            raise RuntimeError("任务已在运行中")

        # 更新状态
        assessment.status = TaskStatus.RUNNING
        assessment.started_at = datetime.utcnow()
        await session.commit()

        # 创建异步任务
        task = asyncio.create_task(
            self._run_assessment(assessment_id)
        )
        self.running_tasks[assessment_id] = task

    async def cancel_assessment(
        self,
        session: AsyncSession,
        assessment_id: int
    ) -> bool:
        """取消评估任务"""
        assessment = await session.get(Assessment, assessment_id)

        if not assessment:
            raise ValueError("评估任务不存在")

        if assessment.status != TaskStatus.RUNNING:
            raise RuntimeError("只能取消运行中的任务")

        # 取消异步任务
        if assessment_id in self.running_tasks:
            self.running_tasks[assessment_id].cancel()
            del self.running_tasks[assessment_id]

        # 更新状态
        assessment.status = TaskStatus.CANCELLED
        await session.commit()

        return True

    async def get_assessment(
        self,
        session: AsyncSession,
        assessment_id: int
    ) -> Optional[Assessment]:
        """获取评估任务详情"""
        return await session.get(
            Assessment,
            assessment_id,
            options=[selectinload(Assessment.reference_video),
                     selectinload(Assessment.distorted_video)]
        )

    async def list_assessments(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Assessment], int]:
        """获取评估任务列表"""
        # 查询总数
        count_query = select(Assessment)
        result = await session.execute(count_query)
        total = len(result.scalars().all())

        # 查询列表
        query = (
            select(Assessment)
            .options(
                selectinload(Assessment.reference_video),
                selectinload(Assessment.distorted_video)
            )
            .order_by(Assessment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    async def get_frame_data(
        self,
        session: AsyncSession,
        assessment_id: int
    ) -> Optional[List[Dict]]:
        """获取逐帧质量数据"""
        assessment = await session.get(Assessment, assessment_id)

        if not assessment or not assessment.frame_data_path:
            return None

        frame_data_path = Path(assessment.frame_data_path)
        if not frame_data_path.exists():
            return None

        with open(frame_data_path, "r") as f:
            return json.load(f)

    async def get_statistics(
        self,
        session: AsyncSession,
        assessment_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取质量统计数据"""
        frame_data = await self.get_frame_data(session, assessment_id)

        if not frame_data:
            return None

        def calc_stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {}
            sorted_values = sorted(values)
            n = len(sorted_values)
            return {
                "mean": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if n > 1 else 0,
                "p5": sorted_values[int(n * 0.05)] if n > 0 else 0,
                "p95": sorted_values[int(n * 0.95)] if n > 0 else 0,
            }

        vmaf_values = [f["vmaf"] for f in frame_data if f.get("vmaf") is not None]
        ssim_values = [f["ssim"] for f in frame_data if f.get("ssim") is not None]
        psnr_values = [f["psnr"] for f in frame_data if f.get("psnr") is not None]

        return {
            "assessment_id": assessment_id,
            "vmaf": calc_stats(vmaf_values) if vmaf_values else None,
            "ssim": calc_stats(ssim_values) if ssim_values else None,
            "psnr": calc_stats(psnr_values) if psnr_values else None,
        }

    async def get_problem_frames(
        self,
        session: AsyncSession,
        assessment_id: int,
        threshold: float = 70,
        limit: int = 10
    ) -> List[Dict]:
        """获取质量较差的帧"""
        frame_data = await self.get_frame_data(session, assessment_id)

        if not frame_data:
            return []

        # 筛选 VMAF 低于阈值的帧
        problem_frames = [
            f for f in frame_data
            if f.get("vmaf") is not None and f["vmaf"] < threshold
        ]

        # 按 VMAF 分数排序
        problem_frames.sort(key=lambda x: x.get("vmaf", 0))

        return problem_frames[:limit]

    # ============ 批量评估相关方法 ============

    async def create_batch_assessment(
        self,
        session: AsyncSession,
        reference_video_id: int,
        distorted_video_ids: List[int]
    ) -> tuple[str, List[Assessment]]:
        """创建批量评估任务

        Args:
            session: 数据库会话
            reference_video_id: 参考视频 ID
            distorted_video_ids: 待测视频 ID 列表

        Returns:
            (batch_id, assessments): 批次 ID 和评估任务列表
        """
        # 验证参考视频存在
        ref_video = await session.get(Video, reference_video_id)
        if not ref_video:
            raise ValueError("参考视频不存在")

        # 验证所有待测视频存在
        for dist_id in distorted_video_ids:
            dist_video = await session.get(Video, dist_id)
            if not dist_video:
                raise ValueError(f"待测视频 ID={dist_id} 不存在")

        # 生成批次 ID
        batch_id = str(uuid.uuid4())

        # 创建评估任务
        assessments = []
        for dist_id in distorted_video_ids:
            assessment = Assessment(
                batch_id=batch_id,
                reference_video_id=reference_video_id,
                distorted_video_id=dist_id,
                status=TaskStatus.PENDING,
                total_frames=ref_video.frame_count or 0
            )
            session.add(assessment)
            assessments.append(assessment)

        await session.commit()

        # 刷新所有评估任务以获取 ID
        for assessment in assessments:
            await session.refresh(assessment)

        return batch_id, assessments

    async def start_batch_assessment(
        self,
        session: AsyncSession,
        batch_id: str
    ) -> None:
        """启动批量评估（顺序执行）

        批量评估中的任务按顺序依次执行，完成一个后自动启动下一个
        """
        # 获取批次中的第一个待处理任务
        query = (
            select(Assessment)
            .where(Assessment.batch_id == batch_id)
            .where(Assessment.status == TaskStatus.PENDING)
            .order_by(Assessment.id)
            .limit(1)
        )
        result = await session.execute(query)
        first_pending = result.scalar_one_or_none()

        if first_pending:
            await self.start_assessment(session, first_pending.id)

    async def _run_assessment(self, assessment_id: int) -> None:
        """执行评估任务（内部方法）- 支持批量模式"""
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            batch_id = None
            try:
                assessment = await session.get(
                    Assessment,
                    assessment_id,
                    options=[selectinload(Assessment.reference_video),
                             selectinload(Assessment.distorted_video)]
                )

                if not assessment:
                    return

                batch_id = assessment.batch_id

                # 准备输出路径
                output_dir = settings.reports_dir / f"assessment_{assessment_id}"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_json = output_dir / "vmaf_output.json"
                frame_data_path = output_dir / "frame_data.json"

                # 执行评估
                async for update in ffmpeg_service.assess_quality(
                    assessment.reference_video.file_path,
                    assessment.distorted_video.file_path,
                    str(output_json)
                ):
                    if update["type"] == "progress":
                        assessment.current_frame = update["current_frame"]
                        assessment.progress = update["progress"]
                        await session.commit()

                    elif update["type"] == "complete":
                        result: QualityResult = update["result"]

                        # 保存逐帧数据
                        with open(frame_data_path, "w") as f:
                            json.dump(result.frame_data, f)

                        # 更新评估结果
                        assessment.vmaf_score = result.vmaf_score
                        assessment.vmaf_min = result.vmaf_min
                        assessment.vmaf_max = result.vmaf_max
                        assessment.ssim_score = result.ssim_score
                        assessment.psnr_score = result.psnr_score
                        assessment.ms_ssim_score = result.ms_ssim_score
                        assessment.frame_data_path = str(frame_data_path)
                        assessment.status = TaskStatus.COMPLETED
                        assessment.progress = 100
                        assessment.completed_at = datetime.utcnow()

                        await session.commit()

            except Exception as e:
                # 获取 assessment 以更新状态
                assessment = await session.get(Assessment, assessment_id)
                if assessment:
                    assessment.status = TaskStatus.FAILED
                    assessment.error_message = str(e)
                    await session.commit()

            finally:
                # 清理运行中任务记录
                if assessment_id in self.running_tasks:
                    del self.running_tasks[assessment_id]

                # 如果是批量任务，触发下一个任务
                if batch_id:
                    await self._trigger_next_batch_task(batch_id)

    async def _trigger_next_batch_task(self, batch_id: str) -> None:
        """触发批量评估中的下一个任务"""
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            # 查找下一个待处理任务
            query = (
                select(Assessment)
                .where(Assessment.batch_id == batch_id)
                .where(Assessment.status == TaskStatus.PENDING)
                .order_by(Assessment.id)
                .limit(1)
            )
            result = await session.execute(query)
            next_task = result.scalar_one_or_none()

            if next_task:
                await self.start_assessment(session, next_task.id)

    async def get_batch_status(
        self,
        session: AsyncSession,
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取批量评估状态

        Returns:
            包含批量评估状态的字典，若 batch_id 不存在则返回 None
        """
        # 查询批次中的所有评估任务
        query = (
            select(Assessment)
            .where(Assessment.batch_id == batch_id)
            .options(
                selectinload(Assessment.reference_video),
                selectinload(Assessment.distorted_video)
            )
            .order_by(Assessment.id)
        )
        result = await session.execute(query)
        assessments = result.scalars().all()

        if not assessments:
            return None

        # 获取参考视频（所有任务共用同一个）
        reference_video = assessments[0].reference_video

        # 计算统计数据
        total_count = len(assessments)
        completed_count = sum(1 for a in assessments if a.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for a in assessments if a.status == TaskStatus.FAILED)

        # 计算整体进度
        # 公式：(已完成数/总数)*100 + (当前任务进度/总数)
        running_task = next((a for a in assessments if a.status == TaskStatus.RUNNING), None)
        running_progress = running_task.progress if running_task else 0

        overall_progress = (completed_count / total_count) * 100 + (running_progress / total_count)

        return {
            "batch_id": batch_id,
            "reference_video": reference_video,
            "assessments": list(assessments),
            "total_count": total_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "progress": round(overall_progress, 2)
        }

    async def list_batches(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取批量评估列表"""
        # 获取所有不重复的 batch_id
        query = (
            select(Assessment.batch_id)
            .where(Assessment.batch_id.isnot(None))
            .distinct()
            .order_by(Assessment.batch_id)
        )
        result = await session.execute(query)
        batch_ids = [row[0] for row in result.all()]

        total = len(batch_ids)
        batch_ids = batch_ids[skip:skip + limit]

        # 获取每个批次的状态
        batches = []
        for batch_id in batch_ids:
            batch_status = await self.get_batch_status(session, batch_id)
            if batch_status:
                batches.append(batch_status)

        return batches, total


# 创建服务实例
assessment_service = AssessmentService()
