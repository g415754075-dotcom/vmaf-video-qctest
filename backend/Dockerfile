# 阶段1：使用预编译的 FFmpeg 镜像获取二进制文件
FROM jrottenberg/ffmpeg:5.1-alpine AS ffmpeg

# 阶段2：Python 运行环境
FROM python:3.11-slim-bookworm

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 从 FFmpeg 镜像复制二进制文件和库
COPY --from=ffmpeg /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg /usr/local/lib /usr/local/lib

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置库路径
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 验证 FFmpeg 和 libvmaf 可用
RUN ffmpeg -version && ffmpeg -filters 2>&1 | grep libvmaf

# 下载 VMAF 模型文件
RUN mkdir -p /usr/local/share/model && \
    curl -L -o /usr/local/share/model/vmaf_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_v0.6.1.json && \
    curl -L -o /usr/local/share/model/vmaf_4k_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_4k_v0.6.1.json

# 设置工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry 并安装依赖
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads reports

# 设置 VMAF 模型路径
ENV VMAF_MODEL_PATH=/usr/local/share/model/vmaf_v0.6.1.json
ENV VMAF_4K_MODEL_PATH=/usr/local/share/model/vmaf_4k_v0.6.1.json

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
