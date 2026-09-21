import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
RAW = ROOT/'data'/'raw'

# DART account-name aliases. Add aliases here if a future XBRL taxonomy uses a different label.
ALIASES = {
 'total_assets':['자산총계'], 'cash':['현금및현금성자산','현금및현금성자산및현금성자산'],
 'receivables':['매출채권','매출채권및기타채권'], 'inventory':['재고자산'], 'ppe':['유형자산'],
 'current_assets':['유동자산'], 'current_liabilities':['유동부채'], 'total_liabilities':['부채총계'],
 'borrowings':['단기차입금','장기차입금','유동성장기차입금','사채','장기차입부채'], 'equity':['자본총계'],
 'revenue':['매출액','수익(매출액)','영업수익'], 'gross_profit':['매출총이익'],
 'sga':['판매비와관리비'], 'operating_income':['영업이익','영업이익(손실)'],
 'pretax_income':['법인세비용차감전순이익','법인세비용차감전순이익(손실)'],
 'net_income':['당기순이익','당기순이익(손실)'], 'controlling_net_income':['지배기업의 소유주에게 귀속되는 당기순이익','지배기업 소유주지분 순이익'],
 'cfo':['영업활동현금흐름','영업활동으로 인한 현금흐름'],
 'cfi':['투자활동현금흐름','투자활동으로 인한 현금흐름'],
 'cff':['재무활동현금흐름','재무활동으로 인한 현금흐름'],
 'interest_expense':['이자비용','금융비용'],
 'depreciation':['감가상각비'], 'amortization':['무형자산상각비']
}


def num(x):
    if x is None: return None
    s = str(x).replace(',','').strip()
    if s in ('','-','nan','None'): return None
    s = s.replace('(','-').replace(')','')
    try: return float(s)
    except: return None


def pick(df, aliases, col):
    m = df[df['account_nm'].isin(aliases)]
    if m.empty:
        # looser matching, but avoid overly broad matches
        for a in aliases:
            m = df[df['account_nm'].astype(str).str.replace(' ','',regex=False).str.contains(re.escape(a.replace(' ','')), regex=True, na=False)]
            if not m.empty: break
    if m.empty: return None
    return num(m.iloc[0].get(col))


def load_year(year):
    p = RAW/f'financials_{year}_annual.json'
    if not p.exists(): return None
    obj = json.loads(p.read_text(encoding='utf-8'))
    rows = obj.get('list', [])
    if not rows: return None
    df = pd.DataFrame(rows)
    # DART annual values normally expose thstrm, frmtrm, bfefrmtrm. Use current period.
    out = {'year': year}
    for k, aliases in ALIASES.items(): out[k] = pick(df, aliases, 'thstrm_amount')
    # DART all-financials sometimes uses thstrm_amount; fallback to amount columns.
    for k in list(out):
        if k == 'year': continue
        if out[k] is None:
            out[k] = pick(df, ALIASES[k], 'thstrm')
    out['capex'] = None
    # CAPEX approximation from cash-flow acquisition of tangible/intangible assets.
    for label in ['유형자산의 취득','유형자산 취득','무형자산의 취득','무형자산 취득']:
        m = df[df['account_nm'].astype(str).str.contains(label, regex=False, na=False)]
        if not m.empty:
            v = num(m.iloc[0].get('thstrm_amount'))
            if v is not None: out['capex'] = (out['capex'] or 0) + abs(v)
    out['net_debt'] = (out['borrowings'] or 0) - (out['cash'] or 0) if out['borrowings'] is not None and out['cash'] is not None else None
    out['ebitda'] = None
    if out['operating_income'] is not None:
        out['ebitda'] = out['operating_income'] + (out['depreciation'] or 0) + (out['amortization'] or 0)
    out['fcf'] = out['cfo'] - out['capex'] if out['cfo'] is not None and out['capex'] is not None else None
    return out


def safe_div(a,b): return None if a is None or b in (None,0) else a/b


