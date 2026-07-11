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
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])['access_token']
    return token

def process_and_update_online():
    token = get_token()
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/octet-stream'}
    
    # 1. Đọc dữ liệu từ file input
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # 2. Tạo file tạm trong bộ nhớ với sheet tên là 'DMS'
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='DMS', index=False)
    
    # 3. Upload file lên OneDrive (Dùng user ID thay vì /me)
    user_id = "dia_chi_email_cua_anh@domain.com" # Thay email của anh vào đây
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    upload_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}:/content"
    
    response = requests.put(upload_url, data=output.getvalue(), headers=headers)
    
    if response.status_code in [200, 201]:
        print("Thành công: Đã cập nhật sheet DMS trong file online.")
        # Tạo thêm output.csv để GitHub Actions commit thành công
        df.to_csv('output.csv', index=False)
    else:
        print(f"Lỗi upload: {response.status_code} - {response.text}")
        exit(1)

if __name__ == "__main__":
    process_and_update_online()
