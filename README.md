# SKN28 중고차 가격 예측 플랫폼

이 저장소는 중고차 가격을 숫자 하나로만 보여주는 도구를 만들기 위한 곳이 아닙니다.  
우리가 풀고 싶은 문제는 아래와 같습니다.

- 지금 이 차량의 가격을 어느 정도로 봐야 하는가
- 앞으로 몇 년 동안 가격이 어떻게 변할 가능성이 있는가
- 왜 이 가격이 나왔는지 사용자가 이해할 수 있는가

즉, 이 프로젝트의 목표는 **현재 가격 + 미래 감가 흐름 + 설명 가능한 근거**를 함께 제공하는 중고차 가격 예측 경험을 만드는 것입니다.

---

## 프로젝트 동기

기존 중고차 서비스는 보통 현재 시세나 매물가를 보여주는 데 집중합니다.  
하지만 실제 사용자 판단은 그보다 더 복잡합니다.

- 지금 팔면 적절한 타이밍인가
- 몇 년 더 타면 감가가 얼마나 커질까
- 동급 차량 대비 왜 비싸거나 싼가
- 주행거리, 색상, 사고 이력 같은 정보가 실제로 어떤 영향을 주는가

이 프로젝트는 이런 질문에 답할 수 있는 제품을 목표로 합니다.  
핵심은 단순 시세 조회가 아니라 **판매 의사결정을 돕는 가격 해석 시스템**입니다.

조금 더 구체적으로 보면, 이 프로젝트가 해결하려는 문제는 세 층으로 나뉩니다.

1. **현재 적정가**
   - 지금 이 차량을 얼마 정도로 보는 것이 타당한가
2. **미래 감가**
   - 앞으로 1년, 3년, 5년 뒤에는 가격이 어느 방향으로 움직일 가능성이 큰가
3. **설명 가능성**
   - 왜 그 가격이 나왔는지, 어떤 요인이 유리하고 불리한지를 납득 가능한 언어로 보여줄 수 있는가

이 접근은 단순 시세 조회 서비스와 다릅니다.  
우리는 가격 숫자 하나를 맞추는 것보다, **사용자가 실제로 "지금 팔지, 더 탈지"를 판단할 수 있는 맥락**을 제공하는 데 더 가깝습니다.

이 문제를 이렇게 보는 이유는 기존 연구와 실무 관찰 모두에서 확인할 수 있습니다.

- Rosen (1974)의 헤도닉 가격 이론은 자동차 가격이 단일 값이 아니라 속성 묶음의 결과라는 점을 보여줍니다.
- Akerlof (1970)의 레몬시장 문제는 중고차 거래에서 정보 비대칭이 얼마나 큰지 설명합니다.
- 실제 중고차 시장에서는 주행거리, 사고 이력, 소유 이력, 옵션, 색상 같은 요소가 단순한 보조 정보가 아니라 가격 설명의 핵심입니다.

따라서 이 프로젝트는 "중고차 가격 예측 모델" 이라기보다,  
**중고차 가격을 해석하고 설명하는 제품 시스템**을 만들기 위한 저장소라고 보는 편이 더 정확합니다.

더 자세한 문제 정당화와 배경은 아래 문서에서 이어집니다.

- [문제 정당화 문서](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/justification.md)
- [프로젝트 문서 사이트](https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/)

---

## 저장소가 하는 일

현재 저장소는 네 영역이 함께 움직이는 구조입니다.

- `fe/`
  - 사용자가 차량을 선택하고 예측 결과를 확인하는 프런트엔드
- `be/`
  - 예측 API, 요인 분석 API, 모델 이미지 API를 제공하는 백엔드
- `predict_engine_research/`
  - 가격 예측 모델을 학습하고 산출물을 관리하는 연구 워크스페이스
- `data_collection/`
  - 원천 데이터 정리와 학습용 데이터 준비를 담당하는 파이프라인

## 저장소 구조

```text
SKN28-1st-4team/
├─ README.md
├─ pyproject.toml
├─ docker-compose.yml
├─ fe/
├─ be/
├─ predict_engine_research/
├─ data_collection/
├─ data_insert/
└─ docs/
```

---

## 실행 방법

### 워크스페이스와 로컬 실행

루트는 `uv` workspace 입니다.

```bash
uv sync --all-packages
```

백엔드:

```bash
cd be
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8000
```

프런트:

```bash
cd fe
uv run --env-file .env streamlit run src/app.py
```

기본 주소:

- 프런트: `http://localhost:8501`
- 백엔드: `http://127.0.0.1:8000`

### Docker Compose

```bash
docker compose up --build
```

---

## 문서 안내

루트 README는 프로젝트의 목적과 실행 방법을 빠르게 설명하는 문서로 유지합니다.  
구현 세부사항과 디렉토리별 설명은 `docs/` 와 각 디렉토리 README로 분리합니다.

### 프로젝트 문서

- 외부 문서 사이트: [GitHub Pages](https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/)
- 저장소 내부 허브: [docs/index.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/index.md)
- [docs/justification.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/justification.md)
- [docs/frontend.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/frontend.md)
- [docs/backend.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/backend.md)
- [docs/research.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/research.md)
- [docs/data-collection.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/data-collection.md)

### 디렉토리별 README

- [fe/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/fe/README.md)
- [be/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/be/README.md)
- [predict_engine_research/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/predict_engine_research/README.md)
- [data_collection/raw/models_cohort/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/data_collection/raw/models_cohort/README.md)
