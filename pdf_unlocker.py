import ctypes
import os
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter

FONT = ("微軟正黑體", 11)

selected_file_path = ""


# === 核心：不碰 GUI,才能在沒有畫面的環境下被測 ===

def open_unlocked(input_path, password):
    """開啟並解密,回傳可讀的 PdfReader;密碼不正確回傳 None。

    decrypt() 回傳 PasswordType(IntEnum),0 = 密碼不正確。
    不檢查回傳值的話,錯密碼會一路走到讀取頁面才炸出難懂的底層錯誤,
    使用者看到的是「解鎖失敗」而不是「密碼錯了」。
    （四種演算法 RC4-40 / RC4-128 / AES-128 / AES-256 正確密碼皆回傳 2、
      錯誤皆回傳 0 —— 這條由 --self-test 每次建置實際驗證,不再只是註解。）
    """
    reader = PdfReader(input_path)
    if reader.is_encrypted and not reader.decrypt(password):
        return None
    return reader


def write_copy(reader, output_path):
    """把每一頁逐一寫進新檔,而不是在原檔上動手腳——原始加密檔完整保留。"""
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)


def default_output_name(input_path):
    """'報告.pdf' → '報告_無密碼'。

    用 splitext 只動最後一個副檔名。原本的 .replace(".pdf", "_無密碼") 有兩個坑:
    'a.pdf.b.pdf' 會被換掉每一段,而大寫的 '報告.PDF' 一段都換不到——後者更糟,
    另存的預設檔名會等於原檔名,使用者直接按儲存就是覆蓋掉自己的加密原檔。
    """
    return os.path.splitext(os.path.basename(input_path))[0] + "_無密碼"


# === GUI ===

def choose_pdf():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename(
        title="選擇加密的 PDF",
        filetypes=[("PDF 檔案", "*.pdf")]
    )
    if selected_file_path:
        label_file.config(text=f"已選擇：{os.path.basename(selected_file_path)}")
    else:
        label_file.config(text="尚未選擇檔案")


def unlock_pdf():
    password = entry_password.get()

    if not selected_file_path:
        messagebox.showwarning("缺少檔案", "請先選擇一個 PDF 檔案")
        return

    if not password:
        messagebox.showwarning("缺少密碼", "請輸入 PDF 密碼")
        return

    try:
        # 先驗密碼再問存到哪:密碼錯的話不該讓使用者白挑一次儲存位置。
        reader = open_unlocked(selected_file_path, password)
        if reader is None:
            messagebox.showerror("密碼錯誤", "PDF 密碼不正確,請重新輸入。")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")],
            title="儲存解鎖後的 PDF",
            initialfile=default_output_name(selected_file_path)
        )

        if not output_path:
            return  # 使用者取消另存

        write_copy(reader, output_path)

        messagebox.showinfo("成功", f"PDF 解鎖完成！\n已儲存：{output_path}")
        os.startfile(os.path.dirname(output_path))

    except Exception as e:
        messagebox.showerror("錯誤", f"解鎖失敗：\n{str(e)}")


def main():
    global label_file, entry_password

    # plain tkinter 沒有 DPI 感知:在 >100% 顯示縮放下 Windows 會把整個視窗放大貼上,
    # 結果字是模糊的。宣告 DPI 感知後由 tkinter 自己以實體像素繪製,字就清楚了。
    # 必須在建立 Tk() 之前呼叫。shcore 需要 Win8.1+,更舊的系統退回 user32 的舊 API。
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass   # 非 Windows 或 API 不存在:維持原本行為,不影響功能

    window = tk.Tk()
    window.title("PDF Unlocker 解鎖工具")
    # 不寫死 geometry,讓 pack 依實際字級撐出視窗尺寸。
    # 宣告 DPI 感知後,寫死的像素尺寸在 150% 縮放下字變大但框沒變大,內容會被裁掉。
    # 交給 tkinter 自動計算才對任何縮放比例都成立（實測 125% 下為 452x206、100% 下 376x202,
    # 所以 README 不該再寫死一組數字）。

    label_file = tk.Label(window, text="尚未選擇檔案", font=FONT)
    label_file.pack(pady=10, padx=24)

    btn_select = tk.Button(window, text="選擇 PDF 檔案", command=choose_pdf, font=FONT)
    btn_select.pack(pady=5)

    entry_password = tk.Entry(window, show="*", width=40, font=FONT)
    entry_password.pack(pady=10, padx=24)

    btn_unlock = tk.Button(window, text="解鎖並另存 PDF", command=unlock_pdf,
                           bg="#4CAF50", fg="white", font=FONT)
    btn_unlock.pack(pady=10)

    # 所有 widget 都打包完才鎖尺寸:先讓 tkinter 算完版面,再固定視窗大小。
    window.update_idletasks()
    window.resizable(False, False)

    window.mainloop()


def self_test():
    """產生四種演算法的加密 PDF 再解回來,全過回傳 0。

    存在的理由是打包後的 exe 沒有 stdout 也沒有 CLI,CI 只能靠離開碼判斷
    .spec 的 hiddenimports 有沒有漏掉 AES 後端——而漏掉的症狀只有打包版會出現,
    原始碼永遠跑得好好的。這個函式跑的是與 GUI 完全相同的 open_unlocked / write_copy。
    """
    for algorithm in ("RC4-40", "RC4-128", "AES-128", "AES-256"):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src.pdf")
            out = os.path.join(tmp, "out.pdf")

            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            writer.encrypt("pw", algorithm=algorithm)
            with open(src, "wb") as f:
                writer.write(f)

            reader = open_unlocked(src, "pw")
            if reader is None:
                return 1                      # 正確密碼被當成錯的
            write_copy(reader, out)
            if len(PdfReader(out).pages) != 1:
                return 1                      # 寫出來的副本是壞的
            if open_unlocked(src, "wrong") is not None:
                return 1                      # 錯密碼沒被擋下
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    main()
