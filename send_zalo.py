import os
import sys
from datetime import datetime, timedelta
import requests
from urllib.parse import quote
from extract_data import get_token, USER_ID

# Gửi PhuYen.png, SongCau.png từ OneDrive/DMS Anh vào Zalo qua Zalo Bot (chính chủ Zalo, miễn phí)
# Secrets cần có trên GitHub:
#   ZALO_BOT_TOKEN : token bot nhận được khi tạo bot ở Zalo Bot Creator
#   ZALO_CHAT_IDS  : các chat_id nhận ảnh, cách nhau bởi dấu phẩy
OUTPUT_FOLDER = "DMS Anh"
FILES = [("PhuYen.png", "DMS Phú Yên"), ("SongCau.png", "DMS Sông Cầu")]

GRAPH = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:"
ZALO = f"https://bot-api.zaloplatforms.com/bot{os.environ.get('ZALO_BOT_TOKEN', '')}"


def download_url(auth, name):
    # Link tải tạm thời (khoảng 1 giờ) do OneDrive cấp, Zalo dùng link này để lấy ảnh
    url = f"{GRAPH}/{quote(f'{OUTPUT_FOLDER}/{name}')}"
    r = requests.get(url, headers=auth)
    r.raise_for_status()
    # Thêm tên file vào cuối link để Zalo nhận ra đây là ảnh .png (cần khi chuyển tiếp ảnh sang nhóm)
    return r.json()["@microsoft.graph.downloadUrl"] + "&name=" + name


def send_photo(chat_id, photo, caption):
    r = requests.post(f"{ZALO}/sendPhoto",
                      json={"chat_id": chat_id, "photo": photo, "caption": caption}, timeout=60)
    print(f"Gửi {caption} tới {chat_id}: HTTP {r.status_code} {r.text[:200]}")
    return r.ok and r.json().get("ok")


def main():
    chat_ids = [c.strip() for c in os.environ.get("ZALO_CHAT_IDS", "").split(",") if c.strip()]
    if not os.environ.get("ZALO_BOT_TOKEN") or not chat_ids:
        print("Thiếu ZALO_BOT_TOKEN hoặc ZALO_CHAT_IDS, bỏ qua bước gửi Zalo")
        return

    auth = {"Authorization": f"Bearer {get_token()}"}
    # Số liệu DMS là của ngày hôm trước (giờ Việt Nam); hôm trước là Chủ nhật thì lấy Thứ 7
    day = datetime.utcnow() + timedelta(hours=7) - timedelta(days=1)
    if day.weekday() == 6:
        day -= timedelta(days=1)
    today = day.strftime("%d/%m/%Y")
    failed = 0
    for name, title in FILES:
        link = download_url(auth, name)
        for chat_id in chat_ids:
            if not send_photo(chat_id, link, f"{title} {today}"):
                failed += 1
    if failed:
        sys.exit(f"Có {failed} ảnh gửi Zalo không thành công")


if __name__ == "__main__":
    main()
