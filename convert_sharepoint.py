"""Đổi mọi file Excel không phải .xlsx thật (.xls, .xlsb, .xlsm, .xlt, .xltx, .xltm, .ods) trên SharePoint
(hoặc OneDrive) sang .xlsx, ngay tại chỗ. Định dạng nhận theo NỘI DUNG file, nên file .xlsb bị đặt tên .xlsx
cũng được đổi (bản gốc cất vào _goc với đúng đuôi thật).

Power Automate gọi workflow "Chuyển Excel sang .xlsx" sau khi lưu file đính kèm, truyền vào:
  SRC_SITE : tên site SharePoint, link site đầy đủ, hoặc để trống = OneDrive cá nhân
  SRC_PATH : đường dẫn FILE hoặc THƯ MỤC trong thư viện Documents
             (thư mục: xét mọi file Excel nằm ngay trong thư mục đó)
  SOURCE_ACTION : việc làm với file gốc sau khi đổi xong
             move   (mặc định) chuyển vào thư mục con "_goc" cạnh file
             delete xoá (vào thùng rác SharePoint, khôi phục được 93 ngày)
             keep   giữ nguyên

File .xlsx cùng tên, cùng thư mục, ghi đè nếu đã có.
CONVERT_MODE: full (mặc định, LibreOffice giữ công thức và định dạng) hoặc values (chỉ giá trị). Xem excel_convert.py.
"""
import os
import posixpath
import traceback

import excel_convert as xc

SITE = os.environ.get("SRC_SITE", "")
SRC_PATH = xc.norm_path(os.environ.get("SRC_PATH", ""))
SOURCE_ACTION = (os.environ.get("SOURCE_ACTION") or "move").strip().lower()
BACKUP_FOLDER = "_goc"
# full = LibreOffice, giữ công thức/định dạng (tự quay về chỉ giá trị nếu sai nhiều); values = chỉ giá trị
MODE = (os.environ.get("CONVERT_MODE") or "full").strip().lower()


def convert_one(token, drive, folder, item):
    """Trả về True nếu đã đổi, False nếu bỏ qua (đã là .xlsx thật hoặc không phải file Excel)."""
    name = item["name"]
    base, ext = posixpath.splitext(name)
    src = xc.download(token, drive, item["id"])
    fmt = xc.detect_format(src)
    if fmt == "xlsx":
        if ext.lower() == ".xlsx":
            print(f"\n{name}: đã là .xlsx thật, bỏ qua")
            return False
        # Nội dung đã là .xlsx nhưng tên sai đuôi (vd pivot_npp_202611.xls): chỉ đổi tên sang .xlsx
        out_path = posixpath.join(folder, base + ".xlsx")
        print(f"\n{name}: nội dung đã là .xlsx, chỉ đổi đuôi → {out_path}")
        xc.upload(token, drive, out_path, src)
        if SOURCE_ACTION == "delete":
            xc.delete(token, drive, item["id"])
        elif SOURCE_ACTION == "move":
            xc.move(token, drive, item["id"], xc.ensure_folder(token, drive, folder, BACKUP_FOLDER))
            print(f"  Đã chuyển file gốc vào {BACKUP_FOLDER}/")
        return True
    if fmt is None:
        print(f"\n{name}: không nhận ra là file Excel, bỏ qua")
        return False

    out_path = posixpath.join(folder, base + ".xlsx")
    same_name = ext.lower() == ".xlsx"
    print(f"\n{posixpath.join(folder, name)} (nội dung thật: .{fmt}) → {out_path}")
    data, used = xc.convert(src, "." + fmt, MODE)

    # Tên file đã là .xlsx (nội dung .xlsb/.xls...): file mới sẽ ghi đè lên chính nó,
    # nên cất bản gốc vào _goc với đúng đuôi thật trước (trừ khi chọn delete).
    if same_name and SOURCE_ACTION != "delete":
        xc.ensure_folder(token, drive, folder, BACKUP_FOLDER)
        xc.upload(token, drive, posixpath.join(folder, BACKUP_FOLDER, f"{base}.{fmt}"), src)
        print(f"  Đã cất bản gốc vào {BACKUP_FOLDER}/{base}.{fmt}")

    xc.upload(token, drive, out_path, data)
    kind = "giữ công thức, định dạng" if used == "full" else "chỉ giá trị"
    print(f"  Đã lưu {base}.xlsx ({len(data) / 1024 / 1024:.1f} MB, {kind})")

    if same_name:
        return True
    if SOURCE_ACTION == "delete":
        xc.delete(token, drive, item["id"])
        print("  Đã xoá file gốc (vào thùng rác)")
    elif SOURCE_ACTION == "move":
        backup = xc.ensure_folder(token, drive, folder, BACKUP_FOLDER)
        xc.move(token, drive, item["id"], backup)
        print(f"  Đã chuyển file gốc vào {BACKUP_FOLDER}/")
    return True


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
        print(f"Không có file Excel ở '{SRC_PATH}'.")
        return

    errors = []
    done = 0
    for it in items:
        try:
            done += convert_one(token, drive, folder, it)
        except Exception:
            # File gốc giữ nguyên, không đụng tới
            traceback.print_exc()
            errors.append(it["name"])
    print(f"\nĐã đổi {done} file, lỗi {len(errors)} file.")
    if errors:
        raise SystemExit(f"Không đổi được: {', '.join(errors)}")


if __name__ == "__main__":
    main()
