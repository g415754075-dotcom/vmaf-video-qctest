# 使用 Ubuntu 24.04，其 FFmpeg 7.x 已包含 libvmaf
FROM ubuntu:24.04

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装 Python 和 FFmpeg（Ubuntu 24.04 的 FFmpeg 7.0 包含 libvmaf）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 验证 FFmpeg 和 libvmaf 可用（严格检查）
RUN ffmpeg -version && \
    ffmpeg -filters 2>&1 | grep -q libvmaf || \
    (echo "ERROR: FFmpeg does not have libvmaf support" && exit 1)

# 下载 VMAF 模型文件
RUN mkdir -p /usr/local/share/model && \
    curl -L -o /usr/local/share/model/vmaf_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_v0.6.1.json && \
    curl -L -o /usr/local/share/model/vmaf_4k_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_4k_v0.6.1.json

# 设置工作目录
WORKDIR /app

# 先复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry 并安装依赖（使用 --break-system-packages 因为 Ubuntu 24.04 默认限制）
RUN pip3 install --no-cache-dir --break-system-packages poetry && \
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
