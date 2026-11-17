"""Hàm dùng chung: đổi file Excel bất kỳ (.xls, .xlsb, .xlsm, .xlsx) sang .xlsx và đọc/ghi SharePoint/OneDrive qua Graph.

File .xlsx tạo ra chỉ chứa GIÁ TRỊ: giữ tên, thứ tự, trạng thái ẩn và vị trí ô của mọi sheet,
nhưng bỏ công thức, định dạng, macro, pivot, biểu đồ, hình ảnh.
"""
import datetime
import io
import math
import os
from urllib.parse import quote, unquote, urlparse

import msal
import requests
from openpyxl import Workbook
from python_calamine import CalamineWorkbook

GRAPH = "https://graph.microsoft.com/v1.0"
USER_ID = "tiennm@tuanvietc5.id.vn"
CONVERT_EXTS = (".xls", ".xlsb", ".xlsm")
CHUNK = 5 * 1024 * 1024  # bội số của 320 KB theo yêu cầu của Graph upload session


# ---------- Chuyển đổi ----------

def _clean(v):
    if v == "":
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, datetime.timedelta):
        return str(v)
    return v


def _trim(rows):
    # Bỏ dòng trống ở cuối và ô trống ở cuối mỗi dòng để file nhỏ hơn
    while rows and all(c is None for c in rows[-1]):
        rows.pop()
    out = []
    for r in rows:
        while r and r[-1] is None:
            r.pop()
        out.append(r)
    return out


def to_xlsx(data, sheets=None, log=print):
    """Nhận nội dung file Excel (bytes, định dạng nhận theo nội dung), trả về bytes .xlsx."""
    src = CalamineWorkbook.from_filelike(io.BytesIO(data))
    names = sheets or src.sheet_names
    missing = [n for n in names if n not in src.sheet_names]
    if missing:
        raise Exception(f"Không có sheet {missing}. Các sheet đang có: {src.sheet_names}")
    hidden = {
        m.name for m in getattr(src, "sheets_metadata", [])
        if not str(m.visible).endswith(".Visible")
    }

    wb = Workbook(write_only=True)
    for name in names:
        rows = src.get_sheet_by_name(name).to_python(skip_empty_area=False)
        rows = _trim([[_clean(v) for v in r] for r in rows])
        ws = wb.create_sheet(title=name)
        if name in hidden:
            ws.sheet_state = "hidden"
        for r in rows:
            ws.append(r)
        log(f"  {name}: {len(rows)} dòng")
    if not names:
        wb.create_sheet("Sheet1")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- Graph ----------

def get_token():
    app = msal.ConfidentialClientApplication(
        os.environ["CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['TENANT_ID']}",
        client_credential=os.environ["CLIENT_SECRET"],
    )
    return app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]


def find_drive(token, site):
    """URL gốc của thư viện tài liệu. site = '' (OneDrive của USER_ID), tên site, hoặc link site đầy đủ."""
    h = {"Authorization": f"Bearer {token}"}
    site = (site or "").strip()
    if not site:
        return f"{GRAPH}/users/{USER_ID}/drive"

    if site.startswith("https://"):
        u = urlparse(site)
        host, site_path = u.netloc, u.path.rstrip("/")
    else:
        # Lấy tên miền SharePoint từ OneDrive của USER_ID: xxx-my.sharepoint.com -> xxx.sharepoint.com
        r = requests.get(f"{GRAPH}/users/{USER_ID}/drive?$select=webUrl", headers=h)
        r.raise_for_status()
        host = urlparse(r.json()["webUrl"]).netloc.replace("-my.sharepoint.com", ".sharepoint.com")
        site_path = f"/sites/{site}"

    r = requests.get(f"{GRAPH}/sites/{host}:{quote(site_path)}?$select=id,webUrl", headers=h)
    if r.status_code == 200:
        print(f"SharePoint site: {r.json()['webUrl']}")
        return f"{GRAPH}/sites/{r.json()['id']}/drive"

    # Không đoán đúng đường dẫn site: tìm theo tên
    s = requests.get(f"{GRAPH}/sites?search={quote(site)}&$select=id,name,displayName,webUrl", headers=h)
    found = s.text
    if s.status_code == 200:
        items = s.json().get("value", [])
        for it in items:
            if site.lower() in (it.get("name", "").lower(), it.get("displayName", "").lower()):
                print(f"SharePoint site: {it['webUrl']}")
                return f"{GRAPH}/sites/{it['id']}/drive"
        found = [x.get("webUrl") for x in items]
    raise Exception(
        f"Không tìm thấy SharePoint site '{site}' ({r.status_code}: {r.text}). "
        f"Kết quả tìm kiếm: {found}. Hãy dùng link site đầy đủ. "
        "Nếu báo 403, app Azure cần thêm quyền Sites.ReadWrite.All (Application) và Grant admin consent."
    )


