import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
import os

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
            reader.decrypt(password)

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
window.geometry("450x250")
window.resizable(False, False)

label_file = tk.Label(window, text="尚未選擇檔案", font=("微軟正黑體", 11))
label_file.pack(pady=10)

btn_select = tk.Button(window, text="選擇 PDF 檔案", command=choose_pdf, font=("微軟正黑體", 11))
btn_select.pack(pady=5)

entry_password = tk.Entry(window, show="*", width=40, font=("微軟正黑體", 11))
entry_password.pack(pady=10)
entry_password.insert(0, "")  # 可預設空密碼

btn_unlock = tk.Button(window, text="解鎖並另存 PDF", command=unlock_pdf, bg="#4CAF50", fg="white", font=("微軟正黑體", 11))
btn_unlock.pack(pady=10)

window.mainloop()
