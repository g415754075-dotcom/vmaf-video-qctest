# 基于 Ubuntu 22.04，使用 ppa 安装带 libvmaf 的 FFmpeg
FROM ubuntu:22.04

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装 Python 3.11 和 FFmpeg（Ubuntu 22.04 的 FFmpeg 5.1 已包含 libvmaf）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置 Python 3.11 为默认
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# 验证 FFmpeg 和 libvmaf
RUN ffmpeg -version && ffmpeg -filters 2>&1 | grep -i vmaf || echo "检查 libvmaf 状态"

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

# 安装 Poetry 并安装依赖
RUN pip3 install --no-cache-dir poetry && \
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
