"""Hàm dùng chung: đổi file Excel bất kỳ (.xls, .xlsb, .xlsm, .xlsx) sang .xlsx và đọc/ghi SharePoint/OneDrive qua Graph.

Hai cách đổi:
- to_xlsx_full(): dùng LibreOffice (chạy ngầm), GIỮ công thức, định dạng, định dạng có điều kiện,
  gộp ô, cố định dòng/cột, hình ảnh, sheet ẩn. Mất: liên kết sang file Excel khác (công thức thành #REF!),
  macro VBA, ghi chú ô. Sau khi đổi, so giá trị từng ô với file gốc và in ra số ô khác.
- to_xlsx(): chỉ GIÁ TRỊ (không công thức, không định dạng). Dùng khi không có LibreOffice
  hoặc khi bản LibreOffice làm sai quá nhiều ô.
"""
import datetime
import glob
import io
import math
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
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


# ---------- Đổi bằng LibreOffice (giữ công thức, định dạng) ----------

def find_soffice():
    for p in [os.environ.get("SOFFICE", "")] + sorted(glob.glob("/opt/libreoffice*/program/soffice"), reverse=True):
        if p and os.path.exists(p):
            return p
    return shutil.which("soffice") or shutil.which("libreoffice")


_BAD_AMP = re.compile(rb"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)")


def _fix_xml(xlsx):
    """Một số bản LibreOffice ghi dấu & chưa mã hoá trong externalLink*.xml làm Excel báo lỗi file. Sửa lại."""
    from lxml import etree
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(xlsx)) as zi, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            d = zi.read(it.filename)
            if it.filename.endswith((".xml", ".rels")):
                try:
                    etree.fromstring(d)
                except etree.XMLSyntaxError:
                    d = _BAD_AMP.sub(b"&amp;", d)
                    etree.fromstring(d)
                    print(f"  Đã sửa XML lỗi: {it.filename}")
            zo.writestr(it, d)
    return out.getvalue()


def _norm(v):
    if v == "" or v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return int(v) if v.is_integer() else round(v, 6)
    if isinstance(v, (datetime.datetime, datetime.date)):
        return str(v)[:10]
    if isinstance(v, datetime.time):
        return str(v)[:8]
    return v


def compare_values(src_data, out_data, log=print, cells=None):
    """So giá trị (kết quả công thức đã lưu) từng ô giữa file gốc và file mới. Trả về (số ô có dữ liệu, số ô khác).
    Nếu truyền dict cells, ghi các ô khác vào cells[tên sheet] = [(dòng, cột, giá trị gốc), ...] (đếm từ 0)."""
    a_wb = CalamineWorkbook.from_filelike(io.BytesIO(src_data))
    b_wb = CalamineWorkbook.from_filelike(io.BytesIO(out_data))
    total = diff = 0
    for name in a_wb.sheet_names:
        if name not in b_wb.sheet_names:
            raise Exception(f"File mới thiếu sheet '{name}'")
        a = a_wb.get_sheet_by_name(name).to_python(skip_empty_area=False)
        b = b_wb.get_sheet_by_name(name).to_python(skip_empty_area=False)
        n = d = 0
        ex = []
        for i in range(max(len(a), len(b))):
            ra = a[i] if i < len(a) else []
            rb = b[i] if i < len(b) else []
            for j in range(max(len(ra), len(rb))):
                va = _norm(ra[j]) if j < len(ra) else None
                vb = _norm(rb[j]) if j < len(rb) else None
                if va is None and vb is None:
                    continue
                n += 1
                if va == vb:
                    continue
                if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and abs(va - vb) <= 1e-6 * max(1, abs(va)):
                    continue
                d += 1
                if cells is not None:
                    cells.setdefault(name, []).append((i, j, ra[j] if j < len(ra) else None))
                if len(ex) < 2:
                    ex.append(f"dòng {i + 1} cột {j + 1}: {va!r} -> {vb!r}")
        total += n
        diff += d
        log(f"  {name}: {n} ô, khác {d}" + (f" (vd {'; '.join(ex)})" if d else ""))
    return total, diff


_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_RNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_EPOCH = datetime.datetime(1899, 12, 30)


def _col_letter(j):
    s = ""
    j += 1
    while j:
        j, r = divmod(j - 1, 26)
        s = chr(65 + r) + s
    return s


def _col_index(ref):
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
        else:
            break
    return n - 1


