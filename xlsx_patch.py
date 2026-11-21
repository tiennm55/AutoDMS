"""Ghi giá trị vào một vùng ô của file .xlsx bằng cách sửa thẳng XML bên trong file.

Dùng khi Excel API (Graph) từ chối sửa file vì file có form controls / ActiveX
(lỗi UnsupportedFeatureEditWarning). Chỉ sheet đích và workbook.xml bị sửa;
mọi phần khác (control, macro, link ngoài, định dạng, ảnh...) được chép nguyên byte.
Không dùng openpyxl vì openpyxl làm mất control và link ngoài.
"""
import io
import re
import zipfile
import datetime
import posixpath
from lxml import etree

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
CALC_CHAIN_TYPE = NS_REL + "/calcChain"

M = "{%s}" % NS_MAIN
_DATETIME_STR = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?$")
_ILLEGAL_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _split_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return col, int(m.group(2))


def _excel_serial(dt):
    delta = dt - datetime.datetime(1899, 12, 30)
    return delta.days + delta.seconds / 86400 + delta.microseconds / 86400e6


def _fmt_number(v):
    if isinstance(v, int):
        return str(v)
    return repr(float(v))


def _set_cell_value(c, value):
    """Thay nội dung ô c bằng value, giữ nguyên định dạng (thuộc tính s)."""
    for child in list(c):
        if child.tag == M + "f" and child.get("t") in ("shared", "array") and child.get("ref"):
            raise Exception(
                f"Ô {c.get('r')} là gốc của công thức {child.get('t')} ({child.get('ref')}); "
                "ghi đè sẽ làm hỏng file. Hãy bỏ công thức này khỏi vùng dán."
            )
        c.remove(child)
    c.attrib.pop("t", None)
    c.attrib.pop("cm", None)
    c.attrib.pop("vm", None)

    if isinstance(value, str) and _DATETIME_STR.match(value):
        value = _excel_serial(datetime.datetime.fromisoformat(value))
    if isinstance(value, datetime.datetime):
        value = _excel_serial(value)
    elif isinstance(value, datetime.date):
        value = _excel_serial(datetime.datetime(value.year, value.month, value.day))

    if value is None or value == "":
        return
    if isinstance(value, bool):
        c.set("t", "b")
        etree.SubElement(c, M + "v").text = "1" if value else "0"
    elif isinstance(value, (int, float)):
        etree.SubElement(c, M + "v").text = _fmt_number(value)
    else:
        text = _ILLEGAL_XML.sub("", str(value))
        c.set("t", "inlineStr")
        is_ = etree.SubElement(c, M + "is")
        t = etree.SubElement(is_, M + "t")
        t.text = text
        if text != text.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _write_block(sheet_xml, start_row, start_col, values):
    root = etree.fromstring(sheet_xml)
    sheet_data = root.find(M + "sheetData")
    rows = {int(r.get("r")): r for r in sheet_data.findall(M + "row")}

    for i, row_values in enumerate(values):
        rnum = start_row + i
        row = rows.get(rnum)
        if row is None:
            row = etree.Element(M + "row", r=str(rnum))
            later = [n for n in rows if n > rnum]
            if later:
                rows[min(later)].addprevious(row)
            else:
                sheet_data.append(row)
            rows[rnum] = row
        row.attrib.pop("spans", None)  # gợi ý tối ưu, Excel tự tính lại

        cells = {}
        for c in row.findall(M + "c"):
            ref = c.get("r")
            if ref is None:
                raise Exception(f"Dòng {rnum} có ô không ghi địa chỉ, không sửa an toàn được.")
            cells[_split_ref(ref)[0]] = c

        for j, value in enumerate(row_values):
            cnum = start_col + j
            c = cells.get(cnum)
            if c is None:
                if value is None or value == "":
                    continue
                c = etree.Element(M + "c", r=f"{_col_letter(cnum)}{rnum}")
                later = [n for n in cells if n > cnum]
                if later:
                    cells[min(later)].addprevious(c)
                else:
                    row.append(c)
                cells[cnum] = c
            _set_cell_value(c, value)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rels_path(part):
    d, f = posixpath.split(part)
    return posixpath.join(d, "_rels", f + ".rels")


def _resolve(base_part, target):
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_part), target))


def write_range(xlsx_bytes, sheet_name, start_row, start_col, values):
    """Trả về bytes của file mới sau khi ghi values (list các dòng) từ ô (start_row, start_col)."""
    zin = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
    names = zin.namelist()

    # Tìm part của workbook qua _rels/.rels
    root_rels = etree.fromstring(zin.read("_rels/.rels"))
    wb_part = next(
        _resolve("", r.get("Target")) for r in root_rels
        if r.get("Type", "").endswith("/officeDocument")
    )
    if not wb_part.endswith(".xml"):
        raise Exception(f"File không phải .xlsx dạng XML ({wb_part}); cách sửa trực tiếp chỉ dùng cho .xlsx/.xlsm.")
    wb_rels_part = _rels_path(wb_part)
    wb = etree.fromstring(zin.read(wb_part))
    wb_rels = etree.fromstring(zin.read(wb_rels_part))

    sheet = next((s for s in wb.iter(M + "sheet") if s.get("name") == sheet_name), None)
    if sheet is None:
        raise Exception(f"File không có sheet '{sheet_name}'")
    rid = sheet.get("{%s}id" % NS_REL)
    rel = next(r for r in wb_rels if r.get("Id") == rid)
    sheet_part = _resolve(wb_part, rel.get("Target"))

    replaced = {sheet_part: _write_block(zin.read(sheet_part), start_row, start_col, values)}

    # Bắt Excel tính lại toàn bộ khi mở, vì công thức ở sheet khác đang giữ giá trị cũ
    calc = wb.find(M + "calcPr")
    if calc is None:
        calc = etree.Element(M + "calcPr")
        anchor = None
        for tag in ("oleSize", "customWorkbookViews", "pivotCaches", "smartTagPr",
                    "smartTagTypes", "webPublishing", "fileRecoveryPr", "webPublishObjects", "extLst"):
            anchor = wb.find(M + tag)
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(calc)
        else:
            wb.append(calc)
    calc.set("fullCalcOnLoad", "1")
    replaced[wb_part] = etree.tostring(wb, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Bỏ calcChain (Excel tự dựng lại) để tránh lỗi "file bị hỏng" khi ô công thức bị ghi đè
    dropped = set()
    for r in list(wb_rels):
        if r.get("Type") == CALC_CHAIN_TYPE:
            dropped.add(_resolve(wb_part, r.get("Target")))
            wb_rels.remove(r)
    if dropped:
        replaced[wb_rels_part] = etree.tostring(wb_rels, xml_declaration=True, encoding="UTF-8", standalone=True)
        ct = etree.fromstring(zin.read("[Content_Types].xml"))
        for o in list(ct):
            if o.get("PartName", "").lstrip("/") in dropped:
                ct.remove(o)
        replaced["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            if info.filename in dropped:
                continue
            data = replaced.get(info.filename)
            if data is None:
                zout.writestr(info, zin.read(info.filename))
            else:
                zout.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    return out.getvalue()
