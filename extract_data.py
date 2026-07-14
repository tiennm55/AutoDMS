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
        # 1. Tìm dòng bắt đầu (start_row) và dòng kết thúc (end_row) có dữ liệu ở cột A
        wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
        ws_input = wb_input['Fundamental']
        
        start_row = None
        end_row = None
        
        for row in range(1, ws_input.max_row + 1):
            if ws_input.cell(row=row, column=1).value is not None:
                if start_row is None:
                    start_row = row  # Ghi nhận dòng đầu tiên (vd: 6)
                end_row = row        # Cập nhật liên tục để lấy dòng cuối cùng (vd: 90)
        
        if start_row is None:
            print("Không có dữ liệu ở cột A để copy.")
            return

        # 2. Đọc chính xác vùng dữ liệu từ start_row đến end_row
        # skiprows = start_row - 0: Bỏ qua phần thừa bên trên
        # nrows = end_row - start_row + 1: Chỉ lấy đúng số dòng chứa dữ liệu (vd: từ 6 đến 90)
        df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', 
                           skiprows=start_row - 0, 
                           nrows=end_row - start_row + 1)
        
        # Cắt lấy 78 cột (Từ cột A đến cột BZ)
        df = df.iloc[:, :78].replace([np.nan, np.inf, -np.inf], None)

        # 3. Tải file gốc từ OneDrive để lấy cấu trúc
        token = get_token()
        user_id = "tiennm@tuanvietc5.id.vn"
        base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
        headers = {'Authorization': f'Bearer {token}'}

        content_response = requests.get(f"{base_url}:/content", headers=headers)
        content_response.raise_for_status()
        
        wb = load_workbook(io.BytesIO(content_response.content))
        ws = wb['DMS']
        
        # 4. Ghi dữ liệu: Dán bắt đầu từ ô B6
        # enumerate(..., start=6): Dòng bắt đầu dán là dòng 6
        # enumerate(..., start=2): Cột bắt đầu dán là cột 2 (Cột B)
        for r_idx, row in enumerate(df.values.tolist(), start=6):
            for c_idx, value in enumerate(row[:78], start=2):
                ws.cell(row=r_idx, column=c_idx, value=value)
        
        save_stream = io.BytesIO()
        wb.save(save_stream)

        # 5. Ghi đè file bằng chiến thuật Force-Replace
        requests.delete(base_url, headers=headers)
        upload_url = f"{base_url}:/content"
        upload = requests.put(upload_url, data=save_stream.getvalue(), headers={**headers, 'Content-Type': 'application/octet-stream'})
        
        if upload.status_code in [200, 201]:
            print(f"Thành công: Đã copy chính xác vùng A{start_row}:BZ{end_row} và dán vào từ ô B6.")
        else:
            raise Exception(f"Upload thất bại: {upload.text}")

    except Exception:
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    update_by_force_replace()
