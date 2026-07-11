import os
import msal
import requests
import pandas as pd
import io

def get_token():
    # Lấy thông tin từ GitHub Secrets
    tenant_id = os.environ.get('TENANT_ID')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, 
        authority=authority, 
        client_credential=client_secret
    )
    
    # Lấy token cho quyền ứng dụng
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in token_response:
        raise Exception(f"Lỗi xác thực: {token_response.get('error_description')}")
    return token_response['access_token']

def process_and_update():
    token = get_token()
    
    # 1. Đọc dữ liệu từ file input (DMS_Input.xlsx)
    # Lấy dữ liệu từ sheet 'Fundamental'
    df = pd.read_excel('DMS_Input.xlsx', sheet_name='Fundamental', engine='openpyxl')
    
    # 2. Tạo nội dung file Excel mới trong bộ nhớ với sheet 'DMS'
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='DMS', index=False)
    
    # 3. Upload file lên OneDrive/SharePoint
    # Thay 'tiennm@tuanvietc5.id.vn' bằng email tài khoản Microsoft 365 của anh
    user_id = "tiennm@tuanvietc5.id.vn" 
    # Đường dẫn file trên OneDrive
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    upload_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}:/content"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/octet-stream'
    }
    
    response = requests.put(upload_url, data=output.getvalue(), headers=headers)
    
    if response.status_code in [200, 201]:
        print("Thành công: Đã cập nhật sheet DMS trong file online.")
        # Tạo file csv để Workflow commit thành công
        df.to_csv('output.csv', index=False)
    else:
        print(f"Lỗi upload ({response.status_code}): {response.text}")
        exit(1)

if __name__ == "__main__":
    process_and_update()
