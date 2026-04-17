FROM python:3.11-slim
WORKDIR /app
# Cài đặt thư viện trực tiếp để tránh lỗi thiếu file requirements
RUN pip install --no-cache-dir fastapi uvicorn redis pydantic
COPY . .
# Chạy thẳng uvicorn để tránh lỗi nạp ứng dụng
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
