"""Chuyển file DMS (.xlsb) sang .xlsx rồi lưu lên OneDrive để Power BI làm mới trên cloud.

Power BI Service không đọc được .xlsb khi không có gateway (thiếu Microsoft.ACE.OLEDB.12.0),
nên bước này tạo một bản .xlsx chỉ chứa giá trị (không công thức), giữ nguyên tên và thứ tự sheet,
để các truy vấn Power BI cũ (Item="Fundamental", ...) chạy được mà không phải sửa bước điều hướng.
"""
import datetime
import io
import math
import os
import traceback
from urllib.parse import quote

import msal
import requests
from openpyxl import Workbook
from python_calamine import CalamineWorkbook

INPUT_FILES = ["DMS_Input.xlsb", "DMS_Input.xlsx"]
USER_ID = "tiennm@tuanvietc5.id.vn"

# Đường dẫn file .xlsx trên OneDrive (tính từ gốc OneDrive). Power BI trỏ vào file này.
# Đổi bằng biến môi trường PBI_OUTPUT_PATH trong workflow nếu muốn để chỗ khác.
OUTPUT_PATH = os.environ.get("PBI_OUTPUT_PATH", "DMS PowerBI/DMS CBD.xlsx")

# Chỉ chuyển các sheet này. Để trống = chuyển tất cả sheet (kể cả sheet ẩn).
# Ví dụ: PBI_SHEETS="Fundamental,List P3M"
SHEETS = [s.strip() for s in os.environ.get("PBI_SHEETS", "").split(",") if s.strip()]

CHUNK = 5 * 1024 * 1024  # 5 MB, là bội số của 320 KB theo yêu cầu của Graph upload session


def get_token():
    app = msal.ConfidentialClientApplication(
        os.environ["CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['TENANT_ID']}",
        client_credential=os.environ["CLIENT_SECRET"],
    )
    return app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]


def find_input():
    for name in INPUT_FILES:
        if os.path.exists(name):
            return name
    raise Exception(f"Không thấy file đầu vào: {' hoặc '.join(INPUT_FILES)}")


def clean(v):
    if v == "":
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, datetime.timedelta):
        return str(v)
    return v


def trim(rows):
    # Bỏ các dòng trống ở cuối và ô trống ở cuối mỗi dòng để file nhỏ hơn
    while rows and all(c is None for c in rows[-1]):
        rows.pop()
    out = []
    for r in rows:
        r = list(r)
        while r and r[-1] is None:
            r.pop()
        out.append(r)
    return out


def build_xlsx(path):
    with open(path, "rb") as f:
        src = CalamineWorkbook.from_filelike(f)  # nhận .xlsb/.xlsx theo nội dung file
        names = SHEETS or src.sheet_names
        missing = [n for n in names if n not in src.sheet_names]
        if missing:
            raise Exception(f"Không có sheet {missing}. Các sheet đang có: {src.sheet_names}")

        wb = Workbook(write_only=True)
        for name in names:
            rows = src.get_sheet_by_name(name).to_python(skip_empty_area=False)
            rows = trim([[clean(v) for v in r] for r in rows])
            ws = wb.create_sheet(title=name)
            for r in rows:
                ws.append(r)
            print(f"  {name}: {len(rows)} dòng")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def upload(data, token):
    # File > 4 MB phải tải lên bằng upload session. Ghi đè nếu đã có file cùng tên.
    url = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/{quote(OUTPUT_PATH)}:/createUploadSession"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
    )
    r.raise_for_status()
    upload_url = r.json()["uploadUrl"]

    total = len(data)
    for start in range(0, total, CHUNK):
        part = data[start:start + CHUNK]
        end = start + len(part) - 1
        resp = requests.put(
            upload_url,
            data=part,
            headers={"Content-Length": str(len(part)), "Content-Range": f"bytes {start}-{end}/{total}"},
        )
        if resp.status_code not in (200, 201, 202):
            raise Exception(f"Upload lỗi {resp.status_code}: {resp.text}")
    return resp.json()


def main():
    try:
        path = find_input()
        print(f"Chuyển {path} sang .xlsx:")
        data = build_xlsx(path)
        print(f"Dung lượng .xlsx: {len(data) / 1024 / 1024:.1f} MB")
        item = upload(data, get_token())
        print(f"Đã lưu OneDrive: {OUTPUT_PATH}")
        print(f"Link cho Power BI: {item.get('webUrl')}")
    except Exception:
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
