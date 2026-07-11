import os
import msal
import requests
import io
from openpyxl import load_workbook

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

def copy_and_paste_overwrite():
    # 1. Đọc vùng dữ liệu động từ file DMS_Input.xlsx (Sheet Fundamental)
    wb_input = load_workbook('DMS_Input.xlsx', data_only=True)
    ws_input = wb_input['Fundamental']
    
    # Tự động tìm dòng đầu tiên có dữ liệu tại cột A
    start_row = None
    for row in range(1, ws_input.max_row + 1):
        if ws_input.cell(row=row, column=1).value is not None:
            start_row = row
            break
            
    if start_row is None:
        print("Không tìm thấy dữ liệu ở cột A trong file input!")
        return

    # Lấy dữ liệu động từ ô đầu tiên cột A đến hết dòng, sang phải đến hết cột có dữ liệu
    data_matrix = []
    for r in range(start_row, ws_input.max_row + 1):
        row_data = []
        for c in range(1, ws_input.max_column + 1):
            row_data.append(ws_input.cell(row=r, column=c).value)
        data_matrix.append(row_data)

    # 2. Tải file đích trên OneDrive về
    token = get_token()
    user_id = "tiennm@tuanvietc5.id.vn" 
    target_path = "1.Job/NPP/C5%20-%20Reporting%20Day%20-%202026.xlsx"
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{target_path}"
    headers = {'Authorization': f'Bearer {token}'}

    content_response = requests.get(f"{base_url}:/content", headers=headers)
    if content_response.status_code != 200:
        print(f"Lỗi tải file gốc: {content_response.status_code}")
        exit(1)
        
    file_stream = io.BytesIO(content_response.content)
    wb_target = load_workbook(file_stream)
    ws_target = wb_target['DMS'] # Lấy đúng sheet DMS có sẵn

    # 3. DÁN ĐÈ TRỰC TIẾP (Không xóa dữ liệu cũ trước đó)
    # Bắt đầu dán từ dòng 6, cột B (Cột 2)
    target_start_row = 6
    target_start_col = 2 

    for r_idx, row_values in enumerate(data_matrix):
        for c_idx, value in enumerate(row_values):
            ws_target.cell(
                row=target_start_row + r_idx, 
                column=target_start_col + c_idx, 
                value=value
            )

    # 4. Lưu lại và upload ngược lên OneDrive
    save_stream = io.BytesIO()
    wb_target.save(save_stream)
    
    upload_response = requests.put(
        f"{base_url}:/content", 
        data=save_stream.getvalue(), 
        headers={**headers, 'Content-Type': 'application/octet-stream'}
    )
    
    if upload_response.status_code in [200, 201]:
        print("Thành công: Đã dán đè dữ liệu động vào ô B6 sheet DMS.")
        # Tạo file phụ để workflow kết thúc tốt đẹp
        with open('output.csv', 'w') as f:
            f.write('success')
    else:
        print(f"Lỗi upload ({upload_response.status_code}): {upload_response.text}")
        exit(1)

if __name__ == "__main__":
    copy_and_paste_overwrite()
