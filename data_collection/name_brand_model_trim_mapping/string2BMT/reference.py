# pyright: reportMissingImports=false

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .config import DEFAULT_REFERENCE_PATH
from .schemas import BrandModelTrimCandidate


TOKEN_PATTERN = re.compile(r"[0-9a-z]+|[가-힣]+")


@dataclass(frozen=True, slots=True)
class _CompiledCandidate:
    brand: str
    model_name: str
    trim_name: str | None
    label: str
    normalized_brand: str
    normalized_model: str
    normalized_trim: str | None
    normalized_label: str
    model_tokens: frozenset[str]
    trim_tokens: frozenset[str]
    label_tokens: frozenset[str]


class ReferenceStore:
    def __init__(self, payload: dict[str, Any], source_path: Path) -> None:
        self.payload = payload
        self.source_path = source_path
        self.metadata = dict(payload.get("metadata") or {})
        self.brand_model_trim_map = dict(payload.get("brand_model_trim_map") or {})
        self._compiled_candidates = self._compile_candidates()
        self._brand_lookup: dict[str, str] = {}
        self._model_lookup: dict[tuple[str, str], str] = {}
        self._trim_lookup: dict[tuple[str, str, str], str] = {}
        self._trims_by_model: dict[tuple[str, str], tuple[str, ...]] = {}
        self._build_lookups()

    @classmethod
    def from_path(cls, path: Path | str = DEFAULT_REFERENCE_PATH) -> "ReferenceStore":
        source_path = Path(path).resolve()
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        return cls(payload=payload, source_path=source_path)

    def shortlist(self, raw_name: str, *, limit: int = 8, min_score: float = 0.25) -> list[BrandModelTrimCandidate]:
        normalized_input = normalize_text(raw_name)
        input_tokens = frozenset(tokenize(raw_name))
        if not normalized_input:
            return []

        ranked: list[BrandModelTrimCandidate] = []
        for candidate in self._compiled_candidates:
            score, reasons = _score_candidate(normalized_input, input_tokens, candidate)
            if score < min_score:
                continue
            ranked.append(
                BrandModelTrimCandidate(
                    brand=candidate.brand,
                    model_name=candidate.model_name,
                    trim_name=candidate.trim_name,
                    score=round(score, 4),
                    match_basis=", ".join(reasons[:4]),
                )
            )

        ranked.sort(
            key=lambda item: (
                item.score,
                item.trim_name is not None,
                len(item.model_name),
                item.brand,
                item.model_name,
                item.trim_name or "",
            ),
            reverse=True,
        )
        return ranked[:limit]

    def resolve(self, *, brand: str | None, model_name: str | None, trim_name: str | None) -> tuple[str | None, str | None, str | None]:
        if not brand or not model_name:
            return (None, None, None)

        normalized_brand = normalize_text(brand)
        normalized_model = normalize_text(model_name)
        model_key = (normalized_brand, normalized_model)
        if model_key not in self._model_lookup:
            return (None, None, None)

        canonical_brand = self._brand_lookup[normalized_brand]
        canonical_model = self._model_lookup[model_key]
        if not trim_name:
            return (canonical_brand, canonical_model, None)

        normalized_trim = normalize_text(trim_name)
        trim_key = (normalized_brand, normalized_model, normalized_trim)
        if trim_key in self._trim_lookup:
            return (canonical_brand, canonical_model, self._trim_lookup[trim_key])

        canonical_trim = self._find_best_trim(model_key, normalized_trim)
        return (canonical_brand, canonical_model, canonical_trim)

    def to_dataframe(self):
        import pandas as pd

        rows: list[dict[str, Any]] = []
        for brand, model_map in self.brand_model_trim_map.items():
            for model_name, trim_names in model_map.items():
                rows.append(
                    {
                        "brand": brand,
                        "model_name": model_name,
                        "trim_count": len(trim_names),
                        "trim_names": trim_names,
                    }
                )
        return pd.DataFrame(rows).sort_values(["brand", "model_name"]).reset_index(drop=True)

    def _compile_candidates(self) -> list[_CompiledCandidate]:
        compiled: list[_CompiledCandidate] = []
        for brand, model_map in self.brand_model_trim_map.items():
            for model_name, trim_names in model_map.items():
                compiled.append(self._make_candidate(brand=brand, model_name=model_name, trim_name=None))
                for trim_name in trim_names:
                    compiled.append(self._make_candidate(brand=brand, model_name=model_name, trim_name=trim_name))
        return compiled

    def _make_candidate(self, *, brand: str, model_name: str, trim_name: str | None) -> _CompiledCandidate:
        label_parts = [brand, model_name]
        if trim_name:
            label_parts.append(trim_name)
        label = " ".join(label_parts)
        return _CompiledCandidate(
            brand=brand,
            model_name=model_name,
            trim_name=trim_name,
            label=label,
            normalized_brand=normalize_text(brand),
            normalized_model=normalize_text(model_name),
            normalized_trim=normalize_text(trim_name) if trim_name else None,
            normalized_label=normalize_text(label),
            model_tokens=frozenset(tokenize(model_name)),
            trim_tokens=frozenset(tokenize(trim_name or "")),
            label_tokens=frozenset(tokenize(label)),
        )

    def _build_lookups(self) -> None:
        for brand, model_map in self.brand_model_trim_map.items():
            normalized_brand = normalize_text(brand)
            self._brand_lookup[normalized_brand] = brand
            for model_name, trim_names in model_map.items():
                normalized_model = normalize_text(model_name)
                model_key = (normalized_brand, normalized_model)
                self._model_lookup[model_key] = model_name
                canonical_trims: list[str] = []
                for trim_name in trim_names:
                    normalized_trim = normalize_text(trim_name)
                    self._trim_lookup[(normalized_brand, normalized_model, normalized_trim)] = trim_name
                    canonical_trims.append(trim_name)
                self._trims_by_model[model_key] = tuple(canonical_trims)

    def _find_best_trim(self, model_key: tuple[str, str], normalized_trim: str) -> str | None:
        trim_names = self._trims_by_model.get(model_key) or ()
        if not trim_names or not normalized_trim:
            return None

        best_trim: str | None = None
        best_score = 0.0
        for trim_name in trim_names:
            candidate_trim = normalize_text(trim_name)
            score = 0.0
            if candidate_trim == normalized_trim:
                score += 1.0
            if candidate_trim and candidate_trim in normalized_trim:
                score += 0.35
            if normalized_trim in candidate_trim:
                score += 0.25
            score += SequenceMatcher(None, normalized_trim, candidate_trim).ratio() * 0.45
            if score > best_score:
                best_trim = trim_name
                best_score = score

        if best_score < 0.55:
            return None
        return best_trim


