---
title: 모델 연구
---

# 모델 연구

`predict_engine_research/` 는 가격 예측 모델을 실험하고, 학습하고, 산출물을 만드는 연구 워크스페이스입니다.

## 담당 역할

- 학습용 CSV 로드
- feature와 target 정의
- 교차검증 기반 성능 확인
- 최종 모델 산출물 생성
- 필요 시 실험 추적

## 이 영역이 중요한 이유

이 저장소의 예측 결과는 결국 연구 워크스페이스에서 만든 모델 산출물에 의해 결정됩니다.  
따라서 이 영역은 "실험" 용도이면서 동시에 운영 모델의 출발점이기도 합니다.

현재 산출물은 아래와 같습니다.

- `model.cbm`
- `feature_manifest.json`
- `metrics.json`

이 파일들은 이후 백엔드 쪽으로 복사되어 실제 서비스에서 사용됩니다.

## 읽을 때의 관점

이 영역은 제품 UI 문서가 아니라 모델 실험 문서에 가깝습니다.  
따라서 아래 질문을 중심으로 보면 됩니다.

- 어떤 데이터를 feature로 썼는가
- 어떤 지표를 중요하게 보는가
- 성능 한계는 무엇인가
- 어떤 산출물이 서비스에 반영되는가

## 어디를 더 보면 되는가

- 연구 워크스페이스 README: [predict_engine_research/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/predict_engine_research/README.md)
- 실험 기록: [experiments.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/experiments.md)
