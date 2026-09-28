from __future__ import annotations
import json, math
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "financial_accounts.csv"
OUT = ROOT / "data" / "processed"

ALIASES = {
    "assets": ["자산총계"], "current_assets": ["유동자산"], "noncurrent_assets": ["비유동자산"],
    "liabilities": ["부채총계"], "current_liabilities": ["유동부채"], "noncurrent_liabilities": ["비유동부채"],
    "equity": ["자본총계"], "revenue": ["매출액", "영업수익"], "cogs": ["매출원가"],
    "gross_profit": ["매출총이익"], "operating_income": ["영업이익", "영업손익"],
    "pretax_income": ["법인세비용차감전순이익", "법인세차감전순이익"],
    "net_income": ["당기순이익", "당기순손익"], "cfo": ["영업활동현금흐름"],
    "capex_ppe": ["유형자산의 취득"], "capex_intangible": ["무형자산의 취득"]
}

def first_value(g, aliases, field="thstrm_amount"):
    for a in aliases:
        x = g[g.account_nm.eq(a)]
        if not x.empty:
            # Prefer total rows without account_detail/member dimensions.
            x2 = x[x.account_detail.fillna("").eq("")]
            if not x2.empty: x = x2
            v = x.iloc[0][field]
            if pd.notna(v): return float(v)
    return None

def safe(a,b):
    return None if b in (None,0) or pd.isna(b) or pd.isna(a) else a/b

def add_ratios(r):
    rev=r.get("revenue"); op=r.get("operating_income"); ni=r.get("net_income")
    assets=r.get("assets"); eq=r.get("equity"); liab=r.get("liabilities")
    ca=r.get("current_assets"); cl=r.get("current_liabilities"); cfo=r.get("cfo")
    r["operating_margin_pct"] = safe(op,rev)*100 if safe(op,rev) is not None else None
    r["net_margin_pct"] = safe(ni,rev)*100 if safe(ni,rev) is not None else None
    r["debt_ratio_pct"] = safe(liab,eq)*100 if safe(liab,eq) is not None else None
    r["equity_ratio_pct"] = safe(eq,assets)*100 if safe(eq,assets) is not None else None
    r["current_ratio_pct"] = safe(ca,cl)*100 if safe(ca,cl) is not None else None
    r["asset_turnover_x"] = safe(rev,assets)
    r["roe_pct"] = safe(ni,eq)*100 if safe(ni,eq) is not None else None
    r["roa_pct"] = safe(ni,assets)*100 if safe(ni,assets) is not None else None
    r["cfo_to_revenue_pct"] = safe(cfo,rev)*100 if safe(cfo,rev) is not None else None
    return r

def extract_periods(df):
    rows=[]
    for (year,period), g in df.groupby(["year","period"], sort=True):
        r={"year":int(year),"period":period}
        for key, aliases in ALIASES.items(): r[key]=first_value(g,aliases)
        # For IS, thstrm_add_amount is cumulative in interim reports. Balance sheet uses thstrm_amount.
        if period in ("half_year","quarterly_q1","quarterly_q3"):
            for key in ["revenue","cogs","gross_profit","operating_income","pretax_income","net_income","cfo","capex_ppe","capex_intangible"]:
                for aliases in [ALIASES[key]]:
                    r[key]=first_value(g,aliases,"thstrm_add_amount") or r[key]
        r=add_ratios(r); rows.append(r)
    return pd.DataFrame(rows)

def quarterlyize(periods):
    rows=[]
    for y,g in periods.groupby("year"):
        g=g.sort_values("period")
        ann=g[g.period.eq("annual")]
        q1=g[g.period.eq("quarterly_q1")]
        h=g[g.period.eq("half_year")]
        q3=g[g.period.eq("quarterly_q3")]
        # balance sheet values remain period-end; income/cashflow are derived as quarter deltas.
        for label, src, prev in [("Q1",q1,None),("Q2",h,q1),("Q3",q3,h),("Q4",ann,q3)]:
            if src.empty: continue
            base=src.iloc[0].to_dict(); base["period"] = label
            if prev is not None and not prev.empty:
                p=prev.iloc[0]
                for k in ["revenue","cogs","gross_profit","operating_income","pretax_income","net_income","cfo","capex_ppe","capex_intangible"]:
                    if pd.notna(base.get(k)) and pd.notna(p.get(k)): base[k]=base[k]-p[k]
            base=add_ratios(base); rows.append(base)
    return pd.DataFrame(rows)

def main():
    df=pd.read_csv(DATA)
    periods=extract_periods(df)
    annual=periods[periods.period.eq("annual")].copy()
    half=periods[periods.period.eq("half_year")].copy()
    q=quarterlyize(periods)
    # Growth fields
    for frame in (annual,half,q):
        frame.sort_values(["year","period"],inplace=True)
        frame["revenue_growth_pct"]=frame["revenue"].pct_change()*100
        frame["asset_growth_pct"]=frame["assets"].pct_change()*100
    def dump(name, frame): frame.to_csv(OUT/name,index=False,encoding="utf-8-sig")
    dump("annual.csv",annual); dump("half_year.csv",half); dump("quarterly.csv",q)
    latest={}
    for name,frame in [("annual",annual),("half_year",half),("quarterly",q)]:
        latest[name]=frame.tail(1).replace({float('nan'):None}).to_dict(orient="records")
    payload={"company":{"name":"딥노이드","stock_code":"315640"},"updated_at":pd.Timestamp.utcnow().isoformat(),"annual":annual.replace({float('nan'):None}).to_dict(orient="records"),"half_year":half.replace({float('nan'):None}).to_dict(orient="records"),"quarterly":q.replace({float('nan'):None}).to_dict(orient="records")}
    (OUT/"dashboard.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print("Analysis complete")
if __name__ == "__main__": main()
