from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, dashboard, lab
from fastapi.staticfiles import StaticFiles
import os
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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(lab.router, prefix="/lab", tags=["Lab"])

# Mount static files to serve uploaded lab reports
os.makedirs("static/lab_reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "✅ PostgreSQL API is running!", "database": "Connected"}

@app.get("/health")
def health():
    return {"status": "ok"}
