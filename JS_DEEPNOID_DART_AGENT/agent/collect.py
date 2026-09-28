from __future__ import annotations
import json, re, sys
from pathlib import Path
from datetime import date
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dart_client import CONFIG, DartError, discover_reports, financial_statement, download_original

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "data" / "reports"


def num(v):
    if v is None or v == "": return None
    s = str(v).replace(",", "").strip()
    if s in {"-", "—", "nan", "None"}: return None
    try: return float(s)
    except ValueError: return None

def normalize_accounts(rows):
    out = []
    for x in rows:
        out.append({
            "sj_div": x.get("sj_div"), "sj_nm": x.get("sj_nm"),
            "account_id": x.get("account_id"), "account_nm": x.get("account_nm"),
            "account_detail": x.get("account_detail"),
            "thstrm_amount": num(x.get("thstrm_amount")),
            "thstrm_add_amount": num(x.get("thstrm_add_amount")),
            "frmtrm_amount": num(x.get("frmtrm_amount")),
            "frmtrm_q_amount": num(x.get("frmtrm_q_amount")),
            "bfefrmtrm_amount": num(x.get("bfefrmtrm_amount"))
        })
    return out

def main():
    start = int(CONFIG["company"]["start_year"])
    end = date.today().year
    RAW.mkdir(parents=True, exist_ok=True); PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    reports = discover_reports(start, end)
    (RAW / "reports.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    if CONFIG["dart"].get("download_original_reports"):
        for r in reports:
            rn = r.get("report_nm", "").replace("/", "_")
            if not rn: continue
            target = REPORTS / f"{r['rcept_no']}_{rn}.zip"
            if not target.exists() and not target.with_suffix(".xml").exists():
                try: download_original(r["rcept_no"], target)
                except Exception as e: print(f"report download skipped {r['rcept_no']}: {e}")

    records = []
    for year in range(max(2015, start), end + 1):
        for period, code in CONFIG["dart"]["report_codes"].items():
            try:
                rows = normalize_accounts(financial_statement(year, code))
            except DartError as e:
                # Some report types/years do not exist; keep the run alive.
                print(f"skip {year} {period}: {e}")
                continue
            if not rows: continue
            path = RAW / f"{year}_{period}.json"
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            for row in rows:
                row.update({"year": year, "period": period})
                records.append(row)

    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("No financial data returned by OpenDART.")
    df.to_csv(PROCESSED / "financial_accounts.csv", index=False, encoding="utf-8-sig")
    print(f"Collected {len(df):,} account rows.")

if __name__ == "__main__": main()
