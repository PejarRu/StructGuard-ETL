from fastapi import FastAPI

from app.routers import endpoints

app = FastAPI(title="StructGuard API", version="0.1.0")

app.include_router(endpoints.router)
