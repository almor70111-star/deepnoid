from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
site=ROOT/"dashboard"
data=ROOT/"data/processed/dashboard.json"
if not data.exists(): raise SystemExit("dashboard.json not found")
# dashboard reads data/dashboard.json, so copy it into the static site.
shutil.copy2(data,site/"dashboard.json")
print("Dashboard data copied")
