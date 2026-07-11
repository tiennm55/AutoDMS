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
    headers = {'Authorization': 'Bearer ' + token}
    
    # 1. Đọc dữ liệu Fundamental từ file input (đã có sẵn trong GitHub workspace)
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental')
    
    # 2. Tạo một file Excel tạm trong bộ nhớ để chuẩn bị upload
    # Lưu ý: Vì ta không thể "copy sheet" trực tiếp qua API, 
    # cách tốt nhất là cập nhật toàn bộ file đích bằng nội dung mới
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='DMS', index=False)
    output.seek(0)
    
    # 3. Đẩy file lên đè vào file đích trên OneDrive
    # Đường dẫn file online (dùng dấu / và %20 cho khoảng trắng)
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{target_path}:/content"
    
    response = requests.put(upload_url, data=output.getvalue(), headers={**headers, 'Content-Type': 'application/octet-stream'})
    
    if response.status_code in [200, 201]:
        print("Thành công: Đã cập nhật sheet DMS trong file online.")
    else:
        print(f"Lỗi upload: {response.status_code} - {response.text}")

if __name__ == "__main__":
    process_and_update_online()
