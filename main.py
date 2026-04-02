import os
from dotenv import load_dotenv
load_dotenv() # Load env BEFORE importing routers that use os.getenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, dashboard, lab, chat, student, ai
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from migrate_db import migrate

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)
# Run migrations for existing tables
migrate()

app = FastAPI(title="Graduation Project API (PostgreSQL)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["*"],
)

# Debug Traffic Monitor Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"--> [TRAFFIC] {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"<-- [TRAFFIC] {request.method} {request.url.path} STATUS: {response.status_code}")
    return response

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(lab.router, prefix="/lab", tags=["Lab"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(student.router, prefix="/student", tags=["Student"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])
# Mount static files to serve uploaded lab and student reports
os.makedirs("static/lab_reports", exist_ok=True)
os.makedirs("static/student_reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "✅ PostgreSQL API is running!", "database": "Connected"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Global Exception Handler for debugging
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL ERROR: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "traceback": "Check logs for full trace",
            "path": request.url.path
        }
    )
