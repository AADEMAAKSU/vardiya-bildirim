import requests
import os
from bs4 import BeautifulSoup

LOGIN_URL = "https://gozenconnect.gohub.aero/accounts/login/"
AUTHORIZE_URL = "https://gozenconnect.gohub.aero/api/v1/authorize/?client_id=gozensystems.gss.gohub_ui&response_type=code&redirect_uri=https://api-gss.gohub.aero/testing/redirect-saha"
DOWNLOAD_URL = "https://api-gss.gohub.aero/correspondence/638463/attachment/42005"

OUTPUT_FILE = "vardiya.xlsx"

USERNAME = os.environ["GSS_USERNAME"]
PASSWORD = os.environ["GSS_PASSWORD"]

session = requests.Session()

# 1️⃣ Login sayfasını aç → CSRF al
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

login_response = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True)

# 3️⃣ Redirect sonrası token oluşur → session’da saklanır
# Artık authenticated durumdayız

# 4️⃣ Dosyayı indir
file_response = session.get(DOWNLOAD_URL)

if file_response.status_code != 200:
    raise Exception(f"Dosya indirilemedi: {file_response.status_code}")

with open(OUTPUT_FILE, "wb") as f:
    f.write(file_response.content)

print("✅ Login başarılı, dosya indirildi")
