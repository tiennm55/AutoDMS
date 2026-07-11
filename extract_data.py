import os
import msal
import requests
import pandas as pd
import io
from openpyxl import load_workbook

# 1. Hàm lấy Token (để xác thực với OneDrive)
def get_token():
    tenant_id = os.environ.get('TENANT_ID')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in token_response:
        raise Exception(f"Lỗi xác thực: {token_response.get('error_description')}")
    return token_response['access_token']

# 2. Hàm chính xử lý dữ liệu
def update_specific_sheet():
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}'}

    # A. Tải file gốc từ OneDrive về để giữ các sheet khác
    content_response = requests.get(f"{base_url}:/content", headers=headers)
    if content_response.status_code != 200:
        raise Exception("Không tải được file từ OneDrive, kiểm tra đường dẫn.")
    file_stream = io.BytesIO(content_response.content)
    
    # B. Đọc dữ liệu mới từ DMS_Input.xlsx
    # Pandas tự động lấy vùng dữ liệu từ ô đầu tiên đến ô cuối cùng có dữ liệu
    df_new = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # C. Cập nhật vào sheet 'DMS' bắt đầu từ B6
    book = load_workbook(file_stream)
    if 'DMS' not in book.sheetnames:
        book.create_sheet('DMS')
    ws = book['DMS']
    
    # Xóa dữ liệu cũ từ dòng 6 trở đi để tránh bị sót khi file mới ngắn hơn file cũ
    ws.delete_rows(6, ws.max_row) 
    
    # Ghi dữ liệu (bỏ qua header nếu anh không muốn chèn tên cột vào file đích)
    # Nếu muốn chèn tên cột, hãy để header=True
    for r_idx, row in enumerate(df_new.values, start=6):
        for c_idx, value in enumerate(row, start=2): # Bắt đầu ở cột 2 (B)
            ws.cell(row=r_idx, column=c_idx, value=value)
            
    # D. Lưu và đẩy ngược lên OneDrive
    save_stream = io.BytesIO()
    book.save(save_stream)
    
    upload_response = requests.put(f"{base_url}:/content", data=save_stream.getvalue(), 
                                   headers={**headers, 'Content-Type': 'application/octet-stream'})
    
    if upload_response.status_code in [200, 201]:
        print("Thành công: Đã cập nhật sheet DMS từ ô B6.")
        # Tạo file csv giả để Github Actions commit thành công
        df_new.to_csv('output.csv', index=False)
    else:
        print(f"Lỗi upload ({upload_response.status_code}): {upload_response.text}")
        exit(1)

if __name__ == "__main__":
    update_specific_sheet()
