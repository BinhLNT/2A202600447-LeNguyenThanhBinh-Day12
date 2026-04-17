"""
ADVANCED — Stateless Agent với Redis Session

Stateless = agent không giữ state trong memory.
Mọi state (session, conversation history) lưu trong Redis.

Tại sao stateless quan trọng khi scale?
  Instance 1: User A gửi request 1 → lưu session trong memory
  Instance 2: User A gửi request 2 → KHÔNG có session! Bug!

  ✅ Giải pháp: Lưu session trong Redis
  Bất kỳ instance nào cũng đọc được session của user.

Demo:
  docker compose up
  # Sau đó test multi-turn conversation
  python test_stateless.py
"""
import os
import time
import json
import logging
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from utils.mock_llm import ask

# ── Redis (optional — fallback to in-memory dict nếu không có Redis)
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    r.ping()
    USE_REDIS = True
    print("✅ Connected to Redis")
except Exception:
    USE_REDIS = False
    _memory_store: dict = {}
    print("⚠️  Redis not available — using in-memory store (not scalable!)")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = os.getenv("INSTANCE_ID", f"instance-{uuid.uuid4().hex[:6]}")


# ──────────────────────────────────────────────────────────
# Session Storage (Redis-backed, Stateless-compatible)
# ──────────────────────────────────────────────────────────

def save_session(session_id: str, data: dict, ttl_seconds: int = 3600):
    """Lưu session vào Redis với TTL."""
    serialized = json.dumps(data)
    if USE_REDIS:
        r.setex(f"session:{session_id}", ttl_seconds, serialized)
    else:
        _memory_store[f"session:{session_id}"] = data


def load_session(session_id: str) -> dict:
    """Load session từ Redis."""
    if USE_REDIS:
        data = r.get(f"session:{session_id}")
        return json.loads(data) if data else {}
    return _memory_store.get(f"session:{session_id}", {})


def append_to_history(session_id: str, role: str, content: str):
    """Thêm message vào conversation history."""
    session = load_session(session_id)
    history = session.get("history", [])
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Giữ tối đa 20 messages (10 turns)
    if len(history) > 20:
        history = history[-20:]
    session["history"] = history
    save_session(session_id, session)
    return history


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting instance {INSTANCE_ID}")
    logger.info(f"Storage: {'Redis ✅' if USE_REDIS else 'In-memory ⚠️'}")
    yield
    logger.info(f"Instance {INSTANCE_ID} shutting down")


app = FastAPI(
    title="Stateless Agent",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None  # None = tạo session mới


# ──────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(body: ChatRequest):
    """
    Exercise 5.3: Stateless Agent
    Toàn bộ lịch sử được đẩy ra Redis, Agent không giữ bất kỳ dữ liệu nào trong RAM.
    """
    # 1. Định danh phiên làm việc (State ID)
    session_id = body.session_id or str(uuid.uuid4())

    # --- BƯỚC QUAN TRỌNG: STATELESS LOGIC ---
    
    # 2. Lấy lịch sử cũ làm ngữ cảnh (Context)
    # Thay vì load cả object session, ta chỉ lấy list history trực tiếp từ Redis
    history = load_session(session_id).get("history", [])

    # 3. Gọi LLM xử lý (Dựa trên câu hỏi và lịch sử nếu cần)
    # Bình có thể truyền 'history' vào hàm ask nếu mock_llm hỗ trợ context
    answer = ask(body.question)

    # 4. Cập nhật State mới (Stateless Write)
    # Sử dụng hàm append_to_history mà chúng ta đã cấu hình dùng Redis rpush
    append_to_history(session_id, "user", body.question)
    append_to_history(session_id, "assistant", answer)

    # 5. Trả về kết quả kèm ID của Instance đang xử lý
    return {
        "session_id": session_id,
        "question": body.question,
        "answer": answer,
        "turn": (len(history) // 2) + 1, 
        "served_by": INSTANCE_ID,  # Chứng minh Load Balancing ở bài 5.4
        "stateless_status": "✅ Đã lưu vào Redis" if USE_REDIS else "⚠️ Lưu tạm trong RAM",
    }


@app.get("/chat/{session_id}/history")
def get_history(session_id: str):
    """Xem conversation history của một session."""
    session = load_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found or expired")
    return {
        "session_id": session_id,
        "messages": session.get("history", []),
        "count": len(session.get("history", [])),
    }


@app.delete("/chat/{session_id}")
def delete_session(session_id: str):
    """Xóa session (user logout)."""
    if USE_REDIS:
        r.delete(f"session:{session_id}")
    else:
        _memory_store.pop(f"session:{session_id}", None)
    return {"deleted": session_id}


# ──────────────────────────────────────────────────────────
# Health / Metrics
# ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    redis_ok = False
    if USE_REDIS:
        try:
            r.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    status = "ok" if (not USE_REDIS or redis_ok) else "degraded"

    return {
        "status": status,
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "storage": "redis" if USE_REDIS else "in-memory",
        "redis_connected": redis_ok if USE_REDIS else "N/A",
    }


@app.get("/ready")
def ready():
    if USE_REDIS:
        try:
            r.ping()
        except Exception:
            raise HTTPException(503, "Redis not available")
    return {"ready": True, "instance": INSTANCE_ID}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
