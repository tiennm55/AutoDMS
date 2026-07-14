import os
import msal
import requests
import pandas as pd
import io

def get_token():
    tenant_id = os.environ.get('TENANT_ID')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token_response['access_token']

def update_via_session():
    # 1. Đọc dữ liệu từ file input
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # Xử lý dữ liệu: Loại bỏ NaN/Inf để tránh lỗi JSON
    df = df.where(pd.notnull(df), None)
    
    # Xử lý định dạng ngày tháng (nếu có) để không bị lỗi JSON
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
    data_values = df.values.tolist()
    
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # 2. Tạo Workbook Session
    session_url = f"{base_url}:/workbook/createSession"
    session_response = requests.post(session_url, json={"persistChanges": True}, headers=headers)
    session_id = session_response.json().get('id')
    headers['workbook-session-id'] = session_id

    # 3. Cập nhật dữ liệu vào sheet DMS, vùng B6:BZ...
    last_row = 6 + len(data_values) - 1
    # Giả định cột cuối là Z, anh có thể điều chỉnh chữ cái BZ tùy theo file thực tế
    range_address = f"DMS!B6:BZ{last_row}"
    update_url = f"{base_url}:/workbook/worksheets/DMS/range(address='{range_address}')"
    
    payload = {"values": data_values}
    
    # Gửi dữ liệu
    update_response = requests.patch(update_url, json=payload, headers=headers)
    
    # 4. Đóng Session
    requests.post(f"{base_url}:/workbook/closeSession", headers=headers)

    if update_response.status_code in [200, 201, 204]:
        print("Thành công: Đã cập nhật dữ liệu qua Workbook Session.")
    else:
        print(f"Lỗi cập nhật: {update_response.text}")
        exit(1)

if __name__ == "__main__":
    update_via_session()
