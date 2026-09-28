from __future__ import annotations
import json, os, time, zipfile, io
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE = CONFIG["dart"]["base_url"]
KEY = os.environ.get("DART_API_KEY", "").strip()

class DartError(RuntimeError):
    pass

def require_key():
    if not KEY or len(KEY) != 40:
        raise DartError("DART_API_KEY must be a valid 40-character OpenDART API key.")

def get(endpoint: str, params: dict, timeout=60):
    require_key()
    params = {**params, "crtfc_key": KEY}
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
    r.raise_for_status()
    return r

def get_json(endpoint: str, params: dict):
    data = get(endpoint, params).json()
    if data.get("status") != "000":
        raise DartError(f"OpenDART {data.get('status')}: {data.get('message')}")
    return data

def sleep():
    time.sleep(0.15)

def discover_reports(year_start: int, year_end: int):
    rows = []
    for year in range(year_start, year_end + 1):
        data = get_json("list.json", {
            "corp_code": CONFIG["company"]["corp_code"],
            "bgn_de": f"{year}0101",
            "end_de": f"{year}1231",
            "pblntf_ty": "A",
            "last_reprt_at": "Y",
            "page_count": 100
        })
        for item in data.get("list", []):
            name = item.get("report_nm", "")
            if any(x in name for x in ("사업보고서", "반기보고서", "분기보고서")):
                item["report_period_year"] = year
                rows.append(item)
        sleep()
    return rows

def financial_statement(year: int, reprt_code: str):
    return get_json("fnlttSinglAcntAll.json", {
        "corp_code": CONFIG["company"]["corp_code"],
        "bsns_year": str(year),
        "reprt_code": reprt_code,
        "fs_div": CONFIG["financial_statement"]["fs_div"]
    }).get("list", [])

def download_original(rcept_no: str, out_path: Path):
    # OpenDART's original-report endpoint returns a ZIP archive in standard API usage.
    require_key()
    r = get("document.xml", {"rcept_no": rcept_no}, timeout=120)
    content_type = (r.headers.get("content-type") or "").lower()
    if "zip" in content_type or r.content[:2] == b"PK":
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return True
    # Keep the raw response for troubleshooting rather than silently discarding it.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.with_suffix(".xml").write_bytes(r.content)
    return False
