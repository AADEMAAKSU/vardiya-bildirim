import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import hashlib
from datetime import datetime

# ================== AYARLAR ==================

LOGIN_URL = "https://gozenconnect.gohub.aero/accounts/login/"
AUTHORIZE_URL = (
    "https://gozenconnect.gohub.aero/api/v1/authorize/"
    "?client_id=gozensystems.gss.gohub_ui"
    "&response_type=code"
    "&redirect_uri=https://api-gss.gohub.aero/testing/redirect-saha"
)

TOKEN_URL = "https://api-gss.gohub.aero/auth/with-code"

# ❗ SADECE CORRESPONDENCE ID SABİT
CORRESPONDENCE_ID = "638463"

LIST_ATTACHMENTS_URL = (
    f"https://api-gss.gohub.aero/correspondence/{CORRESPONDENCE_ID}"
)

DOWNLOAD_BASE_URL = (
    f"https://api-gss.gohub.aero/correspondence/{CORRESPONDENCE_ID}/attachment"
)

OUTPUT_FILE = "vardiya.xlsx"

USERNAME = os.environ["GSS_USERNAME"]
PASSWORD = os.environ["GSS_PASSWORD"]

# ============================================

session = requests.Session()

# 1️⃣ LOGIN → CSRF
login_page = session.get(LOGIN_URL)
soup = BeautifulSoup(login_page.text, "html.parser")
csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

# 2️⃣ LOGIN POST
payload = {
    "csrfmiddlewaretoken": csrf,
    "username": USERNAME,
    "password": PASSWORD,
    "next": AUTHORIZE_URL,
}

headers = {"Referer": LOGIN_URL}

login_response = session.post(
    LOGIN_URL, data=payload, headers=headers, allow_redirects=True
)

# 3️⃣ REDIRECT → CODE
code = None
for r in login_response.history + [login_response]:
    if "code=" in r.url:
        parsed = urlparse(r.url)
        qs = parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
            break

if not code:
    raise Exception("❌ Authorization code alınamadı")

# 4️⃣ CODE → ACCESS TOKEN
token_response = session.get(TOKEN_URL, params={"code": code})
if token_response.status_code != 200:
    raise Exception("❌ Token alınamadı")

access_token = token_response.json().get("access_token")
if not access_token:
    raise Exception("❌ Access token bulunamadı")

auth_headers = {"Authorization": f"Bearer {access_token}"}

# 5️⃣ CORRESPONDENCE → ATTACHMENT LİSTESİ
attachments_response = session.get(
    LIST_ATTACHMENTS_URL, headers=auth_headers
)

if attachments_response.status_code != 200:
    raise Exception("❌ Attachment listesi alınamadı")

attachments = attachments_response.json().get("attachments", [])

if not attachments:
    raise Exception("❌ Hiç attachment bulunamadı")

# 6️⃣ EN GÜNCEL ATTACHMENT'I SEÇ
# createdAt / uploadedAt / id büyük olan en yeni kabul edilir
latest_attachment = sorted(
    attachments,
    key=lambda x: (
        x.get("createdAt") or "",
        x.get("id") or 0
    ),
    reverse=True
)[0]

attachment_id = latest_attachment["id"]
filename = latest_attachment.get("fileName", "vardiya.xlsx")

print(f"📎 Seçilen attachment ID: {attachment_id}")
print(f"📄 Dosya adı (server): {filename}")

# 7️⃣ DOSYAYI İNDİR
download_url = f"{DOWNLOAD_BASE_URL}/{attachment_id}"
file_response = session.get(download_url, headers=auth_headers)

if file_response.status_code != 200:
    raise Exception(
        f"❌ Dosya indirilemedi: {file_response.status_code}"
    )

with open(OUTPUT_FILE, "wb") as f:
    f.write(file_response.content)

# 8️⃣ KANIT LOG
file_hash = hashlib.md5(file_response.content).hexdigest()
print("✅ DOSYA İNDİRİLDİ")
print("📦 HASH:", file_hash)
print("📦 BOYUT:", len(file_response.content))
print("🕒 ZAMAN (UTC):", datetime.utcnow())
