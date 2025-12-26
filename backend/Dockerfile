# 使用更轻量的基础镜像
FROM python:3.11-slim-bookworm

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（使用 Debian bookworm 的 FFmpeg，已包含 libvmaf）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 验证 FFmpeg 和 libvmaf 可用
RUN ffmpeg -version && ffmpeg -filters 2>&1 | grep -q libvmaf && echo "libvmaf available"

# 设置工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry 并安装依赖（不创建虚拟环境，直接安装到系统）
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads reports

# 设置 VMAF 模型路径（使用系统自带的模型）
ENV VMAF_MODEL_PATH=/usr/share/libvmaf/model/vmaf_v0.6.1.json
ENV VMAF_4K_MODEL_PATH=/usr/share/libvmaf/model/vmaf_4k_v0.6.1.json

# 如果系统模型不存在，下载它们
RUN if [ ! -f "$VMAF_MODEL_PATH" ]; then \
    mkdir -p /usr/share/libvmaf/model && \
    curl -L -o /usr/share/libvmaf/model/vmaf_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_v0.6.1.json && \
    curl -L -o /usr/share/libvmaf/model/vmaf_4k_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_4k_v0.6.1.json; \
    fi

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令 - 使用 PORT 环境变量（Render 会自动设置）
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
