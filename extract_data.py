import os
import msal
import requests
import pandas as pd
import numpy as np

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

def update_via_session():
    # 1. Đọc dữ liệu từ file input
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # 2. Làm sạch dữ liệu để tránh lỗi JSON (NaN, Inf)
    # Thay thế NaN, Inf, -Inf bằng None (JSON null)
    df = df.replace([np.nan, np.inf, -np.inf], None)
    
    # Ép kiểu dữ liệu về dạng gốc của Python để tương thích với JSON
    df = df.astype(object)
    
    # Chuyển đổi dữ liệu sang list (thay None cho bất kỳ giá trị null nào còn sót)
    data_values = df.where(pd.notnull(df), None).values.tolist()
    
    # 3. Kết nối Graph API
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # 4. Tạo Workbook Session
    session_url = f"{base_url}:/workbook/createSession"
    session_response = requests.post(session_url, json={"persistChanges": True}, headers=headers)
    
    if session_response.status_code != 200:
        print(f"Lỗi tạo session: {session_response.text}")
        exit(1)
        
    session_id = session_response.json().get('id')
    headers['workbook-session-id'] = session_id

    # 5. Cập nhật dữ liệu vào sheet DMS, vùng B6:BZ...
    last_row = 6 + len(data_values) - 1
    range_address = f"DMS!B6:BZ{last_row}"
    update_url = f"{base_url}:/workbook/worksheets/DMS/range(address='{range_address}')"
    
    payload = {"values": data_values}
    
    # Thực hiện Patch dữ liệu
    update_response = requests.patch(update_url, json=payload, headers=headers)
    
    # 6. Đóng Session
    requests.post(f"{base_url}:/workbook/closeSession", headers=headers)

    if update_response.status_code in [200, 201, 204]:
        print("Thành công: Đã cập nhật dữ liệu qua Workbook Session.")
    else:
        print(f"Lỗi cập nhật dữ liệu: {update_response.text}")
        # Gỡ lỗi: In ra payload để kiểm tra nếu cần
        # print(f"Payload lỗi: {payload}")
        exit(1)

if __name__ == "__main__":
    update_via_session()