def norm_path(path):
    """Làm sạch đường dẫn người dùng nhập: bỏ dấu nháy, đổi \\ thành /, bỏ phần ổ đĩa/thư viện ở đầu.

    Nhận được cả: C5-Insight/07_dms_mo, "C5-Insight\\07_dms_mo",
    D:\\C5\\tiennm - Documents\\C5-Insight\\07_dms_mo, /Shared Documents/C5-Insight/07_dms_mo,
    https://xxx.sharepoint.com/Shared%20Documents/C5-Insight/07_dms_mo
    """
    p = (path or "").strip().strip('"\'').strip()
    p = unquote(p).replace("\\", "/")
    if p.lower().startswith("https://"):
        p = urlparse(p).path
        # bỏ /sites/<tên> nếu có
        parts = p.strip("/").split("/")
        if len(parts) >= 2 and parts[0].lower() in ("sites", "teams"):
            p = "/".join(parts[2:])
    # Thư mục đồng bộ trên máy: ...\\<site> - Documents\\...
    low = p.lower()
    for marker in (" - documents/", " - shared documents/", " - tài liệu/"):
        i = low.find(marker)
        if i >= 0:
            p = p[i + len(marker):]
            break
    p = p.strip("/")
    for lib in ("Shared Documents/", "Documents/", "Tài liệu/"):
        if p.lower().startswith(lib.lower()):
            p = p[len(lib):]
            break
    if p.lower() in ("shared documents", "documents"):
        p = ""
    return "/".join(x.strip() for x in p.split("/") if x.strip())


def item_url(drive, path):
    path = norm_path(path)
    return f"{drive}/root" if not path else f"{drive}/root:/{quote(path)}:"


def get_item(token, drive, path):
    r = requests.get(item_url(drive, path), headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 404:
        raise Exception(
            f"Không thấy '{norm_path(path)}' trong thư viện Documents. Kiểm tra lại tên thư mục/file "
            "(tính từ thư viện, ví dụ C5-Insight/07_dms_mo hoặc C5-Insight/07_dms_mo/ten file.xlsb)."
        )
    r.raise_for_status()
    return r.json()


def list_children(token, drive, path):
    h = {"Authorization": f"Bearer {token}"}
    url = f"{item_url(drive, path)}/children?$select=id,name,file,folder&$top=200"
    out = []
    while url:
        r = requests.get(url, headers=h)
        r.raise_for_status()
        j = r.json()
        out += j.get("value", [])
        url = j.get("@odata.nextLink")
    return out


def download(token, drive, item_id):
    r = requests.get(f"{drive}/items/{item_id}/content", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.content


def upload(token, drive, path, data):
    """Tải lên (ghi đè) bằng upload session, dùng được cho file trên 4 MB."""
    r = requests.post(
        f"{item_url(drive, path)}/createUploadSession",
        headers={"Authorization": f"Bearer {token}"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
    )
    r.raise_for_status()
    upload_url = r.json()["uploadUrl"]
    total = len(data)
    resp = None
    for start in range(0, total, CHUNK):
        part = data[start:start + CHUNK]
        resp = requests.put(
            upload_url,
            data=part,
            headers={"Content-Length": str(len(part)),
                     "Content-Range": f"bytes {start}-{start + len(part) - 1}/{total}"},
        )
        if resp.status_code not in (200, 201, 202):
            raise Exception(f"Upload lỗi {resp.status_code}: {resp.text}")
    return resp.json()


def ensure_folder(token, drive, parent_path, name):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{item_url(drive, parent_path)}/children",
        headers=h,
        json={"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"},
    )
    if r.status_code in (200, 201):
        return r.json()["id"]
    if r.status_code == 409:  # đã có
        return get_item(token, drive, f"{parent_path.strip('/')}/{name}")["id"]
    r.raise_for_status()


def move(token, drive, item_id, folder_id):
    r = requests.patch(
        f"{drive}/items/{item_id}?@microsoft.graph.conflictBehavior=replace",
        headers={"Authorization": f"Bearer {token}"},
        json={"parentReference": {"id": folder_id}},
    )
    r.raise_for_status()


def delete(token, drive, item_id):
    # Vào thùng rác SharePoint, khôi phục được trong 93 ngày
    r = requests.delete(f"{drive}/items/{item_id}", headers={"Authorization": f"Bearer {token}"})
    if r.status_code not in (200, 204):
        r.raise_for_status()
