import io
import time
import unicodedata
import traceback
import requests
import pymupdf as fitz
from PIL import Image, ImageChops
from urllib.parse import quote
from extract_data import get_token, USER_ID

# File cần chụp và thư mục lưu ảnh trên OneDrive
WORKBOOK = "DMS New.xlsx"
OUTPUT_FOLDER = "DMS Anh"
DPI = 200  # Độ nét ảnh, tăng lên 250-300 nếu cần nét hơn

# Mỗi ảnh lấy từ trang PDF có chứa "keyword".
# Nếu dò chữ không ra đúng trang, điền số trang vào "page" (trang đầu = 1).
IMAGES = [
    {"file": "PhuYen.png", "keyword": "PHÚ YÊN", "page": None},
    {"file": "SongCau.png", "keyword": "SÔNG CẦU", "page": None},
]

GRAPH = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:"


def normalize(text):
    return unicodedata.normalize("NFC", text).upper()


def log_day_cells(book, session):
    # Ghi ra log công thức và giá trị của dòng có chữ "Đã qua" để kiểm tra số ngày còn lại
    sheets = requests.get(f"{book}/worksheets?$select=name", headers=session).json()["value"]
    for sheet in sheets:
        url = f"{book}/worksheets/{quote(sheet['name'])}/usedRange?$select=address,formulas,values"
        r = requests.get(url, headers=session, timeout=120)
        if not r.ok:
            continue
        data = r.json()
        for i, row in enumerate(data["values"]):
            if any("ĐÃ QUA" in normalize(str(v)) for v in row):
                cells = [(f, v) for f, v in zip(data["formulas"][i], row) if f != ""]
                print(f"[{sheet['name']}] {data['address']} dòng {i + 1}: {cells[:12]}")


def recalculate(auth):
    # Tính lại toàn bộ (cả công thức theo ngày như TODAY) trong một phiên có lưu,
    # rồi chờ 30 giây cho OneDrive lưu trước khi xuất PDF.
    book = f"{GRAPH}/{quote(WORKBOOK)}:/workbook"
    r = requests.post(f"{book}/createSession", json={"persistChanges": True}, headers=auth)
    r.raise_for_status()
    session = {**auth, "workbook-session-id": r.json()["id"]}
    r = requests.post(f"{book}/application/calculate", json={"calculationType": "Full"}, headers=session)
    print(f"Tính lại toàn bộ công thức: HTTP {r.status_code}")
    try:
        log_day_cells(book, session)
    except Exception as e:
        print(f"Không đọc được ô Đã qua: {e}")
    requests.post(f"{book}/closeSession", headers=session)

    time.sleep(30)


def download_pdf(auth):
    # Graph chuyển xlsx sang PDF bằng bộ in của Excel, giữ nguyên định dạng
    url = f"{GRAPH}/{quote(WORKBOOK)}:/content?format=pdf"
    for attempt in range(1, 4):
        r = requests.get(url, headers=auth, timeout=300)
        if r.status_code == 200:
            print(f"Đã tải PDF: {len(r.content) / 1024:.0f} KB")
            return r.content
        print(f"Lần {attempt}: không tải được PDF (HTTP {r.status_code}) {r.text[:300]}")
        time.sleep(20)
    raise Exception("Không chuyển được file sang PDF")


def render_page(page):
    pix = page.get_pixmap(dpi=DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    # Cắt bỏ lề trắng xung quanh, chừa lại 12px
    bbox = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    if bbox:
        pad = 12
        bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height))
        img = img.crop(bbox)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def upload(auth, path, data):
    url = f"{GRAPH}/{quote(path)}:/content"
    r = requests.put(url, data=data, headers={**auth, "Content-Type": "image/png"})
    if r.status_code not in [200, 201]:
        raise Exception(f"Lỗi khi lưu {path}: {r.text[:300]}")
    print(f"Đã lưu {path} ({len(data) / 1024:.0f} KB)")


def make_images():
    try:
        auth = {"Authorization": f"Bearer {get_token()}"}

        recalculate(auth)

        doc = fitz.open(stream=download_pdf(auth), filetype="pdf")
        page_texts = [normalize(p.get_text()) for p in doc]
        print(f"PDF có {len(doc)} trang")
        for i, text in enumerate(page_texts, start=1):
            print(f"  Trang {i}: {' '.join(text.split())[:80]}")

        used = set()
        missing = []
        for item in IMAGES:
            if item["page"]:
                index = item["page"] - 1
            else:
                index = next((i for i, t in enumerate(page_texts)
                              if normalize(item["keyword"]) in t and i not in used), None)
            if index is None or index >= len(doc):
                missing.append(item["file"])
                continue
            used.add(index)
            print(f"{item['file']} lấy từ trang {index + 1}")
            upload(auth, f"{OUTPUT_FOLDER}/{item['file']}", render_page(doc[index]))

        if missing:
            # Lưu 10 trang cuối (các sheet đã đặt vùng in thường nằm cuối PDF) để xem rồi điền số trang vào IMAGES
            for i in range(max(len(doc) - 10, 0), len(doc)):
                upload(auth, f"{OUTPUT_FOLDER}/kiem-tra/Trang_{i + 1}.png", render_page(doc[i]))
            raise Exception(f"Không tìm thấy trang cho: {', '.join(missing)}. "
                            f"Xem ảnh trong OneDrive/{OUTPUT_FOLDER}/kiem-tra rồi điền 'page' trong IMAGES.")

    except Exception:
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    make_images()
