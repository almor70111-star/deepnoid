import json, html
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/'data/financials.csv')
rs=pd.read_csv(ROOT/'data/ratios.csv')
latest=df.iloc[-1]
labels=json.dumps(df['year'].astype(int).tolist(),ensure_ascii=False)
series=lambda col: json.dumps([None if pd.isna(x) else float(x) for x in df[col]],ensure_ascii=False)

def money(v): return '-' if pd.isna(v) else f'{v:,.0f}'
def pct(v): return '-' if pd.isna(v) else f'{v*100:.1f}%'

cards=[
('매출액',money(latest.revenue)),('영업이익',money(latest.operating_income)),('당기순이익',money(latest.net_income)),('영업현금흐름(CFO)',money(latest.cfo)),
('ROE',pct(latest.roe)),('ROA',pct(latest.roa)),('영업이익률',pct(latest.operating_margin)),('부채비율',pct(latest.debt_ratio))]
card_html=''.join(f'<div class="card"><div>{html.escape(k)}</div><strong>{html.escape(v)}</strong></div>' for k,v in cards)
rows=''.join('<tr>'+''.join(f'<td>{html.escape(str(x))}</td>' for x in [int(r.year),money(r.revenue),money(r.operating_income),money(r.net_income),money(r.total_assets),money(r.total_liabilities),money(r.equity),money(r.cfo),pct(r.operating_margin),pct(r.net_margin),pct(r.roe),pct(r.roa),pct(r.debt_ratio)])+'</tr>' for _,r in df.sort_values('year',ascending=False).iterrows())
page=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>딥노이드 DART Financial Dashboard</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>body{{font-family:Arial,sans-serif;margin:0;background:#f6f7fb;color:#172033}}header{{padding:28px 5%;background:#172033;color:white}}main{{padding:24px 5%;max-width:1400px;margin:auto}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}.card,.panel{{background:white;border-radius:12px;padding:18px;box-shadow:0 2px 12px #0001;margin-bottom:18px}}.card strong{{display:block;font-size:24px;margin-top:8px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:9px;border-bottom:1px solid #eee;text-align:right}}th:first-child,td:first-child{{text-align:center}}.note{{color:#667085;font-size:13px}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><header><h1>DEEPNOID DART Financial Dashboard</h1><div>딥노이드 · 315640 · OpenDART 기반 자동 업데이트</div></header><main><div class="cards">{card_html}</div><div class="grid"><section class="panel"><h2>매출 / 영업이익 / 순이익</h2><canvas id="profit"></canvas></section><section class="panel"><h2>수익성 추이</h2><canvas id="margin"></canvas></section></div><section class="panel"><h2>연도별 핵심 재무수치</h2><table><thead><tr><th>연도</th><th>매출</th><th>영업이익</th><th>순이익</th><th>자산</th><th>부채</th><th>자본</th><th>CFO</th><th>영업이익률</th><th>순이익률</th><th>ROE</th><th>ROA</th><th>부채비율</th></tr></thead><tbody>{rows}</tbody></table></section><section class="panel"><h2>산출 기준</h2><p class="note">첨부 실무 가이드의 지표 체계를 반영했습니다. DART 계정명/보고서 구조에 따라 EBITDA·CAPEX·ROIC·DPO 등은 산출 불가할 수 있습니다. ROIC는 MVP에서 영업이익×(1-22%) / (자본+이자부차입금-현금)의 단순 proxy입니다. DSO/DIO는 현재 MVP에서 매출을 분모로 한 단순화된 일수이며, DPO는 매입액 계정 매핑을 추가하면 정교화할 수 있습니다.</p></section></main><script>const labels={labels};new Chart(document.getElementById('profit'),{{type:'line',data:{{labels,datasets:[{{label:'매출',data:{series('revenue')} }},{{label:'영업이익',data:{series('operating_income')} }},{{label:'순이익',data:{series('net_income')} }}]}},options:{{responsive:true}}}});new Chart(document.getElementById('margin'),{{type:'line',data:{{labels,datasets:[{{label:'영업이익률',data:{series('operating_margin')} }},{{label:'순이익률',data:{series('net_margin')} }},{{label:'ROE',data:{series('roe')} }},{{label:'ROA',data:{series('roa')} }}]}},options:{{responsive:true,scales:{{y:{{ticks:{{callback:v=>(v*100).toFixed(0)+'%'}}}}}}}}}});</script></body></html>'''
(ROOT/'dashboard').mkdir(exist_ok=True)
(ROOT/'dashboard/index.html').write_text(page,encoding='utf-8')
print('dashboard/index.html generated')
