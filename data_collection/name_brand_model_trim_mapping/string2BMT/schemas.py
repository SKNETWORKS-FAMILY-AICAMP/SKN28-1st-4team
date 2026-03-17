from __future__ import annotations

from pydantic import BaseModel, Field


class BrandModelTrimCandidate(BaseModel):
    brand: str
    model_name: str
    trim_name: str | None = None
    score: float = 0.0
    match_basis: str = Field(default="", description="Short explanation of why this candidate ranked well.")


class BrandModelTrimMatch(BaseModel):
    brand: str | None = None
    model_name: str | None = None
    trim_name: str | None = None

    def as_tuple(self) -> tuple[str | None, str | None, str | None]:
        return (self.brand, self.model_name, self.trim_name)

    @classmethod
    def from_candidate(cls, candidate: BrandModelTrimCandidate) -> "BrandModelTrimMatch":
        return cls(
            brand=candidate.brand,
            model_name=candidate.model_name,
            trim_name=candidate.trim_name,
        )
