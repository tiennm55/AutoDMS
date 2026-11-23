"""Chuyển file DMS (.xlsb) trong repo sang .xlsx rồi lưu lên SharePoint để Power BI làm mới trên cloud.

Power BI Service không đọc được .xlsb khi không có gateway (thiếu Microsoft.ACE.OLEDB.12.0),
nên bước này tạo bản .xlsx giữ công thức và định dạng (LibreOffice, xem excel_convert.convert), giữ nguyên
tên và thứ tự sheet, để các truy vấn Power BI cũ (Item="Fundamental", ...) chạy được mà không phải sửa.
"""
import os
import traceback

import excel_convert as xc

INPUT_FILES = ["DMS_Input.xlsb", "DMS_Input.xlsx"]

# Nơi lưu file .xlsx cho Power BI: SharePoint site "tiennm", thư viện Documents,
# thư mục C5-Insight/07_dms_mo (trên máy: D:\C5\tiennm - Documents\C5-Insight\07_dms_mo).
# PBI_SITE: tên site hoặc link site đầy đủ. Để trống thì lưu vào OneDrive cá nhân.
SITE = os.environ.get("PBI_SITE", "tiennm")
OUTPUT_PATH = os.environ.get("PBI_OUTPUT_PATH", "C5-Insight/07_dms_mo/DMS CBD.xlsx")

# Chỉ chuyển các sheet này. Để trống = chuyển tất cả sheet. Ví dụ: PBI_SHEETS="Fundamental,List P3M"
SHEETS = [s.strip() for s in os.environ.get("PBI_SHEETS", "").split(",") if s.strip()]


def main():
    try:
        path = next((p for p in INPUT_FILES if os.path.exists(p)), None)
        if not path:
            raise Exception(f"Không thấy file đầu vào: {' hoặc '.join(INPUT_FILES)}")
        print(f"Chuyển {path} sang .xlsx:")
        with open(path, "rb") as f:
            src = f.read()
        if SHEETS:
            # Chỉ lấy một số sheet: dùng bản chỉ giá trị
            data, used = xc.to_xlsx(src, SHEETS), "values"
        else:
            # Giữ công thức, định dạng (LibreOffice); ô nào khác file gốc thì dán giá trị gốc.
            # Không có LibreOffice hoặc đổi hỏng thì tự quay về bản chỉ giá trị.
            fmt = xc.detect_format(src) or "xlsb"
            data, used = xc.convert(src, "." + fmt, os.environ.get("CONVERT_MODE") or "full")
        kind = "giữ công thức, định dạng" if used == "full" else "chỉ giá trị"
        print(f"Dung lượng .xlsx: {len(data) / 1024 / 1024:.1f} MB ({kind})")
        token = xc.get_token()
        item = xc.upload(token, xc.find_drive(token, SITE), OUTPUT_PATH, data)
        print(f"Đã lưu: {OUTPUT_PATH}")
        print(f"Link cho Power BI: {item.get('webUrl')}")
    except Exception:
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
