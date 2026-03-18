# Predict Engine Research

`predict_engine_research` 는 가격 예측 모델을 학습하고 산출물을 저장하는 연구용 워크스페이스입니다.  
현재는 `CatBoostRegressor` 기반 회귀 모델을 notebook 중심으로 학습합니다.

## 현재 목적

- `prepared_training.csv` 로 학습 데이터 로딩
- feature / target 설정
- 교차검증 기반 성능 확인
- `model.cbm`, `feature_manifest.json`, `metrics.json` 산출
- 필요 시 W&B 실험 추적

## 디렉토리 구조

```text
predict_engine_research/
├─ README.md
├─ .env.example
├─ data/
├─ output/
└─ src/
   ├─ main.ipynb
   ├─ test.ipynb
   ├─ envs/
   ├─ models/
   ├─ runtime/
   ├─ tracking/
   └─ wandb/
```

## 입력 데이터

현재 학습 입력 파일:

- `data/prepared_training.csv`

주요 컬럼:

- `brand`
- `model_name`
- `trim_name`
- `major_category`
- `size_score`
- `vehicle_age_years`
- `color`
- `mileage_km`
- `price_manwon`

현재 모델은 `model_year` 를 사용하지 않습니다.

## 메인 노트북

주 학습 노트북:

- `src/main.ipynb`

현재 흐름:

1. CSV 로드
2. target / feature / categorical column 확정
3. 5-fold 교차검증
4. early stopping 기반 학습
5. aggregate metric 계산
6. full-data 최종 학습
7. 산출물 저장

테스트 노트북:

- `src/test.ipynb`

용도:

- 특정 조합 한 건을 잡아 `vehicle_age_years`, `mileage_km` 변화에 따른 예측값을 시각화

## 현재 모델 설정

현재 출력 기준:

- target: `price_manwon`
- feature columns:
  - `brand`
  - `model_name`
  - `trim_name`
  - `major_category`
  - `size_score`
  - `vehicle_age_years`
  - `color`
  - `mileage_km`
- categorical columns:
  - `brand`
  - `model_name`
  - `trim_name`
  - `major_category`
  - `color`

현재 대표 학습 설정:

- `n_splits = 5`
- `max_iterations = 2000`
- `early_stopping_rounds = 300`
- `train_log_period = 25`
- `final_iteration_strategy = "p75"`

## 산출물

학습 성공 시 아래 파일이 생성됩니다.

- `output/model.cbm`
- `output/feature_manifest.json`
- `output/metrics.json`

이 산출물은 이후 백엔드 `be/src/external/predict_engine/model_assets/` 로 동기화해 사용합니다.

## 지표 해석

이 문제는 분류가 아니라 회귀입니다.  
따라서 `accuracy`, `precision`, `recall`, `F1` 을 보지 않습니다.

현재 우선순위는 아래와 같습니다.

1. `MAE(price_manwon)`
2. `RMSE(price_manwon)`
3. `valid_loss`
4. `R2(price_manwon)`

### MAE

- 평균적으로 몇 만원 틀리는지 바로 해석할 수 있는 지표입니다.
- 운영 관점에서 가장 직관적인 지표입니다.

### RMSE

- 큰 오차에 더 민감합니다.
- 일부 샘플에서 크게 틀리는지 보기 좋습니다.

### valid_loss

- 현재 설정에서는 사실상 검증 RMSE입니다.
- `train_loss` 와 함께 보면 과적합 여부를 판단하기 좋습니다.

### R2

- 설명력 참고용 보조 지표입니다.
- 실사용 해석은 MAE/RMSE보다 우선순위가 낮습니다.

## 현재 한계

현재 데이터 규모는 약 `2,130행` 수준입니다.  
실제로 iteration과 early stopping 조건을 더 느슨하게 조정해도 성능이 크게 개선되지는 않았습니다.

즉 현재 성능 한계는 튜닝 부족보다 아래 요인의 영향이 큽니다.

- 학습 데이터 규모 부족
- 희소 조합 존재
- 설명 변수 제한
- 일부 fold 편차 존재

따라서 현 단계 모델은 아래처럼 해석하는 것이 안전합니다.

- 절대가격 정밀 예측보다는 대략적인 가격 추정
- 현재 가격과 미래 감가 방향성 참고
- 차량 간 상대 비교 참고

## W&B

`src/main.ipynb` 에서 `use_wandb = True` 로 실행하면 W&B에 로그를 보낼 수 있습니다.

로컬 비밀값은 `.env` 로 관리합니다.

지원 키:

- `WANDB_API_KEY`

샘플:

```bash
cp .env.example .env
```

## 실행

```bash
cd predict_engine_research
uv sync
```

그 다음 `src/main.ipynb` 를 열어 순서대로 실행하면 됩니다.

커맨드라인에서 `.env` 를 함께 주입하려면:

```bash
cd predict_engine_research
UV_ENV_FILE=.env uv run jupyter notebook
```
