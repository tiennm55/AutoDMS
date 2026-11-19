"""Chuyển file DMS (.xlsb) trong repo sang .xlsx rồi lưu lên SharePoint để Power BI làm mới trên cloud.

Power BI Service không đọc được .xlsb khi không có gateway (thiếu Microsoft.ACE.OLEDB.12.0),
nên bước này tạo một bản .xlsx chỉ chứa giá trị (không công thức), giữ nguyên tên và thứ tự sheet,
để các truy vấn Power BI cũ (Item="Fundamental", ...) chạy được mà không phải sửa bước điều hướng.
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
            data = xc.to_xlsx(f.read(), SHEETS)
        print(f"Dung lượng .xlsx: {len(data) / 1024 / 1024:.1f} MB")
        token = xc.get_token()
        item = xc.upload(token, xc.find_drive(token, SITE), OUTPUT_PATH, data)
        print(f"Đã lưu: {OUTPUT_PATH}")
        print(f"Link cho Power BI: {item.get('webUrl')}")
    except Exception:
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
