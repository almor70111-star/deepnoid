import io, json, os, re, zipfile
from datetime import date, timedelta
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
API = 'https://opendart.fss.or.kr/api'
KEY = os.getenv('DART_API_KEY')
if not KEY:
    raise SystemExit('DART_API_KEY 환경변수가 없습니다.')

S = requests.Session()
S.headers.update({'User-Agent': 'deepnoid-dart-agent/1.0'})


def get_json(endpoint, params):
    p = dict(params); p['crtfc_key'] = KEY
    r = S.get(f'{API}/{endpoint}', params=p, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get('status') != '000':
        raise RuntimeError(f'DART {endpoint}: {data.get("status")} {data.get("message")}')
    return data


def discover_regular_filings(days=30):
    end = date.today()
    start = end - timedelta(days=days)
    data = get_json('list.json', {
        'corp_code': CFG['corp_code'],
        'bgn_de': start.strftime('%Y%m%d'),
        'end_de': end.strftime('%Y%m%d'),
        'page_no': 1, 'page_count': 100
    })
    rows = []
    for x in data.get('list', []):
        nm = x.get('report_nm', '')
        if any(k in nm for k in ['사업보고서', '반기보고서', '분기보고서']):
            rows.append(x)
    return rows


def fetch_financials(year, reprt_code):
    return get_json('fnlttSinglAcntAll.json', {
        'corp_code': CFG['corp_code'], 'bsns_year': str(year),
        'reprt_code': reprt_code, 'fs_div': 'C'
    })


def download_original(rcept_no, year):
    url = f'{API}/document.xml'
    r = S.get(url, params={'crtfc_key': KEY, 'rcept_no': rcept_no}, timeout=120)
    if r.status_code != 200 or not r.content.startswith(b'PK'):
        raise RuntimeError(f'원문 ZIP 다운로드 실패: {r.status_code}')
    outdir = ROOT / 'reports' / str(year)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f'report_{rcept_no}.zip'
    path.write_bytes(r.content)
    return path


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    meta = {'corp_name': CFG['corp_name'], 'corp_code': CFG['corp_code'], 'stock_code': CFG['stock_code'], 'filings': []}
    rows = discover_regular_filings(CFG['recent_days'])
    # Always refresh the configured annual history, so a newly corrected filing can be reflected.
    for y in range(date.today().year - 1, date.today().year - CFG['years_back'] - 1, -1):
        try:
            fin = fetch_financials(y, CFG['report_codes']['ANNUAL'])
            save_json(ROOT / 'data' / 'raw' / f'financials_{y}_annual.json', fin)
        except Exception as e:
            print(f'[WARN] {y} annual: {e}')

    seen = set()
    for x in rows:
        rcp = x.get('rcept_no')
        if not rcp or rcp in seen: continue
        seen.add(rcp)
        try:
            year = int(x.get('report_nm','')[-5:-1]) if re.search(r'\d{4}', x.get('report_nm','')) else date.today().year
        except Exception:
            year = date.today().year
        # report year from filing metadata if available
        try:
            fin_year = int(x.get('rcept_dt','')[:4])
        except Exception:
            fin_year = year
        save_json(ROOT / 'data' / 'raw' / f'filing_{rcp}.json', x)
        try:
            download_original(rcp, fin_year)
        except Exception as e:
            print(f'[WARN] original {rcp}: {e}')
        meta['filings'].append(x)
    save_json(ROOT / 'data' / 'metadata.json', meta)
    print(f'Collected {len(meta["filings"])} recent regular filings.')

if __name__ == '__main__':
    main()