def main():
    records=[]
    for p in sorted(RAW.glob('financials_*_annual.json')):
        y=int(p.stem.split('_')[1]); x=load_year(y)
        if x: records.append(x)
    if not records: raise SystemExit('재무데이터가 없습니다. 먼저 dart_collector.py를 실행하세요.')
    df=pd.DataFrame(records).sort_values('year')
    for c in ['gross_margin','operating_margin','net_margin','ebitda_margin','roa','roe','roic','current_ratio','quick_ratio','debt_ratio','equity_ratio','borrowing_dependency','interest_coverage','net_debt_ebitda','asset_turnover','dso','dio','dpo','ccc','revenue_growth','cfo_net_income']:
        df[c]=None
    for i,row in df.iterrows():
        prev=df.loc[i-1] if i>df.index.min() else None
        avg_assets=(row.total_assets + prev.total_assets)/2 if prev is not None and pd.notna(row.total_assets) and pd.notna(prev.total_assets) else row.total_assets
        avg_eq=(row.equity + prev.equity)/2 if prev is not None and pd.notna(row.equity) and pd.notna(prev.equity) else row.equity
        df.at[i,'gross_margin']=safe_div(row.gross_profit,row.revenue)
        df.at[i,'operating_margin']=safe_div(row.operating_income,row.revenue)
        df.at[i,'net_margin']=safe_div(row.net_income,row.revenue)
        df.at[i,'ebitda_margin']=safe_div(row.ebitda,row.revenue)
        df.at[i,'roa']=safe_div(row.net_income,avg_assets)
        df.at[i,'roe']=safe_div(row.net_income,avg_eq)
        # Simple NOPAT/Invested capital proxy; explicitly marked as proxy in dashboard.
        nopat=row.operating_income*0.78 if row.operating_income is not None else None
        invested=(row.equity + row.borrowings - row.cash) if all(pd.notna(x) for x in [row.equity,row.borrowings,row.cash]) else None
        df.at[i,'roic']=safe_div(nopat,invested)
        df.at[i,'current_ratio']=safe_div(row.current_assets,row.current_liabilities)
        quick=(row.current_assets-row.inventory) if row.current_assets is not None and row.inventory is not None else None
        df.at[i,'quick_ratio']=safe_div(quick,row.current_liabilities)
        df.at[i,'debt_ratio']=safe_div(row.total_liabilities,row.equity)
        df.at[i,'equity_ratio']=safe_div(row.equity,row.total_assets)
        df.at[i,'borrowing_dependency']=safe_div(row.borrowings,row.total_assets)
        df.at[i,'interest_coverage']=safe_div(row.operating_income,row.interest_expense)
        df.at[i,'net_debt_ebitda']=safe_div(row.net_debt,row.ebitda)
        df.at[i,'asset_turnover']=safe_div(row.revenue,avg_assets)
        df.at[i,'revenue_growth']=safe_div(row.revenue,prev.revenue)-1 if prev is not None and row.revenue is not None and prev.revenue not in (None,0) else None
        df.at[i,'cfo_net_income']=safe_div(row.cfo,row.net_income)
        # Working-capital days require COGS / purchases. Use revenue as a conservative fallback only when necessary.
        if row.revenue:
            df.at[i,'dso']=safe_div(row.receivables,row.revenue)*365 if row.receivables is not None else None
            df.at[i,'dio']=safe_div(row.inventory,row.revenue)*365 if row.inventory is not None else None
        df.at[i,'dpo']=None
        if df.at[i,'dso'] is not None and df.at[i,'dio'] is not None:
            df.at[i,'ccc']=df.at[i,'dso']+df.at[i,'dio']-(df.at[i,'dpo'] or 0)
    # Keep numeric amounts in DART's reported unit (normally KRW million for this endpoint).
    df.to_csv(ROOT/'data'/'financials.csv',index=False,encoding='utf-8-sig')
    ratio_cols=['year','gross_margin','operating_margin','net_margin','ebitda_margin','roa','roe','roic','current_ratio','quick_ratio','debt_ratio','equity_ratio','borrowing_dependency','interest_coverage','net_debt_ebitda','asset_turnover','dso','dio','dpo','ccc','revenue_growth','cfo_net_income']
    df[ratio_cols].to_csv(ROOT/'data'/'ratios.csv',index=False,encoding='utf-8-sig')
    print(df[['year','revenue','operating_income','net_income','cfo','fcf','roe','roa']].to_string(index=False))

if __name__=='__main__': main()
