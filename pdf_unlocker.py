import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter
import os

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

FONT = ("微軟正黑體", 11)

selected_file_path = ""

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
    global selected_file_path
    password = entry_password.get()

    if not selected_file_path:
        messagebox.showwarning("缺少檔案", "請先選擇一個 PDF 檔案")
        return

    if not password:
        messagebox.showwarning("缺少密碼", "請輸入 PDF 密碼")
        return

    try:
        reader = PdfReader(selected_file_path)
        if reader.is_encrypted:
            # decrypt() 回傳 PasswordType(IntEnum),0 = 密碼不正確。
            # 不檢查回傳值的話,錯密碼會一路走到讀取頁面才炸出難懂的底層錯誤,
            # 使用者看到的是「解鎖失敗」而不是「密碼錯了」。
            # (PyPDF2 3.0.1 與 pypdf 6.x 此處行為一致 —— 實測四種演算法
            #  RC4-40 / RC4-128 / AES-128 / AES-256 正確密碼皆回傳 2、錯誤皆回傳 0。)
            if not reader.decrypt(password):
                messagebox.showerror("密碼錯誤", "PDF 密碼不正確,請重新輸入。")
                return

        # 讓使用者選擇輸出位置
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")],
            title="儲存解鎖後的 PDF",
            initialfile=os.path.basename(selected_file_path).replace(".pdf", "_無密碼")
        )

        if not output_path:
            return  # 使用者取消另存

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        messagebox.showinfo("成功", f"PDF 解鎖完成！\n已儲存：{output_path}")
        os.startfile(os.path.dirname(output_path))

    except Exception as e:
        messagebox.showerror("錯誤", f"解鎖失敗：\n{str(e)}")

# === GUI ===
window = tk.Tk()
window.title("PDF Unlocker 解鎖工具")
# 不寫死 geometry,讓 pack 依實際字級撐出視窗尺寸。
# 宣告 DPI 感知後,原本的 450x250 是實體像素——在 150% 縮放下字變大但框沒變大,
# 內容會被裁掉。交給 tkinter 自動計算才對任何縮放比例都成立。
#
# resizable() 移到所有 widget 打包之後（見檔尾）並先 update_idletasks():
# 讓 tkinter 算完版面才鎖尺寸,不依賴「鎖定時剛好已算完」的隱含假設。
# （實測 100% 縮放下視窗為 376x202 / 內容區 361x164,四個元件都完整顯示。）

label_file = tk.Label(window, text="尚未選擇檔案", font=FONT)
label_file.pack(pady=10, padx=24)

btn_select = tk.Button(window, text="選擇 PDF 檔案", command=choose_pdf, font=FONT)
btn_select.pack(pady=5)

entry_password = tk.Entry(window, show="*", width=40, font=FONT)
entry_password.pack(pady=10, padx=24)
entry_password.insert(0, "")  # 可預設空密碼

btn_unlock = tk.Button(window, text="解鎖並另存 PDF", command=unlock_pdf, bg="#4CAF50", fg="white", font=FONT)
btn_unlock.pack(pady=10)

# 所有 widget 都打包完才鎖尺寸:先讓 tkinter 算完版面,再固定視窗大小。
window.update_idletasks()
window.resizable(False, False)

window.mainloop()
