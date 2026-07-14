import os
import msal
import requests
import pandas as pd
import numpy as np
import time
import io
import traceback
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
    try:
        # 1. Tìm dòng bắt đầu dữ liệu ở cột A
        wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
        ws_input = wb_input['Fundamental']
        
        start_row = 1
        for row in range(1, ws_input.max_row + 1):
            if ws_input.cell(row=row, column=1).value is not None:
                start_row = row
                break
        
        # 2. Đọc dữ liệu từ cột A đến BZ (78 cột)
        df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', skiprows=start_row - 1)
        df = df.iloc[:, :78] 
        df = df.replace([np.nan, np.inf, -np.inf], None)
        
        # 3. Tải file đích từ OneDrive
        token = get_token()
        user_id = "tiennm@tuanvietc5.id.vn" 
        target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
        base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
        headers = {'Authorization': f'Bearer {token}'}

        content_response = requests.get(f"{base_url}:/content", headers=headers)
        content_response.raise_for_status()
        
        wb_target = load_workbook(io.BytesIO(content_response.content))
        ws_target = wb_target['DMS']

        # 4. Ghi dữ liệu: Lùi 1 cột (Past vào từ B6)
        # Nguồn: Cột A (index 0) đến BZ (index 77)
        # Đích: Bắt đầu từ cột 2 (B) đến cột 79 (CA)
        data_values = df.values.tolist()
        for r_idx, row in enumerate(data_values, start=6):
            for c_idx, value in enumerate(row[:78], start=2): # start=2 nghĩa là bắt đầu từ cột B
                ws_target.cell(row=r_idx, column=c_idx, value=value)

        # 5. Upload file đã cập nhật
        save_stream = io.BytesIO()
        wb_target.save(save_stream)
        
        for attempt in range(5):
            upload = requests.put(f"{base_url}:/content", data=save_stream.getvalue(), 
                                 headers={**headers, 'Content-Type': 'application/octet-stream'})
            if upload.status_code in [200, 201]:
                print("Thành công: Đã dán dữ liệu vào từ cột B6.")
                return
            else:
                print(f"Thử lại lần {attempt+1}, mã lỗi: {upload.status_code}")
                time.sleep(30)
                
    except Exception as e:
        print("--- ĐÃ XẢY RA LỖI CHI TIẾT ---")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    update_file_securely()
