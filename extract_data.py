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
    # 1. Tự động tìm dòng đầu tiên có dữ liệu ở cột A trong DMS_Input.xlsx
    wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
    ws_input = wb_input['Fundamental']
    
    start_row = 1
    for row in range(1, ws_input.max_row + 1):
        if ws_input.cell(row=row, column=1).value is not None:
            start_row = row
            break
    
    # 2. Đọc file với số dòng bỏ qua động (start_row - 1)
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', skiprows=start_row - 1)
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    df = df.replace([np.nan, np.inf, -np.inf], None)
    
    # 3. Tải file gốc từ OneDrive
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}'}

    content_response = requests.get(f"{base_url}:/content", headers=headers)
    wb_target = load_workbook(io.BytesIO(content_response.content))
    ws_target = wb_target['DMS']

    # 4. Dán đè dữ liệu vào B6 (Giữ nguyên vị trí dán B6 như anh yêu cầu)
    data_values = df.values.tolist()
    for r_idx, row in enumerate(data_values, start=6):
        for c_idx, value in enumerate(row, start=2):
            ws_target.cell(row=r_idx, column=c_idx, value=value)

    # 5. Upload lại với cơ chế thử lại
    save_stream = io.BytesIO()
    wb_target.save(save_stream)
    
    for attempt in range(5):
        upload = requests.put(f"{base_url}:/content", data=save_stream.getvalue(), 
                             headers={**headers, 'Content-Type': 'application/octet-stream'})
        if upload.status_code in [200, 201]:
            print(f"Thành công: Dữ liệu đã lấy từ dòng {start_row} và dán vào B6.")
            return
        time.sleep(30)
    exit(1)

if __name__ == "__main__":
    update_file_securely()
