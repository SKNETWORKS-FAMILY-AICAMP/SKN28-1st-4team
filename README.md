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
자동차 가격은 속성 묶음의 결과로 해석할 수 있고, 중고차 시장은 정보 비대칭과 사용 비용 변화에 민감하게 반응합니다.  
또 실제 시장에서는 사고 이력과 차량 이력 정보가 가격 협상과 가치 판단의 핵심 근거로 작동합니다.

따라서 이 프로젝트는 "중고차 가격 예측 모델" 이라기보다,  
**중고차 가격을 해석하고 설명하는 제품 시스템**을 만들기 위한 저장소라고 보는 편이 더 정확합니다.

더 자세한 문제 정당화와 배경은 아래 문서에서 이어집니다.

- [문제 정당화 문서](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/justification.md)
- [프로젝트 문서 사이트](https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/)

### 핵심 참고 문헌

| 구분 | 원문 | 이 문서에서 쓰는 이유 |
| --- | --- | --- |
| 이론 | [Rosen (1974), *Hedonic Prices and Implicit Markets*](https://matthewturner.org/ec2410/readings/Rosen_JPE_1974.pdf) | 자동차 가격을 속성 묶음으로 보는 기본 관점 |
| 시장 구조 | [Akerlof (1970), *The Market for "Lemons"*](https://www.sfu.ca/~allen/Ackerlof.pdf) | 중고차 시장의 정보 비대칭과 품질 불확실성 설명 |
| 시장 반응 | [Busse, Knittel, Zettelmeyer (2009), *Pain at the Pump*](https://www.nber.org/papers/w15590) | 사용 비용 변화가 중고차 상대가격에 반영되는 방식 설명 |
| 가격 구간 | [Englmaier, Schmöller, Stowasser, *Price Discontinuities in an Online Market for Used Cars*](https://www.storre.stir.ac.uk/retrieve/25a7b70a-723a-4f63-a32a-495294664010/pdomuc2016.pdf) | 연식·주행거리 구간 경계에서 가격이 매끄럽지 않을 수 있다는 점 설명 |
| 실무 자료 | [CARFAX, *History-Based Value / Accident & Damage*](https://support.carfax.com/article/what-is-carfax-value-and-how-is-it-calculated2) | 사고·이력 정보가 실제 가치 판단에 쓰인다는 실무 근거 |

<details>
<summary>Rosen (1974) 요약</summary>

이 논문은 가격을 단순 숫자가 아니라 여러 속성의 결합 결과로 해석하는 헤도닉 가격 관점을 제공합니다.  
이 프로젝트에서 `brand`, `model`, `trim`, `color`, `mileage` 같은 요소를 함께 보려는 이유를 설명하는 가장 기본적인 배경입니다.

</details>

<details>
<summary>Akerlof (1970) 요약</summary>

이 논문은 중고차 시장에서 판매자와 구매자 사이의 정보 비대칭이 어떻게 시장 품질을 왜곡할 수 있는지 설명합니다.  
이 프로젝트에서 사고 이력, 차량 상태, 이력 정보, 설명 가능한 요인을 중요하게 다루는 이유와 직접 연결됩니다.

</details>

<details>
<summary>Busse, Knittel, Zettelmeyer (2009) 요약</summary>

이 연구는 연료비 같은 사용 비용 변화가 신차뿐 아니라 중고차 가격에도 영향을 줄 수 있다는 점을 보여줍니다.  
즉 중고차 가격은 차량 자체 속성만이 아니라 유지 비용과 시장 환경 변화에도 반응한다는 점을 뒷받침합니다.

</details>

<details>
<summary>Englmaier, Schmöller, Stowasser 요약</summary>

이 연구는 온라인 중고차 시장에서 특정 구간 경계에서 가격이 불연속적으로 움직일 수 있다는 점을 보여줍니다.  
이 프로젝트에서 차량 연식과 주행거리를 단순 선형 변수로만 보지 않고, 구간 효과와 시장적 심리도 함께 고려해야 한다는 배경으로 사용할 수 있습니다.

</details>

<details>
<summary>CARFAX 자료 요약</summary>

이 자료는 사고와 차량 이력 정보가 실제 중고차 가치 평가에 반영된다는 실무적 근거를 제공합니다.  
이 프로젝트에서 상승 요인과 하락 요인을 별도로 설명하려는 방향, 그리고 단순 가격 숫자보다 설명 가능한 근거를 같이 보여주려는 방향과 맞닿아 있습니다.

</details>

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
