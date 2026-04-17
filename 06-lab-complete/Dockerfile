# ============================================================
# Production Dockerfile — Multi-stage, < 500 MB, non-root
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Tạo user agent và home directory (Thêm -m để tạo /home/agent)
RUN groupadd -r agent && useradd -r -g agent -m -d /home/agent agent

WORKDIR /app

# CHỈNH SỬA QUAN TRỌNG: Copy packages từ thư mục .local của root (builder) 
# sang thư mục .local của agent (runtime)
COPY --from=builder /root/.local /home/agent/.local

# Copy application
COPY app/ ./app/
COPY utils/ ./utils/

# Cấp quyền cho cả thư mục app và thư mục chứa thư viện .local
RUN chown -R agent:agent /app /home/agent/.local

USER agent

# Các biến môi trường giữ nguyên như file của bạn
ENV PATH=/home/agent/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Sử dụng /bin/sh để chắc chắn $PORT được chuyển thành con số thực tế
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
