# DEEPNOID DART Financial Agent

DART(OpenDART)에서 딥노이드(315640, DART corp_code 01344831)의 정기보고서를 수집하고, 재무수치를 표준화한 뒤 재무비율을 계산하고, 정적 HTML Dashboard를 생성하여 GitHub Pages에 배포하는 MVP입니다.

## 구조

- `src/dart_collector.py` : DART API에서 공시검색/재무제표/원문 ZIP 수집
- `src/financial_engine.py` : 핵심 재무수치 및 재무비율 계산
- `src/build_dashboard.py` : `data/financials.csv`, `data/ratios.csv` → `dashboard/index.html`
- `.github/workflows/update.yml` : 매일 자동 실행 + 수동 실행
- `reports/` : DART 원문 ZIP 저장
- `data/` : 분석용 CSV/JSON
- `dashboard/` : GitHub Pages 정적 대시보드

## 분석 지표

첨부한 `재무제표 및 재무비율 실무 가이드`를 기준으로 다음을 지원합니다.

- 재무상태: 총자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 총부채, 이자부차입금, 자본총계
- 손익: 매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익, EBITDA
- 현금흐름: 영업활동현금흐름, 투자활동현금흐름, 재무활동현금흐름, CAPEX, FCF, 순차입금
- 비율: 매출총이익률, 영업이익률, 순이익률, EBITDA 마진, ROA, ROE, ROIC, 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, DPO, CCC, 매출증가율, CFO/순이익

※ DART XBRL에서 직접 제공되지 않는 EBITDA/CAPEX/ROIC/DSO/DIO/DPO는 계정 매핑 가능 범위에서 계산하며, 산출 불가 시 빈 값으로 둡니다. FCF는 가이드 정의인 CFO - CAPEX를 사용합니다.

## 1. API Key

OpenDART에서 발급받은 40자리 인증키를 GitHub Repository Secret `DART_API_KEY`로 등록합니다.

GitHub: Repository → Settings → Secrets and variables → Actions → New repository secret

이 프로젝트는 API 키를 코드나 Git에 넣지 않습니다.

## 2. Repository

현재 사용자가 지정한 GitHub 계정은 `almor70111`입니다. GitHub URL이 프로필 URL인 경우 실제 저장소 이름은 아직 확정되지 않았으므로 아래 Secret/Variable을 사용합니다.

- Repository 예: `almor70111/deepnoid-dart-agent`
- Pages: Settings → Pages → Build and deployment → Source: GitHub Actions

## 3. 로컬 실행

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
set DART_API_KEY=발급받은키
python src/dart_collector.py
python src/financial_engine.py
python src/build_dashboard.py
```

생성물:

- `data/financials.csv`
- `data/ratios.csv`
- `data/metadata.json`
- `reports/YYYY/report_RCPNO.zip`
- `dashboard/index.html`

## 4. GitHub Actions

`update.yml`은 매일 UTC 17:00(한국시간 02:00)에 실행됩니다. 수동 실행도 가능합니다.

새로운 정기보고서가 DART에 올라오면 공시검색 결과를 확인하고 원문/재무데이터를 다시 수집합니다. 이후 CSV와 Dashboard를 커밋하고 GitHub Pages로 배포합니다.

## 5. 주의

DART는 정기보고서의 XBRL 재무정보와 공시 원문을 API로 제공합니다. 이 프로젝트의 계산식은 첨부 실무 가이드의 정의를 따르되, 계정명/표시체계가 보고서마다 달라지는 항목은 매핑 테이블을 보완해야 합니다.
