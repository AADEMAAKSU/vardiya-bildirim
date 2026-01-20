import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

LOGIN_URL = "https://gozenconnect.gohub.aero/accounts/login/"
AUTHORIZE_URL = "https://gozenconnect.gohub.aero/api/v1/authorize/?client_id=gozensystems.gss.gohub_ui&response_type=code&redirect_uri=https://api-gss.gohub.aero/testing/redirect-saha"
TOKEN_URL = "https://api-gss.gohub.aero/auth/with-code"
DOWNLOAD_URL = "https://api-gss.gohub.aero/correspondence/638463/attachment/42005"

OUTPUT_FILE = "vardiya.xlsx"

USERNAME = os.environ["GSS_USERNAME"]
PASSWORD = os.environ["GSS_PASSWORD"]

session = requests.Session()

# 1️⃣ Login sayfası → CSRF
login_page = session.get(LOGIN_URL)
soup = BeautifulSoup(login_page.text, "html.parser")
csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

# 2️⃣ Login POST
payload = {
    "csrfmiddlewaretoken": csrf,
    "username": USERNAME,
    "password": PASSWORD,
    "next": AUTHORIZE_URL
}

headers = {
    "Referer": LOGIN_URL
}

login_response = session.post(
    LOGIN_URL,
    data=payload,
    headers=headers,
    allow_redirects=True
)

# 3️⃣ Redirect zincirinden CODE yakala
code = None
for r in login_response.history + [login_response]:
    if "code=" in r.url:
        parsed = urlparse(r.url)
        qs = parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
            break

if not code:
    raise Exception("Authorization code alınamadı")

# 4️⃣ CODE → ACCESS TOKEN
token_response = session.get(
    TOKEN_URL,
    params={"code": code}
)

if token_response.status_code != 200:
    raise Exception("Token alınamadı")

token_json = token_response.json()
access_token = token_json.get("access_token")

if not access_token:
    raise Exception("Access token bulunamadı")

# 5️⃣ Dosyayı Bearer token ile indir
file_headers = {
    "Authorization": f"Bearer {access_token}"
}

file_response = session.get(DOWNLOAD_URL, headers=file_headers)

if file_response.status_code != 200:
    raise Exception(f"Dosya indirilemedi: {file_response.status_code}")

with open(OUTPUT_FILE, "wb") as f:
    f.write(file_response.content)

print("✅ Login, token alma ve dosya indirme başarılı")
