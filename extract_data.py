import pandas as pd
import os

def process_excel_to_csv():
    input_file = 'DMS_Input.xlsx'
    output_file = 'output.csv'
    
    # Kiểm tra xem file có tồn tại không trước khi đọc
    if not os.path.exists(input_file):
        print(f"Lỗi: Không tìm thấy file {input_file}")
        exit(1)
        
    try:
        print(f"Đang xử lý file: {input_file} | Sheet: Fundamental")
        
        # Đọc file Excel trực tiếp
        # Engine 'openpyxl' là tiêu chuẩn cho .xlsx
        df = pd.read_excel(input_file, sheet_name='Fundamental', engine='openpyxl')
        
        # Chuyển đổi sang CSV với định dạng UTF-8
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"Thành công! Đã tạo file: {output_file}")
        
    except Exception as e:
        print(f"Báo lỗi: {str(e)}")
        exit(1)

if __name__ == "__main__":
    process_excel_to_csv()
