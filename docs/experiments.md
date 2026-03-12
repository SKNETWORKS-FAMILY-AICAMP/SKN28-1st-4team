---
title: 실험 추적
---

# 실험 추적

## 원칙

이 프로젝트에서 W&B는 학습 실험 기록용으로 사용하고, GitHub Pages는 설명 문서용으로 사용한다.

- 학습 중 생성되는 loss, metric, artifact 기록은 W&B에 남긴다.
- 공개 가능한 리포트만 GitHub Pages에 연결한다.
- GitHub Pages 쪽에는 W&B API 키를 두지 않는다.

즉, 실험은 W&B가 관리하고, 설명은 문서 사이트가 담당한다.

## 왜 이 방식이 맞는가

- 사용자가 직접 실험 대시보드를 조작할 필요가 없다.
- 프로젝트 소개용으로는 public report 링크나 embed면 충분하다.
- 민감한 키를 저장소에 커밋할 필요가 없다.

## W&B 연결 방식

### 추천 흐름

1. 로컬 또는 CI에서 학습을 실행한다.
2. W&B에 실험 결과를 기록한다.
3. 공개 가능한 report를 만든다.
4. report URL을 이 문서 사이트에 연결한다.

### 현재 설정 방식

`docs/_config.yml` 의 아래 값을 채우면 GitHub Pages에 report를 embed 할 수 있다.

```yaml
wandb_report_url: "https://wandb.ai/..."
wandb_report_title: "실험 리포트 제목"
```

## Public report embed

W&B 문서 기준으로 embed는 public report에 대해서만 가능하다.

{% if site.wandb_report_url and site.wandb_report_url != "" %}
<iframe src="{{ site.wandb_report_url }}" style="width: 100%; height: 900px; border: 0;"></iframe>

{% if site.wandb_report_title and site.wandb_report_title != "" %}
현재 연결된 리포트: **{{ site.wandb_report_title }}**
{% endif %}

[W&B 리포트 새 탭에서 열기]({{ site.wandb_report_url }})
{% else %}
아직 W&B public report URL이 연결되지 않았다.

- 학습 결과를 W&B에 업로드한다.
- 공개 가능한 report를 생성한다.
- `docs/_config.yml` 에 `wandb_report_url` 을 넣는다.

현재 단계에서는 이 페이지가 실험 설명용 placeholder 역할을 한다.
{% endif %}

## 보안 메모

- `WANDB_API_KEY` 는 저장소에 커밋하지 않는다.
- 필요하면 로컬 환경변수나 GitHub Actions secrets로만 관리한다.
- 설명용 공개 report만 쓸 경우 Pages에는 API 키가 필요 없다.
