import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import hashlib
from datetime import datetime
import re

# ================== AYARLAR ==================

LOGIN_URL = "https://gozenconnect.gohub.aero/accounts/login/"
AUTHORIZE_URL = (
    "https://gozenconnect.gohub.aero/api/v1/authorize/"
    "?client_id=gozensystems.gss.gohub_ui"
    "&response_type=code"
    "&redirect_uri=https://api-gss.gohub.aero/testing/redirect-saha"
)

TOKEN_URL = "https://api-gss.gohub.aero/auth/with-code"

# 🔴 WEB SAYFASI (MESAJLARIM)
MESSAGES_PAGE = "https://saha.gohub.aero/#!/mesajlarim"

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

# 5️⃣ MESAJLAR SAYFASINI ÇEK
page = session.get(MESSAGES_PAGE, headers=auth_headers)
if page.status_code != 200:
    raise Exception("❌ Mesajlar sayfası alınamadı")

html = page.text

# 6️⃣ TÜM ATTACHMENT LINKLERİNİ BUL
links = re.findall(
    r'/correspondence/\d+/attachment/\d+',
    html
)

if not links:
    raise Exception("❌ Attachment linki bulunamadı")

# 7️⃣ EN SON (EN GÜNCEL) LİNK
latest_link = links[-1]
download_url = "https://api-gss.gohub.aero" + latest_link

print("📎 Kullanılan link:", download_url)

# 8️⃣ DOSYAYI İNDİR
file_response = session.get(download_url, headers=auth_headers)
if file_response.status_code != 200:
    raise Exception(f"❌ Dosya indirilemedi: {file_response.status_code}")

with open(OUTPUT_FILE, "wb") as f:
    f.write(file_response.content)

# 9️⃣ KANIT LOG
file_hash = hashlib.md5(file_response.content).hexdigest()
print("✅ DOSYA İNDİRİLDİ")
print("📦 HASH:", file_hash)
print("📦 BOYUT:", len(file_response.content))
print("🕒 ZAMAN (UTC):", datetime.utcnow())
