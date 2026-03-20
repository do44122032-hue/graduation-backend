from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users
import os

app = FastAPI(title="Graduation Project API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"status": "✅ Graduation Project API is running!", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}
