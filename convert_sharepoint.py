"""Đổi mọi file .xls / .xlsb / .xlsm trên SharePoint (hoặc OneDrive) sang .xlsx, ngay tại chỗ.

Power Automate gọi workflow "Chuyển Excel sang .xlsx" sau khi lưu file đính kèm, truyền vào:
  SRC_SITE : tên site SharePoint, link site đầy đủ, hoặc để trống = OneDrive cá nhân
  SRC_PATH : đường dẫn FILE hoặc THƯ MỤC trong thư viện Documents
             (thư mục: đổi tất cả file .xls/.xlsb/.xlsm nằm ngay trong thư mục đó)
  SOURCE_ACTION : việc làm với file gốc sau khi đổi xong
             move   (mặc định) chuyển vào thư mục con "_goc" cạnh file
             delete xoá (vào thùng rác SharePoint, khôi phục được 93 ngày)
             keep   giữ nguyên

File .xlsx cùng tên, cùng thư mục, ghi đè nếu đã có. Chỉ giữ GIÁ TRỊ (xem excel_convert.py).
"""
import os
import posixpath
import traceback

import excel_convert as xc

SITE = os.environ.get("SRC_SITE", "")
SRC_PATH = xc.norm_path(os.environ.get("SRC_PATH", ""))
SOURCE_ACTION = (os.environ.get("SOURCE_ACTION") or "move").strip().lower()
BACKUP_FOLDER = "_goc"


def convert_one(token, drive, folder, item):
    name = item["name"]
    base, ext = posixpath.splitext(name)
    out_path = posixpath.join(folder, base + ".xlsx")
    print(f"\n{posixpath.join(folder, name)} → {out_path}")
    data = xc.to_xlsx(xc.download(token, drive, item["id"]))
    xc.upload(token, drive, out_path, data)
    print(f"  Đã lưu {base}.xlsx ({len(data) / 1024 / 1024:.1f} MB)")

    if SOURCE_ACTION == "delete":
        xc.delete(token, drive, item["id"])
        print("  Đã xoá file gốc (vào thùng rác)")
    elif SOURCE_ACTION == "move":
        backup = xc.ensure_folder(token, drive, folder, BACKUP_FOLDER)
        xc.move(token, drive, item["id"], backup)
        print(f"  Đã chuyển file gốc vào {BACKUP_FOLDER}/")


def main():
    if SOURCE_ACTION not in ("move", "delete", "keep"):
        raise SystemExit(f"SOURCE_ACTION phải là move, delete hoặc keep (đang là '{SOURCE_ACTION}')")
    token = xc.get_token()
    drive = xc.find_drive(token, SITE)
    print(f"Đường dẫn: '{SRC_PATH or '(gốc thư viện)'}'")
    item = xc.get_item(token, drive, SRC_PATH)

    if "folder" in item:
        folder = SRC_PATH
        items = [c for c in xc.list_children(token, drive, folder)
                 if "file" in c and c["name"].lower().endswith(xc.CONVERT_EXTS)]
    else:
        folder = posixpath.dirname(SRC_PATH)
        items = [item] if item["name"].lower().endswith(xc.CONVERT_EXTS) else []

    if not items:
        print(f"Không có file .xls/.xlsb/.xlsm cần đổi ở '{SRC_PATH}'.")
        return

    errors = []
    for it in items:
        try:
            convert_one(token, drive, folder, it)
        except Exception:
            traceback.print_exc()
            errors.append(it["name"])
    if errors:
        raise SystemExit(f"Không đổi được: {', '.join(errors)}")


if __name__ == "__main__":
    main()
