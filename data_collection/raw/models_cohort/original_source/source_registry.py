from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class SourceRegistryEntry:
    source_id: str
    brand: str
    source_kind: str
    landing_url: str
    collector_key: str
    fetch_mode: str
    notes: str
    external_code: str = ""
    active: bool = True

    def to_row(self) -> dict[str, object]:
        row = asdict(self)
        row["active"] = "Y" if self.active else "N"
        return row


DOMESTIC_SOURCE_REGISTRY: tuple[SourceRegistryEntry, ...] = (
    SourceRegistryEntry(
        source_id="official_hyundai_catalog_index",
        brand="hyundai",
        source_kind="official_catalog_index",
        landing_url="https://www.hyundai.com/kr/ko/e/vehicles/catalog-price-download",
        collector_key="hyundai",
        fetch_mode="playwright",
        notes="Rendered table page. Price PDFs are exposed through download buttons.",
    ),
    SourceRegistryEntry(
        source_id="archive_bobaedream_hyundai_index",
        brand="hyundai",
        source_kind="market_archive_index",
        landing_url="https://m.bobaedream.co.kr/calculator/carinfo",
        collector_key="bobaedream_archive",
        fetch_mode="http_html",
        notes="Historical model hierarchy from Bobaedream new-car price calculator.",
        external_code="49",
    ),
    SourceRegistryEntry(
        source_id="official_kia_catalog_index",
        brand="kia",
        source_kind="official_catalog_index",
        landing_url="https://www.kia.com/kr/vehicles/catalog-price",
        collector_key="kia",
        fetch_mode="playwright",
        notes="Tabbed rendered page. Price PDFs are exposed as direct anchors per visible tab.",
    ),
    SourceRegistryEntry(
        source_id="archive_bobaedream_kia_index",
        brand="kia",
        source_kind="market_archive_index",
        landing_url="https://m.bobaedream.co.kr/calculator/carinfo",
        collector_key="bobaedream_archive",
        fetch_mode="http_html",
        notes="Historical model hierarchy from Bobaedream new-car price calculator.",
        external_code="3",
    ),
    SourceRegistryEntry(
        source_id="official_chevrolet_catalog_index",
        brand="chevrolet",
        source_kind="official_catalog_index",
        landing_url="https://www.chevrolet.co.kr/e-catalog-price-list",
        collector_key="chevrolet",
        fetch_mode="http_html",
        notes="Index text is reachable, but full rendered price access is currently blocked and marked for manual review.",
    ),
    SourceRegistryEntry(
        source_id="archive_bobaedream_chevrolet_index",
        brand="chevrolet",
        source_kind="market_archive_index",
        landing_url="https://m.bobaedream.co.kr/calculator/carinfo",
        collector_key="bobaedream_archive",
        fetch_mode="http_html",
        notes="Historical model hierarchy from Bobaedream new-car price calculator.",
        external_code="105",
    ),
    SourceRegistryEntry(
        source_id="official_renault_catalog_index",
        brand="renault",
        source_kind="official_catalog_index",
        landing_url="https://renault.co.kr/ko/side/catalog_download.jsp",
        collector_key="renault",
        fetch_mode="playwright",
        notes="Rendered download buttons. Price PDFs are exposed through button-triggered downloads.",
    ),
    SourceRegistryEntry(
        source_id="archive_bobaedream_renault_index",
        brand="renault",
        source_kind="market_archive_index",
        landing_url="https://m.bobaedream.co.kr/calculator/carinfo",
        collector_key="bobaedream_archive",
        fetch_mode="http_html",
        notes="Historical model hierarchy from Bobaedream new-car price calculator.",
        external_code="26",
    ),
    SourceRegistryEntry(
        source_id="official_kgm_catalog_index",
        brand="kgm",
        source_kind="official_catalog_index",
        landing_url="https://www.kg-mobility.com/od/promotion/catalog-download",
        collector_key="kgm",
        fetch_mode="playwright",
        notes="Rendered download cards. Price PDFs are exposed through button-triggered downloads.",
    ),
    SourceRegistryEntry(
        source_id="archive_bobaedream_kgm_index",
        brand="kgm",
        source_kind="market_archive_index",
        landing_url="https://m.bobaedream.co.kr/calculator/carinfo",
        collector_key="bobaedream_archive",
        fetch_mode="http_html",
        notes="Historical model hierarchy from Bobaedream new-car price calculator.",
        external_code="31",
    ),
)


def default_registry_rows() -> list[dict[str, object]]:
    return [entry.to_row() for entry in DOMESTIC_SOURCE_REGISTRY]