def load_reference_store(path: Path | str = DEFAULT_REFERENCE_PATH) -> ReferenceStore:
    return ReferenceStore.from_path(path)


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text)).casefold()
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def tokenize(text: str | None) -> tuple[str, ...]:
    normalized = normalize_text(text)
    if not normalized:
        return ()
    return tuple(TOKEN_PATTERN.findall(normalized))


def _score_candidate(
    normalized_input: str,
    input_tokens: frozenset[str],
    candidate: _CompiledCandidate,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if normalized_input == candidate.normalized_label:
        score += 1.45
        reasons.append("exact_label")
    if normalized_input == candidate.normalized_model and candidate.trim_name is None:
        score += 1.25
        reasons.append("exact_model")

    if candidate.normalized_model and candidate.normalized_model in normalized_input:
        score += 0.90
        reasons.append("model_in_input")
    elif normalized_input and normalized_input in candidate.normalized_model:
        score += 0.55
        reasons.append("input_in_model")

    model_overlap = _token_overlap(input_tokens, candidate.model_tokens)
    if model_overlap:
        score += model_overlap * 0.45
        reasons.append(f"model_token_overlap={model_overlap:.2f}")

    model_ratio = SequenceMatcher(None, normalized_input, candidate.normalized_model).ratio()
    score += model_ratio * 0.50

    if candidate.normalized_brand and candidate.normalized_brand in normalized_input:
        score += 0.15
        reasons.append("brand_in_input")

    if candidate.trim_name and candidate.normalized_trim:
        if candidate.normalized_trim in normalized_input:
            score += 0.70
            reasons.append("trim_in_input")

        trim_overlap = _token_overlap(input_tokens, candidate.trim_tokens)
        if trim_overlap:
            score += trim_overlap * 0.35
            reasons.append(f"trim_token_overlap={trim_overlap:.2f}")

        full_ratio = SequenceMatcher(None, normalized_input, candidate.normalized_label).ratio()
        score += full_ratio * 0.20
    else:
        full_ratio = SequenceMatcher(None, normalized_input, candidate.normalized_label).ratio()
        score += full_ratio * 0.10
        extra_tokens = input_tokens - candidate.model_tokens
        if extra_tokens:
            score -= min(0.12, 0.04 * len(extra_tokens))

    return (score, reasons)


def _token_overlap(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(right)
