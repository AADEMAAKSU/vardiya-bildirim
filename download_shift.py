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

NOTIFICATION_API = "https://api-gss.gohub.aero/notification-service"

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

# 4️⃣ CODE → TOKEN
token_response = session.get(TOKEN_URL, params={"code": code})
if token_response.status_code != 200:
    raise Exception("❌ Token alınamadı")

access_token = token_response.json().get("access_token")
if not access_token:
    raise Exception("❌ Access token bulunamadı")

auth_headers = {"Authorization": f"Bearer {access_token}"}

# 5️⃣ NOTIFICATION SERVICE → BİLDİRİMLER
notif_resp = session.get(NOTIFICATION_API, headers=auth_headers)
if notif_resp.status_code != 200:
    raise Exception("❌ Notification API alınamadı")

data = notif_resp.json().get("data", [])
if not data:
    raise Exception("❌ Bildirim bulunamadı")

# 6️⃣ ATTACHMENT OLANLARI BUL
attachments = [
    n for n in data
    if n.get("attachmentId") and n.get("correspondenceId")
]

if not attachments:
    raise Exception("❌ Attachment içeren bildirim yok")

# 7️⃣ EN GÜNCEL BİLDİRİM (ilk sıradaki)
latest = attachments[0]

correspondence_id = latest["correspondenceId"]
attachment_id = latest["attachmentId"]

download_url = (
    f"https://api-gss.gohub.aero/"
    f"correspondence/{correspondence_id}/attachment/{attachment_id}"
)

print("📎 Kullanılan link:", download_url)

# 8️⃣ DOSYAYI İNDİR
file_response = session.get(download_url, headers=auth_headers)
if file_response.status_code != 200:
    raise Exception(f"❌ Dosya indirilemedi: {file_response.status_code}")

with open(OUTPUT_FILE, "wb") as f:
    f.write(file_response.content)

# 9️⃣ KANIT
file_hash = hashlib.md5(file_response.content).hexdigest()
print("✅ DOSYA İNDİRİLDİ")
print("📦 HASH:", file_hash)
print("📦 BOYUT:", len(file_response.content))
print("🕒 ZAMAN (UTC):", datetime.utcnow())
