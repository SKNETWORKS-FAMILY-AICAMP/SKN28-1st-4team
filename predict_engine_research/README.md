# Predict Engine Research

Notebook-first CatBoost regression workspace for training a car price model from the prepared dataset and saving the native CatBoost artifact as `output/model.cbm`.

## Structure

- `src/main.ipynb`: main training workflow
- `src/models/`: model defaults and CatBoost regressor helpers
- `src/tracking/`: logger and optional W&B helpers
- `src/runtime/`: simple runtime/device helpers
- `src/envs/`: `.env` loader for secret-backed integrations
- `data/`: input CSV files
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

1. Put your CSV in `data/prepared_training.csv`
2. Open `src/main.ipynb`
3. Check the notebook variables near the top:
   - `target_column`
   - `feature_columns`
   - `categorical_columns`
   - `max_iterations`, `early_stopping_rounds`, `train_log_period`
   - `use_wandb`, `wandb_project`, `wandb_entity`, `wandb_run_name`
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

## Metric Guide

이 프로젝트는 차량 가격을 예측하는 회귀 문제다.  
따라서 `accuracy`, `precision`, `recall`, `F1` 같은 분류 지표는 핵심 지표가 아니다.

현재 노트북에서 우선적으로 보는 지표는 아래 순서다.

1. `MAE(price_manwon)`
2. `RMSE(price_manwon)`
3. `valid_loss`
4. `R2(price_manwon)`

### 1. MAE(price_manwon)

- 의미: 예측값이 실제 가격에서 평균적으로 얼마나 벗어났는지 보여준다.
- 단위: `만원`
- 해석: 가장 직관적이다. 예를 들어 `MAE = 256.8` 이면 평균적으로 약 `256.8만원` 정도 오차가 난다는 뜻이다.
- 왜 중요하나: 이 프로젝트는 “실제 가격과 얼마나 차이 나는가”가 가장 중요하므로, 운영 해석과 비즈니스 설명이 가장 쉬운 `MAE` 를 1순위로 본다.

### 2. RMSE(price_manwon)

- 의미: 큰 오차에 더 강한 패널티를 주는 평균 오차 지표다.
- 단위: `만원`
- 해석: 일부 샘플에서 크게 틀리는 경우가 많으면 `RMSE` 가 빠르게 커진다.
- 왜 중요하나: 평균 오차만 낮고 일부 차량에서 크게 틀리는 모델은 실사용에서 위험하다. 그래서 `MAE` 다음으로 `RMSE` 를 본다.

### 3. valid_loss

- 의미: 검증 셋 기준의 학습 손실이다. 현재 CatBoost 설정에서는 `RMSE` 기준으로 기록된다.
- 로그 이름:
  - `train_loss`: 학습 셋 손실
  - `valid_loss`: 검증 셋 손실
- 왜 중요하나: 과적합 여부를 가장 빨리 확인할 수 있다.
  - `train_loss` 와 `valid_loss` 가 함께 내려가면 정상 학습
  - `train_loss` 만 내려가고 `valid_loss` 가 멈추거나 올라가면 과적합 신호

### 4. R2(price_manwon)

- 의미: 모델이 가격 분산을 얼마나 설명하는지 나타내는 설명력 지표다.
- 범위: 보통 `1` 에 가까울수록 좋다.
- 왜 보조 지표인가: 모델의 전체 설명력은 알 수 있지만, 실제로 몇 만원 틀렸는지 바로 보여주지는 못한다. 그래서 `MAE`, `RMSE` 보다 우선순위는 낮다.

## How To Read Results

학습 결과를 해석할 때는 아래 순서로 본다.

1. `aggregate_metrics.mae_price_manwon`
   - 평균적으로 얼마 정도 틀리는지 먼저 확인한다.
2. `aggregate_metrics.rmse_price_manwon`
   - 큰 오차가 많은지 확인한다.
3. fold 간 편차
   - 특정 fold만 유독 나쁘면 데이터 분포가 흔들리는지 점검한다.
4. `train_loss` / `valid_loss` 추이
   - 더 학습시켜도 되는지, 이미 과적합인지 본다.
5. `r2_price_manwon`
   - 최종 설명력 참고용으로 확인한다.

## Current Notebook Defaults

- target: `price_manwon`
- cross-validation: enabled by default
- default objective / eval metric: `RMSE`
- early stopping: enabled
- iteration-level logs:
  - `train_loss`
  - `valid_loss`

## Limitation Note

현재 데이터셋 규모는 약 `2,130`건 수준이라서, 모델이 학습할 수 있는 패턴 자체에 한계가 있다.

실제로 early stopping 조건을 더 느슨하게 하고 iteration을 더 늘려서 과적합 직전까지 한 번 더 확인했지만, `MAE(price_manwon)` 와 `RMSE(price_manwon)` 가 의미 있게 개선되지는 않았다.  
즉 현재 성능 한계는 튜닝 부족보다는 데이터 분포와 표본 수의 제약에 더 가깝다고 보는 것이 맞다.

따라서 현재 모델은 아래 전제를 두고 사용하는 것이 적절하다.

- 평균 오차가 수백만원 단위까지 발생할 수 있다.
- 특정 fold에서 오차가 크게 튀는 경우가 있다.
- 개별 차량 절대가격을 정밀하게 맞추는 용도보다는, 대략적인 가격 추정과 상대 비교 용도로 해석하는 편이 안전하다.

정리하면, 현 단계에서는 모델 구조를 더 복잡하게 만들기보다:

1. 더 많은 학습 데이터 확보
2. 차량 옵션 / 사고 여부 / 연료 / 지역 / 판매 상태 같은 설명 변수 확장
3. 이상치와 희소 조합 보강

이 성능 개선에 더 직접적인 영향을 줄 가능성이 높다.
