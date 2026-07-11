import os
import msal
import requests
import pandas as pd
import io
from openpyxl import load_workbook

def get_token():
    tenant_id = os.environ.get('TENANT_ID')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token_response['access_token']

def update_specific_sheet():
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}'}

    # 1. Tải file từ OneDrive
    content_response = requests.get(f"{base_url}:/content", headers=headers)
    if content_response.status_code != 200:
        print(f"Lỗi tải file: {content_response.status_code} - {content_response.text}")
        exit(1)
    file_stream = io.BytesIO(content_response.content)
    
    # 2. Đọc dữ liệu từ sheet Fundamental
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # 3. Mở file Excel và cập nhật sheet DMS
    book = load_workbook(file_stream)
    ws = book['DMS'] # Đã có sẵn nên sẽ lấy trực tiếp
    
    # Xóa dữ liệu cũ từ dòng 6 trở đi
    ws.delete_rows(6, ws.max_row) 
    
    # Ghi Header vào dòng 6
    for c_idx, col_name in enumerate(df.columns, start=2):
        ws.cell(row=6, column=c_idx, value=col_name)
    
    # Ghi dữ liệu vào từ dòng 7 trở đi
    for r_idx, row in enumerate(df.values, start=7):
        for c_idx, value in enumerate(row, start=2):
            ws.cell(row=r_idx, column=c_idx, value=value)
            
    # 4. Lưu và đẩy lên lại
    save_stream = io.BytesIO()
    book.save(save_stream)
    
    upload_response = requests.put(f"{base_url}:/content", data=save_stream.getvalue(), 
                                   headers={**headers, 'Content-Type': 'application/octet-stream'})
    
    if upload_response.status_code in [200, 201]:
        print("Thành công: Đã cập nhật sheet DMS (cả Header và Dữ liệu).")
        df.to_csv('output.csv', index=False)
    else:
        print(f"Lỗi upload ({upload_response.status_code}): {upload_response.text}")
        exit(1)

if __name__ == "__main__":
    update_specific_sheet()
