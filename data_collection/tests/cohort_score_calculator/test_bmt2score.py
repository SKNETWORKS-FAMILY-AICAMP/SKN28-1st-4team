from __future__ import annotations

from pytest import approx

from data_collection.cohort_score_calculator.BMT2Score import get_size_score


def test_returns_score_for_known_tuple() -> None:
    score = get_size_score("kia", "더 뉴 쏘렌토", "노블레스")

    assert score is not None
    assert score == approx(67.67676767676768)


def test_suv_scores_increase_with_vehicle_size() -> None:
    kona_score = get_size_score("hyundai", "코나", "모던")
    sportage_score = get_size_score("kia", "디 올 뉴 스포티지", "프레스티지")
    sorento_score = get_size_score("kia", "더 뉴 쏘렌토", "프레스티지")

    assert kona_score is not None
    assert sportage_score is not None
    assert sorento_score is not None
    assert kona_score < sportage_score < sorento_score


def test_mixed_geometry_tuple_collapses_to_one_score() -> None:
    score = get_size_score("hyundai", "엑센트 (신형)", "프리미엄")

    assert score is not None
    assert score == approx(0.5141388174807198)


def test_returns_none_without_usable_geometry() -> None:
    assert get_size_score("chevrolet", "더 넥스트 이쿼녹스", "LS") is None


def test_falls_back_to_base_class_placeholder_when_trim_is_missing() -> None:
    base_score = get_size_score("kia", "레이", "-")
    fallback_score = get_size_score("kia", "레이", None)

    assert base_score is not None
    assert fallback_score == base_score


def test_returns_model_level_score_when_only_base_class_exists() -> None:
    score = get_size_score("renault", "SM7 노바", None)

    assert score is not None
