import requests
import os

# ================= AYARLAR =================

DOWNLOAD_URL = "https://api-gss.gohub.aero/correspondence/638463/attachment/42005"
OUTPUT_FILE = "01 IST INT 16-31 CALISMA PROGRAMI.xlsx"

TOKEN = os.environ["GSS_TOKEN"]

# ===========================================

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

r = requests.get(DOWNLOAD_URL, headers=headers)

if r.status_code != 200:
    raise Exception(f"Dosya indirilemedi: {r.status_code}")

with open(OUTPUT_FILE, "wb") as f:
    f.write(r.content)

print("✅ Vardiya dosyası indirildi")
