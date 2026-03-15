# Predict Engine Research

Notebook-first CatBoost regression workspace for training a car price model and saving the native CatBoost artifact as `output/model.cbm`.

## Structure

- `src/main.ipynb`: main training workflow
- `src/models/`: model defaults and CatBoost regressor helpers
- `src/tracking/`: logger and optional W&B helpers
- `src/runtime/`: simple runtime/device helpers
- `src/envs/`: `.env` loader for secret-backed integrations
- `data/raw/`: input CSV files
- `output/`: generated model and metadata files

## Environment

`predict_engine_research/.env` is only for local secrets.

Current supported secret:

- `WANDB_API_KEY`: optional, only needed when `use_wandb = True` in `src/main.ipynb`

Setup:

```bash
cp .env.example .env
```

Then fill in `WANDB_API_KEY` if you want W&B syncing.

## Install

From `predict_engine_research/`:

```bash
uv sync
```

## Run

1. Put your CSV in `data/raw/`
2. Open `src/main.ipynb`
3. Update the notebook variables near the top:
   - `data_path`
   - `target_column`
   - `feature_columns` if needed
   - `categorical_columns` if needed
   - `use_wandb`
   - `wandb_project`, `wandb_entity`, `wandb_run_name`
4. Run the notebook cells in order

If you want uv itself to preload `.env` for commands, use:

```bash
UV_ENV_FILE=.env uv run ...
```

## Outputs

After a successful run, the notebook writes:

- `output/model.cbm`
- `output/metrics.json`
- `output/feature_manifest.json`

`model.cbm` is the primary deployment artifact for the current MVP.
