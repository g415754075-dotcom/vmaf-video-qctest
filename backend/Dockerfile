# 多阶段构建：从静态 FFmpeg 镜像复制二进制文件
FROM mwader/static-ffmpeg:7.1 AS ffmpeg

# 使用 Python 3.11 slim 作为运行时基础
FROM python:3.11-slim-bookworm

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 从 ffmpeg 镜像复制静态编译的 ffmpeg 和 ffprobe
COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffprobe /usr/local/bin/ffprobe

# 安装必要的系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# 安装 Python 依赖
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

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
