---
title: SKN28 Technical Docs
---

# SKN28 기술 문서

> 진행 중인 문서입니다. 모델 설계, 데이터 파이프라인, 서비스 역할, 실험 추적 방식은 현재도 계속 업데이트되고 있습니다.

이 문서는 루트 `README.md` 보다 더 기술적인 설명을 담는 GitHub Pages용 문서 허브입니다.

## 문서 구성

- [문제 정당화](justification.md): 왜 기존 중고차 가격 서비스 접근만으로는 부족한지
- [아키텍처](architecture.md): 모노레포 구조, 서비스 경계, 루트 Compose 운영 방식
- [기술 결정](technical-decisions.md): cohort-based 설계, gRPC/ONNX, uv workspace 채택 이유
- [실행 가이드](runbook.md): `.env` 준비, 로컬 실행, 루트 Compose 실행 방법
- [실험 추적](experiments.md): W&B를 설명용 문서와 연결하는 방식

## 이 문서를 따로 둔 이유

- 저장소 `README.md` 는 빠르게 프로젝트를 이해하는 용도로 유지한다.
- 설계 근거, 세부 전술, 아키텍처 이유, 실험 기록은 길어질수록 별도 문서가 더 적합하다.
- GitHub Pages를 이용하면 별도 웹앱을 만들지 않고도 같은 저장소에서 기술 문서를 공개할 수 있다.

## 문서 운영 원칙

- 사용자 관점 설명은 `README.md` 중심으로 유지한다.
- 기술적 디테일은 `docs/` 기준으로 누적한다.
- 학습 지표는 W&B에서 기록하고, 공개 가능한 리포트만 문서에 연결한다.
