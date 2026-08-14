# PDF Unlocker

[![CI](https://github.com/HSU-YU-MING/PDFUnlocker/actions/workflows/ci.yml/badge.svg)](https://github.com/HSU-YU-MING/PDFUnlocker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](#)

**[作品介紹與開發故事](https://cornhsu.com/pdf-unlock) · MIT**

> 有些 PDF 設了開啟密碼,每次打開都得重打一次。這支小工具的用途很單純:
> 對於**你本來就知道密碼**的 PDF,輸入一次密碼,輸出一份移除密碼、日後開啟免輸入的副本。

一個不能縮放的小視窗,三個動作走完:選檔 → 輸入密碼 → 另存。
（尺寸不寫死——版面由 tkinter 依實際字級撐開,才不會在高 DPI 縮放下裁掉內容。）
原始加密檔保留不動,結果另存成新檔。

## 這不是破解工具

密碼錯了就解不開——解密交由 pypdf 把關,本工具沒有任何猜測、暴力嘗試或繞過機制。

請只用在**你自己擁有、且已經知道密碼**的檔案上。
它碰得到什麼、碰不到什麼(不連網、密碼不落地、原檔只讀)寫在 [SECURITY.md](SECURITY.md)。

## 使用方式

### 直接跑原始碼

```sh
pip install pypdf cryptography
python pdf_unlocker.py
```

`cryptography` 是 AES 加密 PDF 的解密後端。不裝的話,一般 RC4 加密的 PDF 仍然解得開,
但 AES 加密的檔案會失敗——而這正是同類工具最常見的失敗原因。

### 打包成單檔 exe

```sh
pyinstaller PDFUnlocker.spec
```

**一定要走 `.spec`,不要自己敲 pyinstaller 參數。** `--onefile` 等價選項、不帶主控台視窗、
內嵌 `version.txt` 版本資訊,還有 pypdf AES 後端的 `hiddenimports`,全都在裡面。

那五個 `hiddenimports` 目前是**保險而非必要**:pypdf 在執行期才從 `_crypt_providers`
挑後端(cryptography → pycryptodome → 無),而 2026-08-13 實測 PyInstaller 6.21.0 追得到
這條 try/except 載入鏈——清空 hiddenimports 重新打包,AES-128 / AES-256 一樣解得開。
留著是防未來版本收緊分析,因為這類問題的症狀很難查:**只有打包版會失敗、原始碼跑得好好的**。

不必相信上面這段話——每次 push 由 CI 打包後實跑驗證:

```sh
PDFUnlocker.exe --self-test
```

產生 RC4-40 / RC4-128 / AES-128 / AES-256 四種加密 PDF 各解一次(順便確認錯誤密碼會被擋下),
全過離開碼 0。這支 exe 沒有主控台,所以它只給離開碼、不印任何東西。

產物在 `dist/PDFUnlocker.exe`。

### 程式碼簽章

[Releases](https://github.com/HSU-YU-MING/PDFUnlocker/releases) 提供的執行檔已以
IV 程式碼簽章憑證(`YU-MING HSU`,SSL.com 簽發)完成數位簽章,並帶 RFC3161 時戳——
即使憑證日後到期,已簽署的檔案仍然有效。右鍵 → 內容 → 數位簽章可驗證。

自行打包後要簽章的話,執行 `sign.ps1`(需持有憑證的硬體金鑰):

```powershell
powershell -ExecutionPolicy Bypass -File sign.ps1
```

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
| 核心 | Python · pypdf(`PdfReader` / `PdfWriter`) |
| 介面 | Tkinter(檔案選擇、密碼輸入、另存對話框、訊息提示) |
| 加密支援 | cryptography——支援 AES 加密的 PDF |
| 打包 | PyInstaller `.spec`(`--onefile --noconsole` · 內嵌版本資訊) |
| 平台 / 授權 | Windows · MIT |

## 授權

MIT — 見 [LICENSE](LICENSE)。
