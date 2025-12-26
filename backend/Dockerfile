# 使用 linuxserver/ffmpeg 作为基础，它预编译了完整的 FFmpeg（包含 libvmaf）
FROM linuxserver/ffmpeg:latest

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装 Python 3 和 pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 验证 FFmpeg 和 libvmaf 可用
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

# 创建虚拟环境并安装依赖（避免系统 Python 限制）
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
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

# 启动命令（使用虚拟环境中的 uvicorn）
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
