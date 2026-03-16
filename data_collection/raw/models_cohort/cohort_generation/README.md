# Cohort Generation

This package consumes the raw source outputs from `../original_source/data/`.

Current v1 responsibility:

- load `vehicle_lake_raw.csv`
- build a clearer `cohort_input.csv` table from the main Bobaedream source
- keep official URLs as supplemental metadata for later enrichment

Naming:

- `vehicle_lake_raw.csv`: as-collected raw rows from Bobaedream detail pages
- `cohort_input.csv`: the first cleaned table that is actually meant to feed cohort logic

Weighted-neighbor scoring is intentionally kept for the next step, after the
raw lake table is stable enough.

Recommended run:

```bash
uv run python data_collection/raw/models_cohort/cohort_generation/run.py
```
