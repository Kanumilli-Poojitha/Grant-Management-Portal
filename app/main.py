import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.application_controller import router as application_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.grant_controller import router as grant_router
from app.controllers.user_controller import router as user_router
from app.database import Base, engine
from app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Grant Management Portal",
    description="Secure multi-user grant management API with RBAC and OAuth 2.0",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(grant_router)
app.include_router(application_router)


@app.on_event("startup")
def on_startup():
    max_retries = 30
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            seed_database()
            logger.info("Database initialized and seeded successfully")
            return
        except Exception as exc:
            logger.warning("Database not ready (attempt %s/%s): %s", attempt + 1, max_retries, exc)
            time.sleep(2)
    raise RuntimeError("Failed to initialize database after multiple retries")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
