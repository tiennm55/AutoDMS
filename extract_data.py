import os
import msal
import requests
import math
import traceback
import datetime # Bổ sung thư viện xử lý thời gian
from urllib.parse import quote
from python_calamine import CalamineWorkbook
from xlsx_patch import write_range

# File DMS do Power Automate đẩy lên repo. Từ 11/2026 file gốc là .xlsb.
# Có DMS_Input.xlsb thì dùng file đó, không thì dùng DMS_Input.xlsx.
# Định dạng thật được nhận theo nội dung file, nên .xlsb lưu dưới tên .xlsx vẫn đọc được.
INPUT_FILES = ["DMS_Input.xlsb", "DMS_Input.xlsx"]
INPUT_SHEET = "Fundamental"
MAX_COLS = 78

USER_ID = "tiennm@tuanvietc5.id.vn"

# Các file đích trên OneDrive (đường dẫn tính từ thư mục gốc OneDrive).
# "D:\OneDrive - C5\DMS New.xlsx" trên máy = "DMS New.xlsx" ở gốc OneDrive.
TARGETS = [
    {"path": "1.Job/NPP/C5 - Report - FY2627.xlsx", "sheet": "DMS", "start_row": 6, "start_col": 2},
    {"path": "DMS New.xlsx", "sheet": "Admin", "start_row": 4, "start_col": 1},  # dán từ ô A4
]

def get_token():
    tenant_id = os.environ.get('TENANT_ID')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token_response['access_token']

def get_column_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def find_input():
    for name in INPUT_FILES:
        if os.path.exists(name):
            return name
    raise Exception(f"Không thấy file đầu vào: {' hoặc '.join(INPUT_FILES)}")


def clean_value(v):
    # Đổi giá trị ô về dạng gửi được qua Excel API, giống cách làm cũ với pandas
    if v is None or v == "":
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        if v.is_integer() and abs(v) < 2**53:
            return int(v)
    if isinstance(v, datetime.datetime):
        return str(v)
    if isinstance(v, datetime.date):
        return str(datetime.datetime(v.year, v.month, v.day))
    if isinstance(v, (datetime.time, datetime.timedelta)):
        return str(v)
    return v


def read_input_rows():
    # Đọc sheet Fundamental của file .xlsb hoặc .xlsx (python-calamine đọc được cả hai)
    path = find_input()
    with open(path, "rb") as f:
        wb = CalamineWorkbook.from_filelike(f)
        if INPUT_SHEET not in wb.sheet_names:
            raise Exception(f"File {path} không có sheet '{INPUT_SHEET}'. Các sheet đang có: {wb.sheet_names}")
        rows = wb.get_sheet_by_name(INPUT_SHEET).to_python(skip_empty_area=False)
    print(f"Đọc {path}: sheet {INPUT_SHEET} có {len(rows)} dòng")

    # Lấy từ dòng đầu tới dòng cuối có dữ liệu ở cột A, bỏ các dòng trống cột A ở giữa
    data_rows = [[clean_value(v) for v in row[:MAX_COLS]] for row in rows]
    return [row for row in data_rows if row and row[0] is not None]


def is_unsupported_workbook(response):
    # Excel API từ chối sửa file có form controls / ActiveX
    return response.status_code == 400 and (
        "UnsupportedFeatureEditWarning" in response.text or "unsupportedWorkbook" in response.text
    )


def paste_by_file(base_url, auth, target, data_values):
    # Đường dự phòng: tải file về, ghi vùng dán bằng cách sửa XML, rồi tải lên đè đúng file đó.
    # File giữ nguyên ID nên link chia sẻ và link từ file khác vẫn đúng; control, link ngoài,
    # định dạng được chép nguyên. If-Match để không ghi đè nếu ai đó vừa sửa file trong lúc chạy.
    meta = requests.get(f"{base_url}?$select=id,eTag", headers=auth, timeout=60)
    meta.raise_for_status()
    etag = meta.json()["eTag"]
    content = requests.get(f"{base_url}:/content", headers=auth, timeout=300)
    content.raise_for_status()
    new_bytes = write_range(content.content, target["sheet"], target["start_row"], target["start_col"], data_values)
    up = requests.put(
        f"{base_url}:/content",
        data=new_bytes,
        headers={**auth, "If-Match": etag,
                 "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        timeout=300,
    )
    if up.status_code not in [200, 201]:
        hint = " (file vừa bị sửa hoặc đang mở khoá, chạy lại sau)" if up.status_code in [409, 412, 423] else ""
        raise Exception(f"Upload lỗi HTTP {up.status_code}{hint}: {up.text[:300]}")


def update_preserve_link():
    try:
        # 1. Đọc và chốt vùng dữ liệu
        data_values = read_input_rows()
        if not data_values:
            print("Không có dữ liệu ở cột A để copy.")
            return

        # Dòng nào ngắn hơn thì thêm ô trống cho đủ cột
        width = max(len(row) for row in data_values)
        data_values = [row + [None] * (width - len(row)) for row in data_values]

        num_rows = len(data_values)
        num_cols = len(data_values[0]) if num_rows > 0 else 0
        
        if num_rows == 0:
            print("Không có dòng dữ liệu hợp lệ.")
            return

        # 2. Dán vào từng file đích
        token = get_token()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        errors = []
        for target in TARGETS:
            start_col_str = get_column_letter(target["start_col"])
            end_col_str = get_column_letter(target["start_col"] + num_cols - 1)
            end_row_idx = target["start_row"] + num_rows - 1
            range_address = f"{target['sheet']}!{start_col_str}{target['start_row']}:{end_col_str}{end_row_idx}"

            base_url = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/{quote(target['path'])}"
            update_url = f"{base_url}:/workbook/worksheets/{quote(target['sheet'])}/range(address='{range_address}')"

            print(f"[{target['path']}] Đang chèn dữ liệu vào vùng {range_address}...")
            patch_response = requests.patch(update_url, json={"values": data_values}, headers=headers)

            if patch_response.status_code in [200, 204]:
                print(f"[{target['path']}] Thành công: Đã dán xong dữ liệu, Link gốc được giữ nguyên an toàn!")
            elif is_unsupported_workbook(patch_response):
                print(f"[{target['path']}] Excel API không sửa được vì file có form controls/ActiveX. "
                      "Chuyển sang sửa trực tiếp file...")
                try:
                    paste_by_file(base_url, {'Authorization': headers['Authorization']}, target, data_values)
                    print(f"[{target['path']}] Thành công (sửa trực tiếp file): đã dán xong, control và link được giữ nguyên.")
                except Exception as e:
                    print(f"[{target['path']}] Sửa trực tiếp file cũng lỗi: {e}")
                    errors.append(target['path'])
            else:
                # Ghi lỗi rồi làm tiếp file sau, để một file lỗi không chặn file còn lại
                print(f"[{target['path']}] Lỗi khi đẩy qua Excel API: {patch_response.text}")
                errors.append(target['path'])

        if errors:
            raise Exception(f"Không dán được vào: {', '.join(errors)}")

    except Exception:
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    update_preserve_link()
