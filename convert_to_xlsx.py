"""Chuyển file DMS (.xlsb) sang .xlsx rồi lưu lên SharePoint để Power BI làm mới trên cloud.

Power BI Service không đọc được .xlsb khi không có gateway (thiếu Microsoft.ACE.OLEDB.12.0),
nên bước này tạo một bản .xlsx chỉ chứa giá trị (không công thức), giữ nguyên tên và thứ tự sheet,
để các truy vấn Power BI cũ (Item="Fundamental", ...) chạy được mà không phải sửa bước điều hướng.
"""
import datetime
import io
import math
import os
import traceback
from urllib.parse import quote, urlparse

import msal
import requests
from openpyxl import Workbook
from python_calamine import CalamineWorkbook

INPUT_FILES = ["DMS_Input.xlsb", "DMS_Input.xlsx"]
USER_ID = "tiennm@tuanvietc5.id.vn"

# Nơi lưu file .xlsx cho Power BI: SharePoint site "tiennm", thư viện Documents,
# thư mục C5-Insight/07_dms_mo. Trên máy đồng bộ thành
# "D:\\C5\\tiennm - Documents\\C5-Insight\\07_dms_mo".
# PBI_SITE: tên site hoặc link site đầy đủ (https://<tên>.sharepoint.com/sites/<site>).
# Để PBI_SITE trống thì lưu vào OneDrive của USER_ID.
SITE = os.environ.get("PBI_SITE", "tiennm").strip()
OUTPUT_PATH = os.environ.get("PBI_OUTPUT_PATH", "C5-Insight/07_dms_mo/DMS CBD.xlsx")

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


GRAPH = "https://graph.microsoft.com/v1.0"


def find_drive(token):
    """Trả về URL gốc của thư viện tài liệu (drive) cần lưu file."""
    h = {"Authorization": f"Bearer {token}"}
    if not SITE:
        return f"{GRAPH}/users/{USER_ID}/drive"

    if SITE.startswith("https://"):
        u = urlparse(SITE)
        host, site_path = u.netloc, u.path.rstrip("/")
    else:
        # Lấy tên miền SharePoint từ OneDrive của USER_ID: xxx-my.sharepoint.com -> xxx.sharepoint.com
        r = requests.get(f"{GRAPH}/users/{USER_ID}/drive?$select=webUrl", headers=h)
        r.raise_for_status()
        host = urlparse(r.json()["webUrl"]).netloc.replace("-my.sharepoint.com", ".sharepoint.com")
        site_path = f"/sites/{SITE}"

    r = requests.get(f"{GRAPH}/sites/{host}:{quote(site_path)}?$select=id,webUrl", headers=h)
    if r.status_code == 200:
        print(f"SharePoint site: {r.json()['webUrl']}")
        return f"{GRAPH}/sites/{r.json()['id']}/drive"

    # Không đoán đúng đường dẫn site: tìm theo tên
    s = requests.get(f"{GRAPH}/sites?search={quote(SITE)}&$select=id,name,displayName,webUrl", headers=h)
    if s.status_code == 200:
        sites = s.json().get("value", [])
        for site in sites:
            if SITE.lower() in (site.get("name", "").lower(), site.get("displayName", "").lower()):
                print(f"SharePoint site: {site['webUrl']}")
                return f"{GRAPH}/sites/{site['id']}/drive"
        found = [x.get("webUrl") for x in sites]
    else:
        found = s.text
    raise Exception(
        f"Không tìm thấy SharePoint site '{SITE}' ({r.status_code}: {r.text}). "
        f"Kết quả tìm kiếm: {found}. Đặt PBI_SITE = link site đầy đủ trong workflow. "
        "Nếu báo 403, app Azure cần thêm quyền Sites.ReadWrite.All (Application) và Grant admin consent."
    )


def upload(data, token):
    # File > 4 MB phải tải lên bằng upload session. Ghi đè nếu đã có file cùng tên.
    url = f"{find_drive(token)}/root:/{quote(OUTPUT_PATH)}:/createUploadSession"
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
        print(f"Đã lưu: {OUTPUT_PATH}")
        print(f"Link cho Power BI: {item.get('webUrl')}")
    except Exception:
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
