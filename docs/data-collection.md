---
title: 데이터 준비
---

# 데이터 준비

`data_collection/` 은 원천 데이터를 정리하고, 학습 가능한 형태로 만드는 파이프라인을 담당합니다.

## 담당 역할

- 원천 소스 정리
- 상세 페이지 sanitize
- 학습용 컬럼 선택과 정리
- category / size score 계산용 참조 테이블 준비
- 최종 training-ready CSV 생성

## 왜 별도 영역으로 두는가

중고차 데이터는 그대로 모델에 넣기 어렵습니다.  
브랜드 표기, 모델명, 세부 트림, 체급, 색상, 주행거리 같은 정보가 일관되지 않기 때문입니다.

따라서 이 영역은 단순 수집이 아니라,  
**모델이 학습 가능한 형태로 문제를 다시 정의하는 층**에 가깝습니다.

## 결과적으로 만들어지는 것

이 파이프라인의 결과는 대략 두 갈래로 이어집니다.

- 모델 학습용 CSV
- 백엔드 전처리에서 재사용할 reference 데이터

즉 데이터 준비 단계는 연구 워크스페이스와 백엔드 둘 다에 영향을 줍니다.

## 어디를 더 보면 되는가

- 코호트/원천 수집 README: [data_collection/raw/models_cohort/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/data_collection/raw/models_cohort/README.md)
- 문제 배경: [justification.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/docs/justification.md)
