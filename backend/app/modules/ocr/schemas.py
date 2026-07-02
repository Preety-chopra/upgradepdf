from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OcrStatus = Literal["queued", "running", "completed", "failed", "timeout"]


class OcrJobCreateResponse(BaseModel):
    job_id: str
    status: OcrStatus = "queued"
    status_url: str
    pdf_download_url: str | None = None
    text_download_url: str | None = None
    message: str = "OCR job queued."


class OcrStatusResponse(BaseModel):
    job_id: str
    status: OcrStatus
    percent: int = Field(ge=0, le=100)
    message: str
    filename: str | None = None
    language: str | None = None
    page_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    output_pdf_available: bool = False
    output_text_available: bool = False
    error: str | None = None


class OcrLanguage(BaseModel):
    code: str
    label: str
    installed: bool = False


class OcrLanguagesResponse(BaseModel):
    supported: list[OcrLanguage]
    installed: list[str]
