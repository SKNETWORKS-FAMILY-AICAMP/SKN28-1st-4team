# Models Cohort

This directory keeps the cohort work in one place.

The flow is split into two phases:

1. `original_source/`
   - collect domestic OEM source indexes
   - collect historical Bobaedream archive indexes
   - discover price-source URLs
   - treat Bobaedream detail pages as the main structured source
   - keep official price/catalog links as supplemental current-model sources
   - optionally cache selected price PDFs and extract text
   - build one raw vehicle-lake CSV
2. `cohort_generation/`
   - build a cohort-usable seed table from the raw lake
   - assign canonical variant ids later
   - prepare the weighted-neighbor cohort inputs

Current v1 scope is domestic brands only:

- Hyundai
- Kia
- Chevrolet
- Renault
- KGM

The first hard requirement is trim-level base price discovery.
That is why the source phase focuses on price-source URLs and a raw
`variant_seed_raw.csv` table instead of a large archive of HTML files.
