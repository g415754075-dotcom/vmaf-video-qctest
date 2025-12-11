"""VMAF Video QC Test - 主应用入口"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api import upload, videos, assessments, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print(f"✓ 数据库初始化完成")
    print(f"✓ 上传目录: {settings.upload_dir.absolute()}")
    print(f"✓ 报告目录: {settings.reports_dir.absolute()}")

    yield

    # 关闭时清理资源
    print("应用关闭")


# 创建应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="视频质量评估工具 - 使用 VMAF/SSIM/PSNR 评估视频编解码质量",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（上传的视频和缩略图）
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")
app.mount("/reports", StaticFiles(directory=str(settings.reports_dir)), name="reports")

# 注册路由
app.include_router(upload.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


@app.get("/api/config")
async def get_config():
    """获取前端配置"""
    return {
        "max_file_size": settings.max_file_size,
        "allowed_extensions": settings.allowed_extensions,
        "chunk_size": settings.chunk_size,
        "max_concurrent_tasks": settings.max_concurrent_tasks
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
