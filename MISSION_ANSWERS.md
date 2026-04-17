#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Lê Nguyễn Thanh Bình  
> **Student ID:** 2A202600447  
> **Date:** 17/04/2026


### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:


# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded Secrets: Các thông tin nhạy cảm như OPENAI_API_KEY và DATABASE_URL được viết trực tiếp vào mã nguồn, dễ dẫn đến rò rỉ khi đẩy lên GitHub.
2. Thiếu Health Check Endpoint: Không có các endpoint như /health hay /ready, khiến hệ thống quản lý cloud không thể biết trạng thái của ứng dụng để tự động khởi động lại khi gặp sự cố.
3. Sử dụng `print()` thay vì Logging: Việc dùng `print()` không cho phép phân loại mức độ lỗi (INFO, ERROR, DEBUG) và có thể vô tình log ra cả các thông tin nhạy cảm (secrets).
4. Cấu hình Port cố định: Port được đặt cứng là `8000` thay vì đọc từ biến môi trường, điều này gây lỗi trên các nền tảng như Railway hay Render vốn tự động cấp phát Port qua biến `PORT`.
5. Host Binding hạn chế: Thiết lập `host="localhost"` chỉ cho phép truy cập nội bộ từ chính máy đó, khiến ứng dụng không thể nhận kết nối từ bên ngoài khi chạy trong Docker hay Cloud.
6. Chế độ Debug luôn bật: `reload=True` chỉ nên dùng khi phát triển, nếu để ở môi trường production sẽ làm giảm hiệu năng và gây rủi ro bảo mật.
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | Hardcode trực tiếp trong code.     | Đọc tập trung từ biến môi trường thông qua file `config.py` và `.env`.        | Giúp tách biệt mã nguồn và cấu hình, dễ dàng thay đổi thông số mà không cần sửa code và tránh lộ mật khẩu.            |
| Health check  | Không có endpoint kiểm tra trạng thái.     | Cung cấp endpoint /health (Liveness) và /ready (Readiness).  | Giúp các nền tảng Cloud và Load Balancer biết khi nào cần restart container hoặc khi nào ứng dụng đã sẵn sàng nhận traffic. |
| Logging  | Sử dụng lệnh `print()` cơ bản.     | Sử dụng Structured JSON logging.  | Giúp các hệ thống quản lý log tập trung dễ dàng thu thập, tìm kiếm và phân tích lỗi một cách chuyên nghiệp. |
| Shutdown  | Tắt ứng dụng đột ngột bằng lệnh Ctrl+C hoặc tắt process.     | Xử lý tín hiệu SIGTERM để Graceful Shutdown.  | Đảm bảo các yêu cầu đang xử lý dở dang được hoàn tất và các kết nối database được đóng an toàn trước khi dừng hẳn. |
...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: Bản Develop: python:3.11 & Bản Production: python:3.11-slim 
2. Working directory: /app
...

### Exercise 2.3: Image size comparison
- Develop: [1.66] MB
- Production: [236] MB
- Difference: [~85.8]%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://binh-ai-agent-lab12-production.up.railway.app
- Screenshot: ![alt text](image.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- 4.1: ![alt text](image-1.png)
- 4.1: ![alt text](image-2.png)
- 4.2: ![alt text](image-3.png)
- 4.2: ![alt text](image-4.png)
- 4.3: ![alt text](image-5.png)

### Exercise 4.4: Cost guard implementation
```
def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Logic:
    1. Mỗi user có hạn mức chi tiêu cố định (ví dụ $10).
    2. Sử dụng Redis để lưu trữ số tiền đã dùng: key = f"usage:{user_id}".
    """
    # Lấy số tiền đã tiêu từ Redis
    current_spent = float(redis_client.get(f"usage:{user_id}") or 0)
    
    # Kiểm tra nếu vượt quá hạn mức $10
    if current_spent + estimated_cost > 10.0:
        return False  # Chặn yêu cầu (trả về 402 hoặc 403)
        
    # Nếu hợp lệ, cập nhật số tiền mới vào Redis
    redis_client.set(f"usage:{user_id}", current_spent + estimated_cost)
    return True
```


## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]

- ![alt text](image-6.png)
- ![alt text](image-7.png)
- ![alt text](image-8.png)
- ![alt text](image-9.png)
- ![alt text](image-10.png)

- 5.1: Mục tiêu: Giúp hệ thống tự động kiểm tra sức khỏe của Agent.
- 5.2: Mục tiêu: Tắt ứng dụng một cách "lịch sự", không gây mất dữ liệu đột ngột.
- 5.3: Mục tiêu: Biến Agent thành thực thể "không trí nhớ" để có thể mở rộng hàng ngang.
- 5.4: Mục tiêu: Phân phối tải trọng và tăng tính sẵn sàng (High Availability).
- 5.5: Mục tiêu: Kiểm chứng thực tế kiến trúc đã thiết kế.