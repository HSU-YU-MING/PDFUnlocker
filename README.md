# PDF Unlocker

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](#)

**[作品介紹與開發故事](https://cornhsu.com/pdf-unlock.html) · MIT**

> 有些 PDF 設了開啟密碼,每次打開都得重打一次。這支小工具的用途很單純:
> 對於**你本來就知道密碼**的 PDF,輸入一次密碼,輸出一份移除密碼、日後開啟免輸入的副本。

一個 450×250 的固定視窗,三個動作走完:選檔 → 輸入密碼 → 另存。
原始加密檔保留不動,結果另存成新檔。

## 這不是破解工具

密碼錯了就解不開——解密交由 PyPDF2 把關,本工具沒有任何猜測、暴力嘗試或繞過機制。

請只用在**你自己擁有、且已經知道密碼**的檔案上。

## 使用方式

### 直接跑原始碼

```sh
pip install PyPDF2 pycryptodome
python pdf_unlocker.py
```

`pycryptodome` 是 AES 加密 PDF 的解密後端。不裝的話,一般 RC4 加密的 PDF 仍然解得開,
但 AES 加密的檔案會失敗——而這正是同類工具最常見的失敗原因。

### 打包成單檔 exe

```sh
pyinstaller --noconsole --onefile --name PDFUnlocker --version-file version.txt --hidden-import=Crypto pdf_unlocker.py
```

`--hidden-import=Crypto` 不能省:PyInstaller 的靜態分析看不到 PyPDF2 對 `Crypto` 的動態載入,
漏掉它,打包出來的 exe 一遇到 AES 加密的檔案就會失敗。
`--noconsole` 讓執行檔不帶黑色主控台視窗;`version.txt` 是內嵌的版本資訊(MIT 授權)。

產物在 `dist/PDFUnlocker.exe`。執行檔未經數位簽章,Windows SmartScreen 可能顯示
「未知發行者」,點「其他資訊 → 仍要執行」即可。

## 操作流程

| 步驟 | 動作 |
|---|---|
| 1 | 按「選擇 PDF 檔案」,挑出設了密碼的 PDF,視窗上方會顯示已選檔名 |
| 2 | 在密碼框輸入已知的開啟密碼(以圓點遮蔽顯示),按下綠色的「解鎖並另存 PDF」 |
| 3 | 選擇儲存位置——預設檔名自動帶上 `_無密碼`;完成後自動開啟所在資料夾 |

沒選檔、沒輸入密碼會先跳提示;解密或寫入出錯時,以對話框回報實際的錯誤訊息,不會默默失敗。

## 運作方式

解密後以 `PdfWriter` 把每一頁逐一寫進新檔,而不是在原檔上動手腳——
原始加密檔完整保留,產出是一份獨立的無密碼 PDF。

## 技術棧

| | |
|---|---|
| 核心 | Python · PyPDF2(`PdfReader` / `PdfWriter`) |
| 介面 | Tkinter(檔案選擇、密碼輸入、另存對話框、訊息提示) |
| 加密支援 | pycryptodome(`Crypto`)——支援 AES 加密的 PDF |
| 打包 | PyInstaller `--onefile --noconsole` · 內嵌版本資訊 |
| 平台 / 授權 | Windows · MIT |

## 授權

MIT — 見 [LICENSE](LICENSE)。
