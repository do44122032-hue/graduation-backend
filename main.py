from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, dashboard
from database import engine
import models

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

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

@app.get("/")
def root():
    return {"status": "✅ PostgreSQL API is running!", "database": "Connected"}

@app.get("/health")
def health():
    return {"status": "ok"}
