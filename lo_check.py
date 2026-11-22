# Tạm thời: so sánh file .xlsb gốc với .xlsx do LibreOffice tạo (sẽ xoá)
import sys, re, zipfile, datetime, collections, io
from lxml import etree
from python_calamine import CalamineWorkbook
src_path, out_path = sys.argv[1], sys.argv[2]
bad = re.compile(rb'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)')
buf = io.BytesIO()
with zipfile.ZipFile(out_path) as zi, zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        d = zi.read(it.filename)
        if it.filename.endswith(('.xml', '.rels')):
            try: etree.fromstring(d)
            except etree.XMLSyntaxError:
                d = bad.sub(b'&amp;', d); print('XML hỏng đã sửa:', it.filename)
        zo.writestr(it, d)
import openpyxl
wb = openpyxl.load_workbook(io.BytesIO(buf.getvalue()))
src = CalamineWorkbook.from_filelike(open(src_path, 'rb'))
outv = CalamineWorkbook.from_filelike(io.BytesIO(buf.getvalue()))
def norm(v):
    if v == '': return None
    if isinstance(v, float): return int(v) if v.is_integer() else round(v, 6)
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)[:10]
    if isinstance(v, datetime.time): return str(v)[:8]
    return v
T = collections.Counter()
for name in src.sheet_names:
    a = src.get_sheet_by_name(name).to_python(skip_empty_area=False)
    b = outv.get_sheet_by_name(name).to_python(skip_empty_area=False)
    ws = wb[name]
    fs = [c.value for row in ws.iter_rows() for c in row if c.data_type == 'f']
    xl = [f for f in fs if 'XLOOKUP' in str(f)]
    diff = 0; ex = []
    for i in range(max(len(a), len(b))):
        ra = a[i] if i < len(a) else []; rb = b[i] if i < len(b) else []
        for j in range(max(len(ra), len(rb))):
            va = norm(ra[j]) if j < len(ra) else None; vb = norm(rb[j]) if j < len(rb) else None
            if va == vb or (isinstance(va, (int, float)) and isinstance(vb, (int, float)) and abs(va - vb) < 1e-6 * max(1, abs(va))): continue
            diff += 1
            if len(ex) < 2: ex.append((openpyxl.utils.get_column_letter(j + 1) + str(i + 1), va, vb))
    T['f'] += len(fs); T['diff'] += diff
    print(f"{name}: formulas={len(fs)} diff={diff} xlookup_ví_dụ={xl[:1]} {ex}")
print('TỔNG', dict(T))
