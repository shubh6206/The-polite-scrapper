"""
Data Models and Schema Definitions using Pydantic.
FlyRank Backend Track Week 5 Assignment A9
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class BookRecord(BaseModel):
    """
    Validated schema for a scraped book record.
    Preserves both raw values and normalized types with full provenance.
    """
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute HTTPS product URL")
    price_text: str = Field(..., description="Raw price text as scraped (e.g. £51.77)")
    price_gbp: float = Field(..., ge=0.0, description="Normalized numeric price in GBP")
    availability_text: str = Field(..., description="Raw availability status string")
    rating_text: str = Field(..., description="Star rating string (e.g. Three)")
    description: Optional[str] = Field(None, description="Book description or None if absent")
    source_page: str = Field(..., description="Provenance source catalogue URL")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp of fetch")

    @validator("product_url")
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://") and not v.startswith("http://127.0.0.1"):
            raise ValueError(f"product_url must start with https:// (or test localhost), got: {v}")
        return v

    class Config:
        validate_assignment = True
        extra = "forbid"


class RecordValidationError(BaseModel):
    """Container for invalid records that failed schema validation."""
    raw_record: Dict[str, Any]
    error_reason: str