def _set_cell_value(c, v):
    """Bỏ công thức của ô <c>, ghi giá trị v (giữ kiểu định dạng s)."""
    from lxml import etree
    for child in list(c):
        c.remove(child)
    c.attrib.pop("t", None)
    c.attrib.pop("cm", None)
    c.attrib.pop("vm", None)
    if v is None or v == "":
        return
    if isinstance(v, bool):
        c.set("t", "b")
        etree.SubElement(c, f"{{{_NS}}}v").text = "1" if v else "0"
        return
    if isinstance(v, datetime.datetime):
        v = (v - _EPOCH).total_seconds() / 86400
    elif isinstance(v, datetime.date):
        v = (datetime.datetime(v.year, v.month, v.day) - _EPOCH).days
    elif isinstance(v, datetime.time):
        v = (v.hour * 3600 + v.minute * 60 + v.second + v.microsecond / 1e6) / 86400
    elif isinstance(v, datetime.timedelta):
        v = v.total_seconds() / 86400
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return
        etree.SubElement(c, f"{{{_NS}}}v").text = repr(v) if isinstance(v, float) else str(v)
        return
    v = str(v)
    if v.startswith("#") and v.rstrip("!?0/").upper() in ("#REF", "#N/A", "#NAME", "#VALUE", "#DIV", "#NUM", "#NULL"):
        c.set("t", "e")
        etree.SubElement(c, f"{{{_NS}}}v").text = v
        return
    c.set("t", "inlineStr")
    is_ = etree.SubElement(c, f"{{{_NS}}}is")
    t = etree.SubElement(is_, f"{{{_NS}}}t")
    t.text = v
    if v != v.strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def paste_values(xlsx, cells, log=print):
    """Dán giá trị gốc vào các ô trong cells (dict sheet -> [(dòng, cột, giá trị)]), bỏ công thức của các ô đó.
    Các ô khác giữ nguyên công thức và định dạng. Trả về bytes .xlsx mới."""
    from lxml import etree
    from posixpath import join, normpath
    if not cells:
        return xlsx
    zi = zipfile.ZipFile(io.BytesIO(xlsx))
    wb = etree.fromstring(zi.read("xl/workbook.xml"))
    rels = etree.fromstring(zi.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    paths = {}
    for sh in wb.iter(f"{{{_NS}}}sheet"):
        t = target[sh.get(f"{{{_RNS}}}id")]
        paths[sh.get("name")] = t.lstrip("/") if t.startswith("/") else normpath(join("xl", t))

    patched = {}
    for name, items in cells.items():
        path = paths[name]
        root = etree.fromstring(zi.read(path))
        sd = root.find(f"{{{_NS}}}sheetData")
        rows = {int(r.get("r")): r for r in sd.iter(f"{{{_NS}}}row")}
        for i, j, v in items:
            rn = i + 1
            ref = f"{_col_letter(j)}{rn}"
            row = rows.get(rn)
            if row is None:
                row = etree.Element(f"{{{_NS}}}row", r=str(rn))
                after = [r for k, r in rows.items() if k < rn]
                if after:
                    max(after, key=lambda r: int(r.get("r"))).addnext(row)
                else:
                    sd.insert(0, row)
                rows[rn] = row
            cell = None
            for c in row.iter(f"{{{_NS}}}c"):
                if c.get("r") == ref:
                    cell = c
                    break
            if cell is None:
                if v is None or v == "":
                    continue
                cell = etree.Element(f"{{{_NS}}}c", r=ref)
                prev = [c for c in row.iter(f"{{{_NS}}}c") if _col_index(c.get("r", "A")) < j]
                if prev:
                    prev[-1].addnext(cell)
                else:
                    row.insert(0, cell)
                row.attrib.pop("spans", None)
            _set_cell_value(cell, v)
        patched[path] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        log(f"  {name}: dán giá trị gốc vào {len(items)} ô")

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            if it.filename == "xl/calcChain.xml":
                continue
            zo.writestr(it, patched.get(it.filename, zi.read(it.filename)))
    return out.getvalue()


def to_xlsx_full(data, ext=".xlsb", log=print):
    """Đổi bằng LibreOffice. Trả về bytes .xlsx. Lỗi nếu không có LibreOffice hoặc đổi không được."""
    soffice = find_soffice()
    if not soffice:
        raise Exception("Không tìm thấy LibreOffice (soffice)")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in" + ext)
        with open(src, "wb") as f:
            f.write(data)
        outdir = os.path.join(tmp, "out")
        # Hồ sơ người dùng riêng để không đụng tiến trình LibreOffice khác
        profile = "file://" + os.path.join(tmp, "profile")
        r = subprocess.run(
            [soffice, f"-env:UserInstallation={profile}", "--headless", "--norestore",
             "--convert-to", "xlsx:Calc Office Open XML", "--outdir", outdir, src],
            capture_output=True, text=True, timeout=600,
        )
        out = os.path.join(outdir, "in.xlsx")
        if r.returncode != 0 or not os.path.exists(out):
            raise Exception(f"LibreOffice đổi lỗi: {r.stdout} {r.stderr}")
        with open(out, "rb") as f:
            return _fix_xml(f.read())


def convert(data, ext=".xlsb", mode="full", max_diff_ratio=0.05, log=print):
    """Đổi sang .xlsx. Trả về (bytes, cách đã dùng).
    mode="full": LibreOffice giữ công thức, định dạng. Ô nào có giá trị khác file gốc (vd #REF! do liên kết
    sang file khác) thì bỏ công thức, dán giá trị gốc (như Paste Values). Nếu LibreOffice lỗi, hoặc số ô
    phải dán vượt max_diff_ratio (file đổi hỏng nhiều), thì quay về bản chỉ giá trị.
    mode="values": chỉ giá trị."""
    if mode == "full":
        try:
            out = to_xlsx_full(data, ext, log)
            log("  So giá trị với file gốc:")
            cells = {}
            total, diff = compare_values(data, out, log, cells)
            ratio = diff / total if total else 0
            log(f"  Tổng: {total} ô, khác {diff} ({ratio:.2%})")
            if ratio > max_diff_ratio:
                raise Exception(f"khác quá {max_diff_ratio:.0%} số ô")
            if diff:
                log("  Dán giá trị gốc vào các ô khác (bỏ công thức của các ô đó):")
                out = paste_values(out, cells, log)
                total2, diff2 = compare_values(data, out, lambda *a: None)
                log(f"  Sau khi dán: khác {diff2} ô")
                if diff2:
                    raise Exception(f"vẫn còn {diff2} ô khác sau khi dán giá trị")
            return out, "full"
        except Exception as e:
            log(f"  CẢNH BÁO: không giữ được công thức ({e}), chuyển sang bản chỉ giá trị")
    return to_xlsx(data, log=log), "values"


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
