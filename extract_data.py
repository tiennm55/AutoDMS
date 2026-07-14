import os
import msal
import requests
import pandas as pd
import numpy as np
import time
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

def update_file_securely():
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}'}

    # 1. Tải file gốc về để bảo toàn dữ liệu các sheet khác
    content_response = requests.get(f"{base_url}:/content", headers=headers)
    if content_response.status_code != 200:
        print(f"Lỗi tải file gốc: {content_response.status_code}")
        exit(1)
    
    file_stream = io.BytesIO(content_response.content)
    wb = load_workbook(file_stream)
    ws = wb['DMS']

    # 2. Đọc dữ liệu mới
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    df = df.replace([np.nan, np.inf, -np.inf], None)
    
    # 3. Dán đè dữ liệu vào sheet DMS (B6 trở đi)
    data_values = df.values.tolist()
    for r_idx, row in enumerate(data_values, start=6):
        for c_idx, value in enumerate(row, start=2):
            ws.cell(row=r_idx, column=c_idx, value=value)

    # 4. Upload lại với cơ chế thử lại (Retry) để tránh lỗi Locked/Unavailable
    save_stream = io.BytesIO()
    wb.save(save_stream)
    
    max_retries = 5
    for attempt in range(max_retries):
        upload = requests.put(f"{base_url}:/content", data=save_stream.getvalue(), 
                             headers={**headers, 'Content-Type': 'application/octet-stream'})
        
        if upload.status_code in [200, 201]:
            print("Thành công: Đã cập nhật file.")
            return
        else:
            print(f"Lần thử {attempt+1} thất bại (Status: {upload.status_code}). Đợi 30s...")
            time.sleep(30)
            
    print("Đã thử 5 lần nhưng vẫn thất bại. Vui lòng kiểm tra lại tình trạng file trên OneDrive.")
    exit(1)

if __name__ == "__main__":
    update_file_securely()
