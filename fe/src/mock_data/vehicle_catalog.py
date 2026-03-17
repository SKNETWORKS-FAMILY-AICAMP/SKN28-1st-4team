import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VehicleCandidate:
    id: str
    title: str
    year: str
    trim: str
    mileage: int
    fuel: str
    color: str


@dataclass(frozen=True)
class VehicleModelOption:
    id: str
    brand: str
    model: str
    image_src: str


ASSET_PATH = Path(__file__).resolve().parent.parent / "assets" / "brand_model_trim_reference.json"
COLOR_OPTIONS_ASSET_PATH = Path(__file__).resolve().parent.parent / "assets" / "training_color_options.json"
IMAGE_SOURCE_DIR = Path(__file__).resolve().parents[3] / "data_insert" / "source" / "images"

BRAND_DISPLAY_NAME = {
    "hyundai": "현대",
    "kia": "기아",
    "kgm": "KG모빌리티",
    "chevrolet": "쉐보레",
    "renault": "르노",
}
BRAND_KEY_BY_LABEL = {label: key for key, label in BRAND_DISPLAY_NAME.items()}

MODEL_BASE_PRICE = {
    "아반떼": 1780,
    "쏘나타": 2140,
    "그랜저": 3120,
    "투싼": 2480,
    "싼타페": 2970,
    "팰리세이드": 3950,
    "K3": 1680,
    "K5": 2090,
    "K8": 3250,
    "쏘렌토": 3180,
    "스포티지": 2360,
    "카니발": 3390,
    "트레일블레이저": 1940,
    "말리부": 1760,
    "트래버스": 3880,
    "QM6": 2490,
    "SM6": 2140,
}

COLOR_TONE = {
    "화이트": 0,
    "블랙": 25,
    "실버": 12,
    "그레이": 8,
    "블루": -18,
    "레드": -25,
    "화이트 펄": 18,
    "미드나잇 블랙": 28,
    "티타늄 실버": 14,
    "어비스 블루": 10,
    "다크 그린": -12,
    "샴페인 골드": 6,
    "버건디": -14,
    "아이보리": 4,
}

ACCIDENT_DETAIL_FIELDS = (
    ("accident_front", "전면부"),
    ("accident_left_side", "좌측면"),
    ("accident_right_side", "우측면"),
    ("accident_rear", "후면부"),
    ("accident_roof_pillar", "루프·필러"),
    ("accident_underbody", "하부·서스펜션"),
    ("accident_frame", "주요 골격"),
)

TRANSMISSION_OPTIONS = ("자동", "수동", "세미오토", "무단변속기", "기타")
FUEL_OPTIONS = ("가솔린", "디젤", "LPG", "하이브리드", "전기", "수소전기", "기타")
WARRANTY_OPTIONS = ("보험사보증", "자가보증")
USAGE_CHANGE_OPTIONS = ("렌트", "영업용")
RECALL_OPTIONS = ("리콜 이행", "리콜 미이행", "해당없음")
VIN_CONDITION_OPTIONS = ("양호", "부식", "훼손(오손)", "상이", "변조(변타)", "도말")
METER_CONDITION_OPTIONS = ("양호", "불량")
ACCIDENT_HISTORY_OPTIONS = ("없음", "있음")
SIMPLE_REPAIR_OPTIONS = ("없음", "있음")
SPECIAL_HISTORY_OPTIONS = ("침수", "화재")
COLOR_HISTORY_OPTIONS = ("전체도색", "색상변경")
MAJOR_OPTION_OPTIONS = ("썬루프", "네비게이션", "헤드업 디스플레이", "드라이브 어시스트", "통풍시트")
DOCUMENT_OPTIONS = ("사용설명서", "안전삼각대", "잭", "스패너")


def _load_color_options() -> tuple[str, ...]:
    fallback_colors = tuple(COLOR_TONE.keys())
    if not COLOR_OPTIONS_ASSET_PATH.exists():
        return fallback_colors

    raw_payload = json.loads(COLOR_OPTIONS_ASSET_PATH.read_text(encoding="utf-8"))
    raw_colors = raw_payload.get("colors", raw_payload) if isinstance(raw_payload, dict) else raw_payload
    colors = tuple(
        color.strip()
        for color in raw_colors
        if isinstance(color, str) and color.strip()
    )
    return colors or fallback_colors


def _load_reference_map() -> dict[str, dict[str, list[str]]]:
    raw_payload = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    brand_model_trim_map = raw_payload["brand_model_trim_map"]
    catalog: dict[str, dict[str, list[str]]] = {}

    for canonical_brand, models in brand_model_trim_map.items():
        brand_label = BRAND_DISPLAY_NAME.get(canonical_brand, canonical_brand)
        normalized_models: dict[str, list[str]] = {}
        for model_name, trims in models.items():
            normalized_models[model_name] = trims if trims else ["기본 트림"]
        catalog[brand_label] = normalized_models

    return catalog


def _build_candidate_library(catalog: dict[str, dict[str, list[str]]]) -> dict[str, tuple[VehicleCandidate, ...]]:
    color_cycle = COLOR_OPTIONS
    fuel_cycle = ("가솔린", "디젤", "하이브리드", "전기")
    candidates_by_model: dict[str, tuple[VehicleCandidate, ...]] = {}

    for brand, models in catalog.items():
        for model_name, trims in models.items():
            candidates = []
            for index, trim_name in enumerate(trims):
                slug_brand = brand.lower().replace(" ", "-")
                slug_model = model_name.lower().replace(" ", "-").replace("/", "-")
                candidates.append(
                    VehicleCandidate(
                        id=f"{slug_brand}-{slug_model}-{index + 1}",
                        title=model_name,
                        year="",
                        trim=trim_name,
                        mileage=24000 + (index * 6300),
                        fuel=fuel_cycle[index % len(fuel_cycle)],
                        color=color_cycle[index % len(color_cycle)],
                    )
                )
            candidates_by_model[model_name] = tuple(candidates)

    return candidates_by_model


def _build_model_image(brand: str, model_name: str) -> str:
    matched_image = _find_model_image(brand, model_name)
    if matched_image is not None:
        return str(matched_image)
    return ""


def _normalize_image_token(value: str) -> str:
    lowered = value.casefold()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", "", lowered)
    return collapsed


def _find_model_image(brand: str, model_name: str) -> Path | None:
    canonical_brand = next(
        (key for key, label in BRAND_DISPLAY_NAME.items() if label == brand),
        brand.casefold(),
    )
    brand_files = sorted(IMAGE_SOURCE_DIR.glob(f"{canonical_brand}_*.jpg"))
    if not brand_files:
        return None

    normalized_model = _normalize_image_token(model_name)
    for image_path in brand_files:
        image_model_name = image_path.stem.split("_", 1)[1]
        if _normalize_image_token(image_model_name) == normalized_model:
            return image_path

    for image_path in brand_files:
        image_model_name = image_path.stem.split("_", 1)[1]
        if normalized_model in _normalize_image_token(image_model_name):
            return image_path

    return brand_files[0]


CATALOG = _load_reference_map()
COLOR_OPTIONS = _load_color_options()
_CANDIDATE_LIBRARY = _build_candidate_library(CATALOG)


def build_model_options_for_page(brand: str, model_names: list[str] | tuple[str, ...]) -> tuple[VehicleModelOption, ...]:
    return tuple(
        VehicleModelOption(
            id=f"{brand.lower().replace(' ', '-')}-{model_name.lower().replace(' ', '-')}-{index}",
            brand=brand,
            model=model_name,
            image_src=_build_model_image(brand, model_name),
        )
        for index, model_name in enumerate(model_names, start=1)
    )
