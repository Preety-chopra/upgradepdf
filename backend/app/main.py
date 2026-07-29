from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import files, health, jobs, pdf
from app.core.config import settings
from app.core.database import Base, engine
from app.modules.conversions.routes import router as conversions_router
from app.modules.ocr.routes import router as ocr_router

Base.metadata.create_all(bind=engine)

# create_all does not extend an existing PostgreSQL enum. Keep upgrades from
# earlier releases compatible with the compression operation.
if engine.dialect.name == "postgresql":
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TYPE joboperation ADD VALUE IF NOT EXISTS 'COMPRESS'")
        )


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.4.0",
    description="Secure PDF utility platform backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF Tools"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(conversions_router)
app.include_router(ocr_router)

@app.get("/")
def root():
    return {
        "message": "PDF Utility Platform API is running",
        "docs": "/docs",
        "version": "0.4.0",
    }
