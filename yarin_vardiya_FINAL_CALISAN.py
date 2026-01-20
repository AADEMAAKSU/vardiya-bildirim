import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
import re

# ================== AYARLAR ==================

EXCEL_PATH = "vardiya.xlsx"
STAFF_NAME = "ADEM AKSU"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ============================================


def parse_flights(text: str) -> str:
    """
    İçerik hücresinde birden fazla Flight varsa ayıklar.
    """
    if not text or text.lower() == "nan":
        return ""

    results = []
    parts = re.split(r'(?=Flight)', text)

    for part in parts:
        part = part.strip()
        if not re.search(r'Flight\s*:?', part):
            continue

        flight = re.search(r'Flight\s*:?\s*([A-Z0-9 ]+)', part)
        task = re.search(r'Task\s*:?\s*([A-Z0-9\.\-İIÖŞĞÜÇ ]+)', part)

        block = []
        if flight:
            block.append(f"✈️ Flight: {flight.group(1).strip()}")
        if task:
            block.append(f"🛠 Task: {task.group(1).strip()}")

        if block:
            results.append("\n".join(block))

    return "\n\n".join(results)


async def main():
    # 🇹🇷 TÜRKİYE SAATİ
    now_tr = datetime.now(ZoneInfo("Europe/Istanbul"))
    tomorrow = now_tr + timedelta(days=1)
    target_day = tomorrow.day

    raw = pd.read_excel(EXCEL_PATH, header=None)

    # STAFF satırını bul
    header_row_index = None
    for i in range(len(raw)):
        if str(raw.iloc[i, 0]).strip().upper() == "STAFF":
            header_row_index = i
            break

    if header_row_index is None:
        print("❌ STAFF satırı bulunamadı")
        return

    header_row = raw.iloc[header_row_index]

    # 🎯 Hedef günün sütununu bul
    vardiya_col = None
    for col_idx in range(1, len(header_row)):
        match = re.search(r'\b(\d{1,2})\b', str(header_row[col_idx]))
        if match and int(match.group(1)) == target_day:
            vardiya_col = col_idx
            break

    if vardiya_col is None:
        print("❌ Hedef gün için sütun bulunamadı")
        return

    # Personel satırını bul
    staff_row = None
    for i in range(header_row_index + 1, len(raw)):
        if str(raw.iloc[i, 0]).strip().upper() == STAFF_NAME:
            staff_row = raw.iloc[i]
            break

    if staff_row is None:
        print("❌ Personel bulunamadı")
        return

    # 🧩 Vardiya hücresi
    vardiya_cell = str(staff_row[vardiya_col]).strip()

    # 📋 İçerik hücresini dinamik bul
    icerik_cell = ""
    for col in range(vardiya_col + 1, len(staff_row)):
        cell_text = str(staff_row[col])
        if re.search(r'Flight\s*:?', cell_text, re.IGNORECASE):
            icerik_cell = cell_text.strip()
            break

    # 🧪 DEBUG — içerik bulunamazsa raporla
    debug_info = ""
    if not icerik_cell:
        debug_info += "⚠️ İÇERİK BULUNAMADI\n"
        debug_info += f"📍 Vardiya sütunu: {vardiya_col}\n\n"
        debug_info += "👉 Sağdaki hücreler:\n"

        for col in range(vardiya_col + 1, min(vardiya_col + 6, len(staff_row))):
            raw_text = str(staff_row[col])
            debug_info += f"[Sütun {col}] → {raw_text}\n"

    # Vardiya bilgisi
    words = vardiya_cell.split()
    vardiya = words[0] if words else ""
    vardiya_aciklama = " ".join(words[1:]) if len(words) > 1 else ""

    detay = parse_flights(icerik_cell)

    # 📩 Mesaj oluştur
    if vardiya.lower() == "off":
        message = (
            f"📅 Yarın ({tomorrow.strftime('%d %B')})\n"
            f"😴 OFF’sun"
        )
    else:
        message = (
            f"📅 Yarın ({tomorrow.strftime('%d %B')})\n"
            f"👤 {STAFF_NAME}\n"
            f"⏰ Vardiya: {vardiya}"
        )

        if vardiya_aciklama:
            message += f" ({vardiya_aciklama})"

        if detay:
            message += f"\n\n📋 İçerik:\n{detay}"

    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)

    if debug_info:
        await bot.send_message(chat_id=CHAT_ID, text=debug_info)

    print("✅ Telegram mesajı gönderildi")


asyncio.run(main())
