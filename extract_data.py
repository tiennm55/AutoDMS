import pandas as pd
import sys
import os

def extract_excel_to_csv(excel_file_path, sheet_name, output_csv_path):
    try:
        print(f"Đang xử lý file: {excel_file_path} | Sheet: {sheet_name}")
        
        # openpyxl đọc lõi XML của Excel, bỏ qua mọi ActiveX/Form Controls
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name, engine='openpyxl')
        
        if df.empty:
            print(f"Cảnh báo: Sheet '{sheet_name}' rỗng.")
        else:
            # Lưu ra CSV chuẩn tiếng Việt (utf-8-sig)
            df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            print(f"✅ Hoàn tất! File CSV đã lưu tại: {output_csv_path}")
            
    except Exception as e:
        print(f"❌ Báo lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Tên file quy ước (Power Automate sẽ đẩy file lên với tên này)
    input_file = "DMS_Input.xlsx" 
    target_sheet = "Fundamental"
    output_file = "DMS_Output_C5.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy file {input_file} trên repository.")
        sys.exit(1)
        
    extract_excel_to_csv(input_file, target_sheet, output_file)
