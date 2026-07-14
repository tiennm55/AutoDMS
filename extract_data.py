import os
import msal
import requests
import pandas as pd
import numpy as np
import time
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

def update_via_session():
    try:
        # 1. Đọc dữ liệu từ file input và xử lý
        wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
        ws_input = wb_input['Fundamental']
        start_row = 1
        for row in range(1, ws_input.max_row + 1):
            if ws_input.cell(row=row, column=1).value is not None:
                start_row = row
                break
        df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', skiprows=start_row - 1)
        df = df.iloc[:, :78].replace([np.nan, np.inf, -np.inf], None)
        data_values = df.values.tolist()

        # 2. Setup API
        token = get_token()
        user_id = "tiennm@tuanvietc5.id.vn"
        target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
        base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # 3. Tạo Session với Retry
        for attempt in range(5):
            session_response = requests.post(f"{base_url}:/workbook/createSession", json={"persistChanges": True}, headers=headers)
            if session_response.status_code == 200:
                session_id = session_response.json().get('id')
                headers['workbook-session-id'] = session_id
                break
            time.sleep(60) # Đợi 1 phút nếu bị khóa
        else:
            raise Exception("Không thể tạo Session sau 5 lần thử.")

        # 4. Ghi dữ liệu vào B6 (cột 2)
        last_row = 6 + len(data_values) - 1
        range_address = f"DMS!B6:CA{last_row}" # B đến CA là 78 cột
        update_url = f"{base_url}:/workbook/worksheets/DMS/range(address='{range_address}')"
        requests.patch(update_url, json={"values": data_values}, headers=headers)

        # 5. Đóng Session
        requests.post(f"{base_url}:/workbook/closeSession", headers=headers)
        print("Thành công: Đã cập nhật qua Workbook Session.")

    except Exception:
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    update_via_session()
