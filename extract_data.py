import os
import msal
import requests
import pandas as pd
import numpy as np
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

def update_by_force_replace():
    try:
        # 1. Đọc và làm sạch dữ liệu như cũ
        wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
        ws_input = wb_input['Fundamental']
        start_row = next((row for row in range(1, ws_input.max_row + 1) if ws_input.cell(row=row, column=1).value is not None), 1)
        
        df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', skiprows=start_row - 1)
        df = df.iloc[:, :78].replace([np.nan, np.inf, -np.inf], None)

        # 2. Setup API
        token = get_token()
        user_id = "tiennm@tuanvietc5.id.vn"
        base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
        headers = {'Authorization': f'Bearer {token}'}

        # 3. Tải file về để lấy cấu trúc
        content_response = requests.get(f"{base_url}:/content", headers=headers)
        wb = load_workbook(io.BytesIO(content_response.content))
        ws = wb['DMS']
        for r_idx, row in enumerate(df.values.tolist(), start=6):
            for c_idx, value in enumerate(row[:78], start=2):
                ws.cell(row=r_idx, column=c_idx, value=value)
        
        save_stream = io.BytesIO()
        wb.save(save_stream)

        # 4. CHIẾN THUẬT FORCE-REPLACE: Xóa file cũ trước khi upload file mới
        # Xóa file cũ
        requests.delete(base_url, headers=headers)
        
        # Upload file mới với cùng tên
        upload_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx:/content"
        upload = requests.put(upload_url, data=save_stream.getvalue(), headers={**headers, 'Content-Type': 'application/octet-stream'})
        
        if upload.status_code in [200, 201]:
            print("Thành công: Đã xóa file cũ và ghi đè file mới.")
        else:
            raise Exception(f"Upload thất bại sau khi xóa: {upload.text}")

    except Exception:
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    update_by_force_replace()
