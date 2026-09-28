# DEEPNOID DART Financial Agent

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-1264D8?style=for-the-badge)](https://hsc-class02.github.io/JS_DEEPNOID/)

> 딥노이드(315640)의 DART 정기보고서(사업보고서·반기보고서·분기보고서)를 수집하고, 주요 재무수치와 재무비율을 계산한 뒤 GitHub Pages 대시보드로 공개하는 자동화 Agent입니다.

## Dashboard

**🔗 [대시보드 바로가기](https://hsc-class02.github.io/JS_DEEPNOID/)**

GitHub Pages 주소가 다르게 생성되면 위 링크를 실제 Pages URL로 교체하세요.

## 국내 Peer Firms

딥노이드의 공시·시장자료에서 유사 국내 의료 AI 상장사로 함께 언급되는 비교군을 기본값으로 넣었습니다. 비교군은 분석 목적에 따라 추가/삭제할 수 있습니다.

| 기업 | 종목코드 | 비교 영역 |
|---|---:|---|
| 루닛 | 328130 | 의료 영상·조직 분석 AI |
| 뷰노 | 338220 | 의료 영상·생체신호·의료 AI |
| 제이엘케이 | 322510 | 의료 영상·원격의료 AI |
| 코어라인소프트 | 384470 | 흉부 CT 기반 영상진단 AI |

## 수집 범위

- 기업: 딥노이드 / DART corp_code `01344831` / KOSDAQ `315640`
- 시작 연도: 2010
- 보고서: 사업보고서, 반기보고서, 분기보고서
- 데이터 API: OpenDART
- XBRL 재무제표 API의 구조화 재무수치는 2015년 이후 제공 범위입니다. 따라서 2010~2014년은 보고서 메타데이터/원문 보관을 우선하고, 구조화 재무수치가 존재하지 않는 경우 대시보드 수치에는 임의의 값을 채우지 않습니다.
- 기준 재무제표: 기본값 `OFS`(별도). 필요하면 `config.json`에서 `CFS`(연결)로 변경합니다.

## 주요 수치 및 비율

### 핵심 재무수치

- 자산총계 / 유동자산 / 비유동자산
- 부채총계 / 유동부채 / 비유동부채
- 자본총계
- 매출액 / 매출원가 / 매출총이익
- 영업이익 / 법인세비용차감전순이익 / 당기순이익
- 영업활동현금흐름
- 유형자산·무형자산 취득액(공시 계정명이 일치하는 경우)

### 재무비율

- 매출액 성장률
- 자산 성장률
- 영업이익률
- 순이익률
- 부채비율
- 자기자본비율
- 유동비율
- 총자산회전율
- ROA
- ROE
- 영업현금흐름/매출액

## API Key 입력 방법

1. OpenDART에서 인증키를 발급합니다: https://opendart.fss.or.kr/
2. GitHub 저장소의 **Settings → Secrets and variables → Actions → New repository secret**으로 이동합니다.
3. Name: `DART_API_KEY`
4. Secret: 발급받은 40자리 API 키
5. 저장 후 **Actions → DART monthly update → Run workflow**를 실행해 초기 수집을 테스트합니다.

**API 키를 코드, README, JSON, CSV 또는 commit에 직접 입력하지 마세요.**

## GitHub Pages 설정

이 저장소는 `.github/workflows/pages.yml`에서 GitHub Pages를 GitHub Actions 방식으로 배포하도록 구성되어 있습니다.

처음 한 번 저장소의 **Settings → Pages → Build and deployment → Source**가 `GitHub Actions`인지 확인하세요.

대시보드 기본 URL:

`https://hsc-class02.github.io/JS_DEEPNOID/`

## 매월 1일 자동 업데이트

`update-dart.yml`은 UTC 기준 월말 날짜에 실행된 뒤 **Asia/Seoul 기준 날짜가 1일인지 검사**합니다. 따라서 한국시간 매월 1일에만 DART 수집·분석·커밋·Pages 배포를 수행합니다. GitHub Actions의 스케줄 실행은 플랫폼 사정에 따라 지연될 수 있으므로 수동 `workflow_dispatch`도 제공합니다.

## 폴더 구조

```text
JS_DEEPNOID/
├─ .github/workflows/
│  ├─ update-dart.yml
│  └─ pages.yml
├─ agent/
│  ├─ dart_client.py
│  ├─ collect.py
│  ├─ analyze.py
│  └─ build_dashboard.py
├─ dashboard/
│  ├─ index.html
│  └─ dashboard.json
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ reports/
├─ config.json
├─ requirements.txt
└─ README.md
```

## 원문 보고서

수집 단계에서는 DART 접수번호를 기준으로 원문을 보관하고, 원문 링크/메타데이터도 `data/raw/reports.json`에 저장합니다. 원문 다운로드가 제공되지 않는 과거 자료는 오류로 간주하지 않고 메타데이터를 보존합니다.

## 데이터 해석 주의

OpenDART가 제공하는 구조화 재무데이터는 원 공시서류에서 추출된 값입니다. 금융감독원도 제공 데이터의 정확성·완전성을 보장하지 않으며 원문 공시와의 확인을 안내하고 있으므로, 분석 결과를 사용할 때는 원문 보고서를 함께 확인하세요.
