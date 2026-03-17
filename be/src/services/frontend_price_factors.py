from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
import json
from pathlib import Path

from .ai_agent import AIAgentService, get_ai_agent_service
from .frontend_price_prediction import FrontendPricePredictionInput


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "frontend_price_factor_instructions.txt"
REFERENCE_ANNUAL_MILEAGE_KM = 13140
REFERENCE_SOURCE_NOTE = "한국교통안전공단 2024 분석 기준 자동차 1대당 하루 평균 36.0km, 연간 약 13,140km"
POPULAR_COLOR_SET = {
    "흰색",
    "진주색",
    "화이트 펄",
    "검정",
    "검정색",
    "쥐색",
    "회색",
    "그레이",
    "은색",
    "실버",
}
BANNED_PHRASES = ("신차 대비 사용감", "신차 대비", "당연히", "무조건")


@dataclass(frozen=True)
class FrontendPriceFactorResult:
    positive_factors: tuple[str, ...]
    negative_factors: tuple[str, ...]
    logic_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "positive_factors": list(self.positive_factors),
            "negative_factors": list(self.negative_factors),
            "logic_note": self.logic_note,
        }


class FrontendPriceFactorService:
    def __init__(self, ai_agent_service: AIAgentService | None = None) -> None:
        self._ai_agent_service = ai_agent_service

    def analyze(self, request: FrontendPricePredictionInput) -> FrontendPriceFactorResult:
        context = self._build_context(request)
        if self._ai_agent_service is not None:
            try:
                return self._analyze_with_ai(context)
            except Exception as exc:
                print(
                    "[frontend_price_factors] AI analysis failed, falling back to heuristic factors",
                    {"error": type(exc).__name__, "message": str(exc)},
                )
                pass
        return self._fallback_analyze(context)

    def _analyze_with_ai(self, context: dict[str, object]) -> FrontendPriceFactorResult:
        instructions = PROMPT_PATH.read_text(encoding="utf-8")
        response = self._ai_agent_service.create_response(
            input_text=json.dumps(context, ensure_ascii=False, indent=2),
            instructions=instructions,
            text={"format": {"type": "json_object"}},
        )
        raw_text = getattr(response, "output_text", None)
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ValueError("AI factor response did not contain output_text")

        payload = json.loads(raw_text)
        expected_topics = _build_expected_topic_map(context)
        positive_factors = _sanitize_ai_factor_list(
            payload.get("positive_factors", []),
            tone="positive",
            expected_topics=expected_topics,
        )
        negative_factors = _sanitize_ai_factor_list(
            payload.get("negative_factors", []),
            tone="negative",
            expected_topics=expected_topics,
        )
        logic_note = _normalize_sentence(str(payload.get("logic_note", "")).strip())
        if not logic_note or not _is_polite_sentence(logic_note):
            raise ValueError("AI factor response did not contain a polite logic_note")
        if not positive_factors and not negative_factors:
            raise ValueError("AI factor response did not contain usable factors")

        return FrontendPriceFactorResult(
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            logic_note=logic_note,
        )

    def _fallback_analyze(self, context: dict[str, object]) -> FrontendPriceFactorResult:
        positive: list[str] = []
        negative: list[str] = []

        annual_mileage_km = float(context["annual_mileage_km"])
        purchase_age_years = float(context["vehicle_age_years"])
        color = str(context["color"])
        transmission = str(context["transmission"])

        if annual_mileage_km <= REFERENCE_ANNUAL_MILEAGE_KM * 0.85:
            positive.append(
                f"연간 주행거리 추정치가 {annual_mileage_km:,.0f}km로 기준 {REFERENCE_ANNUAL_MILEAGE_KM:,.0f}km보다 낮아 주행거리 조건이 비교적 양호합니다."
            )
        elif annual_mileage_km >= REFERENCE_ANNUAL_MILEAGE_KM * 1.15:
            negative.append(
                f"연간 주행거리 추정치가 {annual_mileage_km:,.0f}km로 기준 {REFERENCE_ANNUAL_MILEAGE_KM:,.0f}km보다 높아 감가 압력이 커질 수 있습니다."
            )

        if purchase_age_years <= 3.0:
            positive.append(
                f"차량 사용 기간이 {purchase_age_years:.1f}년 수준으로 짧은 편이라 동일 차급 중고차 대비 연식 부담이 덜합니다."
            )
        elif purchase_age_years >= 7.0:
            negative.append(
                f"차량 사용 기간이 {purchase_age_years:.1f}년 수준으로 길어 동일 차급 중고차 대비 연식 감가 압력이 커질 수 있습니다."
            )

        if color in POPULAR_COLOR_SET:
            positive.append(f"{color} 계열은 중고차 시장에서 무난한 인기 색상으로 받아들여지는 편이라 재판매 협상에 유리할 수 있습니다.")
        else:
            negative.append(f"{color} 계열은 비교 매물 대비 선호도가 갈릴 수 있는 색상이라 수요 폭이 다소 좁아질 수 있습니다.")

        if transmission == "자동":
            positive.append("자동 변속기 기준이라 일반적인 중고차 수요와 잘 맞는 편입니다.")

        logic_note = (
            "구매일 기준 경과 연수, 추정 연간 주행거리, 색상 선호도, 변속기 선호도를 일반적인 중고차 거래 기준과 비교해 요인을 정리했습니다."
        )

        return FrontendPriceFactorResult(
            positive_factors=tuple(positive[:3]),
            negative_factors=tuple(negative[:3]),
            logic_note=logic_note,
        )

    def _build_context(self, request: FrontendPricePredictionInput) -> dict[str, object]:
        today = date.today()
        purchase_age_days = max((today - request.purchase_date).days, 0)
        vehicle_age_years = max(round(purchase_age_days / 365.25, 2), 0.1)
        annual_mileage_km = round(request.mileage_km / max(vehicle_age_years, 1.0), 2)
        annual_mileage_position = _classify_annual_mileage_position(annual_mileage_km)
        vehicle_age_band = _classify_vehicle_age_band(vehicle_age_years)
        color_marketability = "popular" if request.color in POPULAR_COLOR_SET else "mixed"
        transmission_marketability = "preferred" if request.transmission == "자동" else "neutral"
        return {
            "brand_key": request.brand_key,
            "brand_label": request.brand_label,
            "model_name": request.model_name,
            "trim_name": request.trim_name,
            "purchase_date": request.purchase_date.isoformat(),
            "vehicle_age_years": vehicle_age_years,
            "mileage_km": request.mileage_km,
            "annual_mileage_km": annual_mileage_km,
            "annual_mileage_position": annual_mileage_position,
            "reference_annual_mileage_km": REFERENCE_ANNUAL_MILEAGE_KM,
            "reference_source_note": REFERENCE_SOURCE_NOTE,
            "vehicle_age_band": vehicle_age_band,
            "color": request.color,
            "color_marketability": color_marketability,
            "transmission": request.transmission,
            "transmission_marketability": transmission_marketability,
        }


