import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
import os

def unlock_pdf():
    file_path = filedialog.askopenfilename(
        title="選擇 PDF 檔案",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if not file_path:
        return

    password = password_entry.get()

    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            reader.decrypt(password)

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_path = os.path.splitext(file_path)[0] + "_無密碼.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        messagebox.showinfo("成功", f"PDF 解鎖成功！\\n儲存於：\\n{output_path}")
    except Exception as e:
        messagebox.showerror("錯誤", f"解鎖失敗：{str(e)}")

# GUI 設計
window = tk.Tk()
window.title("PDF 密碼解除工具")
window.geometry("400x180")
window.resizable(False, False)

tk.Label(window, text="請輸入 PDF 密碼：", font=("Arial", 12)).pack(pady=10)
password_entry = tk.Entry(window, show="*", font=("Arial", 12), width=30)
password_entry.pack()

tk.Button(window, text="選擇 PDF 並解鎖", font=("Arial", 12), command=unlock_pdf).pack(pady=20)

window.mainloop()