def _classify_annual_mileage_position(annual_mileage_km: float) -> str:
    if annual_mileage_km <= REFERENCE_ANNUAL_MILEAGE_KM * 0.85:
        return "below"
    if annual_mileage_km >= REFERENCE_ANNUAL_MILEAGE_KM * 1.15:
        return "above"
    return "average"


def _classify_vehicle_age_band(vehicle_age_years: float) -> str:
    if vehicle_age_years <= 3.0:
        return "recent"
    if vehicle_age_years >= 7.0:
        return "aged"
    return "mid"


def _build_expected_topic_map(context: dict[str, object]) -> dict[str, str]:
    expected_topics: dict[str, str] = {}
    annual_mileage_position = str(context.get("annual_mileage_position", ""))
    if annual_mileage_position == "below":
        expected_topics["mileage"] = "positive"
    elif annual_mileage_position == "above":
        expected_topics["mileage"] = "negative"

    vehicle_age_band = str(context.get("vehicle_age_band", ""))
    if vehicle_age_band == "recent":
        expected_topics["age"] = "positive"
    elif vehicle_age_band == "aged":
        expected_topics["age"] = "negative"

    color_marketability = str(context.get("color_marketability", ""))
    if color_marketability == "popular":
        expected_topics["color"] = "positive"
    elif color_marketability == "mixed":
        expected_topics["color"] = "negative"

    transmission_marketability = str(context.get("transmission_marketability", ""))
    if transmission_marketability == "preferred":
        expected_topics["transmission"] = "positive"

    return expected_topics


def _sanitize_ai_factor_list(
    values: object,
    *,
    tone: str,
    expected_topics: dict[str, str],
) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise ValueError("AI factor response did not contain factor arrays")

    normalized: list[str] = []
    seen_topics: set[str] = set()
    for item in values:
        text = _normalize_sentence(str(item).strip())
        if not text:
            continue
        if any(banned in text for banned in BANNED_PHRASES):
            continue
        if not _is_polite_sentence(text):
            raise ValueError("AI factor response contained non-polite factors")

        topic = _classify_factor_topic(text)
        if topic is None:
            continue
        if expected_topics.get(topic) != tone:
            continue
        if topic in seen_topics:
            continue

        seen_topics.add(topic)
        normalized.append(text)

    return tuple(normalized[:3])


def _normalize_sentence(text: str) -> str:
    text = text.strip().lstrip("-").strip()
    if not text:
        return ""
    if text.endswith(".") and not text.endswith("니다."):
        return text
    if text.endswith("니다."):
        return text
    if text.endswith("니다"):
        return f"{text}."
    return text


def _is_polite_sentence(text: str) -> bool:
    return text.endswith("니다.")


def _classify_factor_topic(text: str) -> str | None:
    if "주행거리" in text or "km" in text or "킬로" in text:
        return "mileage"
    if "연식" in text or "경과 연수" in text or "사용 기간" in text:
        return "age"
    if (
        "색상" in text
        or "화이트" in text
        or "흰색" in text
        or "검정" in text
        or "진주색" in text
        or "쥐색" in text
        or "회색" in text
        or "그레이" in text
        or "은색" in text
        or "실버" in text
    ):
        return "color"
    if "변속기" in text or "자동" in text:
        return "transmission"
    return None


@lru_cache(maxsize=1)
def get_frontend_price_factor_service() -> FrontendPriceFactorService:
    try:
        ai_agent_service = get_ai_agent_service()
    except Exception:
        ai_agent_service = None
    return FrontendPriceFactorService(ai_agent_service=ai_agent_service)
