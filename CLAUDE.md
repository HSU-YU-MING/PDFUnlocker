# PDFUnlocker 開發指南

plain tkinter 的 PDF 解密小工具：對**已知密碼**的 PDF 輸出一份移除密碼的副本。
支援 RC4-40 / RC4-128 / AES-128 / AES-256 四種加密。
使用者文件、操作流程、技術棧見 [README.md](README.md)；威脅模型見 [SECURITY.md](SECURITY.md)。
**這份寫的是那兩份沒寫、而下次動手前會需要的東西。**

打包、簽章、`version.txt` 的共通規則在全域 skill `python-gui-apps`
（`~/.claude/skills/python-gui-apps/SKILL.md`）——**先讀它**，這裡只寫本專案特有的。

## ⚠ 這台機器的 `python` 不能用

`python` 解析到的是 **Microsoft Store 的空殼**（`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`），
執行任何東西都可能**靜默失敗**：沒有輸出、沒有錯誤、離開碼還是 0。
用 pytest 尤其危險——它會表現得像「測試全過」。

**一律用完整路徑：**

```powershell
C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe
```

本專案**沒有 venv**（跟 FetchWeave 不同），就用上面這顆。
README 與 CI 裡寫的 `python` / `pip` 是給 GitHub runner 看的，在這台機器上都要換成完整路徑。

## 指令

以下把那顆 python 簡寫成 `$py`。

- 跑原始碼：`$py pdf_unlocker.py`
- **原始碼自我測試**：`$py pdf_unlocker.py --self-test`（四種演算法各解一次，全過離開碼 0）
- 打包：`$py -m PyInstaller PDFUnlocker.spec`——**一律走 `.spec`**，
  `--onefile` 等價選項、`console=False`、內嵌 `version.txt`、AES 後端的 `hiddenimports` 全在裡面
- **打包版自我測試**（真正該信的那個，見下節）：

```powershell
$p = Start-Process -FilePath dist\PDFUnlocker.exe -ArgumentList '--self-test' -Wait -PassThru
$p.ExitCode
```

- 版本號檢查：`$py tools\check_version.py`（四處一致）／`$py tools\check_version.py v1.0.4`（連 tag 比）
- 簽章：`powershell -ExecutionPolicy Bypass -File sign.ps1`——**用預設的 `-Target content`**，
  這個專案沒有安裝檔（`$InstallerGlob = ''`），下 `-Target installer` 會直接 throw。
  打包 → 簽一次就結束，沒有 FetchWeave 那種兩段式順序。
  ⚠ 要插 YubiKey 現場輸 PIN／觸碰，**不能代跑**。

## CI 的核心主張：不測原始碼，測打包後的 exe

`.github\workflows\ci.yml` 只有這一件事值得自動化，而它是這個專案最該被理解的設計：

> **「原始碼解得開 AES，不代表打包後的 exe 解得開。」**

打包後才會壞的東西（動態載入的加密後端、被 PyInstaller 分析漏掉的模組）**要等使用者拿到
才會發現**。所以 `frozen-selftest` job 是 `pyinstaller PDFUnlocker.spec` → 跑
`dist\PDFUnlocker.exe --self-test`，完全不跑原始碼那一份。

⚠ **它抓的是症狀，不是成因。** 別把它當成 `hiddenimports` 的守門員——它守的是
「使用者真正會遇到的那件事」，不管成因是不是 hiddenimports（見下面「五行 hiddenimports」）。

### 三條寫在 ci.yml 註解裡的實測教訓，都是踩出來的

**1. exe 是 GUI subsystem，PowerShell 不會等它結束。**
`console=False` 代表沒有 console，直接 `.\dist\PDFUnlocker.exe --self-test` 拿不到離開碼。
一定要 `Start-Process -Wait -PassThru`。同理它也**沒有 stdout**——`--self-test` 只給離開碼、
不印任何東西，別加 `print()` 期待在 CI log 裡看到。

**2. `timeout-minutes: 15` 是防呆，不能拿掉。**
2026-08-15 這個 job 真的**卡滿 6 小時**（GitHub 預設逾時）才被砍掉，清理時還留下兩個沒關掉的
`PDFUnlocker` 行程。exe 不結束 → `Start-Process -Wait` 就永遠等下去。打包約 1 分鐘、
自我測試幾秒，失敗訊號本來就該在幾分鐘內出現，沒理由讓一次卡死賠掉 6 小時。

**3. `permissions: contents: read` 不能拿掉。**
兩個 job 做的事（checkout、裝套件、打包、跑 --self-test、比對版本號）沒有一件需要寫回 GitHub。
值得修的理由不是 CodeQL 亮紅燈，是**這個 CI 會 `pip install` 第三方套件並在同一個 runner 裡
執行它們**——相依被投毒的話，惡意程式碼執行的當下就握有一把能改這個 repo 的 token。

### ⚠ `${{ github.ref_name }}` 不要改回直接內插

`version-matches-tag` job 是這樣寫的：

```yaml
- env:
    REF_NAME: ${{ github.ref_name }}
  run: python tools/check_version.py "$REF_NAME"
```

2026-08-23 安全稽核提出的硬化：直接把 `${{ }}` 內插進 `run:` 理論上可被含特殊字元的 tag 名注入。
實際只有具寫入權的人推得了 tag、workflow 又已是唯讀權限，純屬防禦縱深——
但改掉之後**六個 repo（本 repo + 四個 NuGet repo）的寫法完全一致**。
看到「經 env 繞一圈很囉唆」就改回去，會破壞那個一致性。

## 版本號：真相源是 `version.txt`，CI 兩道守門

- `version.txt` 裡有**四處**版本號（`filevers`、`prodvers`、`FileVersion`、`ProductVersion`），
  **沒有自動同步機制，要一起手改**。收不斂成一處的理由（PyInstaller 用 `eval()` 讀、
  只吃單一運算式）在 skill 與 `tools\check_version.py` 檔頭。
- **exe 內嵌版本必須等於 `version.txt`**——`frozen-selftest` 會讀
  `(Get-Item dist\PDFUnlocker.exe).VersionInfo.FileVersion` 比一次。
- **推 tag 時 tag 必須等於 `version.txt`**——`version-matches-tag` job（只在 `refs/tags/v*` 跑）。

擋的是「簽章過的 exe 帶著上一版版本號出門」。這種錯**沒有任何症狀**，要等使用者在
「內容 → 詳細資料」看到才會發現，而那時已經散布出去了。

**為什麼是 tag 跟著 `version.txt` 而不是反過來**：發版順序是
改 version.txt → PyInstaller 建置 → YubiKey 簽章 → 建 Release 順便建 tag，
**建置當下 tag 還不存在**。排在消費者後面的東西當不了真相源。
⚠ 這跟同一位作者的 NuGet 專案**規則相反**（那邊 tag 才是真相源），不要混。

發完版還有 **winget manifest** 要手動去 `microsoft/winget-pkgs` 發 PR——最容易忘的一個，
細節在 skill 的「發版之後」那節。

## 地雷

### `.spec` 的五行 `hiddenimports` 是保險，不是必要——但也別刪

`pypdf/_crypt_providers/__init__.py` 是 try/except 鏈（cryptography → pycryptodome → fallback）。
**2026-08-13 實測**（PyInstaller 6.21.0 + pypdf 6.14.2）：把 `hiddenimports` 清空重打包，
AES-128 / AES-256 **一樣解得開**，兩顆 exe 只差 118 bytes——靜態分析自己追進了 try 區塊。

所以：**留著是防未來**（pypdf 改成更動態的載入、或 PyInstaller 收緊分析），
**不是防現在**。⚠ 兩個方向都別走：不要因為「看起來多餘」刪掉，
也**不要宣稱刪了就會壞**——README 原本就是這樣寫的，2026-08-13 文件校準時被實測推翻。
（原本是 `hiddenimports=['Crypto']`，那是 PyPDF2 走 pycryptodome 時代的設定。）

### `pyinstaller==6.22.0` 不要退回 6.21.0

6.21.0 打包出來的 exe 在 `windows-latest` + Python 3.14.7 上跑 `--self-test` 會**卡住不結束**
（就是上面那個卡滿 6 小時的 run）。**沒有查根因**，因為當時同時抓到三個漏洞、本來就非升不可，
查一個馬上要丟掉的版本沒有意義。理由寫在 `requirements.txt` 裡，別把它當成可以隨手降版的數字。

### 版本要釘死，而且釘死才是重點

`requirements.txt` 存在的理由**不是「方便安裝」，是讓 Dependabot 看得見**：
`pypdf` 與 `cryptography` 是靜態包進 exe 出貨的，套件出漏洞時使用者手上那顆 exe 不會自己更新，
得等這邊重新打包發版。GitHub 只認 manifest 檔，不會去讀 workflow 裡的 `pip install` 指令。

⚠ **這個 repo 沒有 `.github\dependabot.yml`**（跟 FetchWeave 不同），
靠的是 GitHub 端開啟的 Dependabot 掃描讀 `requirements.txt`。

**釘死版本本身就抓到過問題**：在釘死之前 CI 一直是綠的，但它裝的是最新版、**比出貨的還新**
——那些綠燈從來沒證明過「使用者手上那顆 exe 沒問題」。釘死之後 CI 第一次真的測到出貨組合，
當場就卡住了。要升版就改 `requirements.txt` 的數字，讓 CI 重跑一次 `--self-test`。

⚠ **Dependabot 自動開的 PR 不一定能直接合**：1.0.4 那次它只動有漏洞的套件、不碰 `pyinstaller`，
合了 CI 一樣卡；而且它升到的是剛好補掉漏洞的版本，不是實測過的那個。

### `open_unlocked()` / `write_copy()` 不能搬回 GUI

兩個純函式不碰 GUI，GUI 全部收在 `main()` 裡、底下用 `if __name__ == "__main__"` 守著。
**這是 CI 測得到打包產物的前提**，也讓 `import pdf_unlocker` 不會彈出視窗。
`self_test()` 跑的是與 GUI **完全相同**的那兩個函式——搬回去等於讓 CI 測的東西跟使用者跑的東西
分岔。（FetchWeave 沒有這個切分。）

### `default_output_name()`：用 `splitext`，不要用 `.replace(".pdf", ...)`

原本是 `basename(path).replace(".pdf", "_無密碼")`，兩個坑：

```
my.pdf.report.pdf → my_無密碼.report_無密碼   （每一段都被換掉）
報告.PDF          → 報告.PDF                  （大寫一段都換不到）
```

第二個比較嚴重：**另存的預設檔名等於原檔名，使用者直接按儲存就是覆蓋掉自己的加密原檔**，
而 README 兩處都寫著「原始加密檔保留不動」。已改用 `os.path.splitext` 只動最後一個副檔名。

### `decrypt()` 的回傳值一定要檢查

回傳的是 `PasswordType(IntEnum)`，**0 = 密碼不正確**。不檢查的話錯密碼會一路走到讀頁面才炸出
難懂的底層錯誤，使用者看到的是「解鎖失敗」而不是「密碼錯了」。
四種演算法的正確／錯誤密碼回傳值由 `--self-test` 每次建置實際驗證，不再只是註解。

GUI 流程上是**先驗密碼再問存到哪**——密碼錯的話不該讓使用者白挑一次儲存位置。改順序前先想這件事。

### 視窗尺寸：不寫死，任何一組數字都是錯的

`main()` 裡在建立 `Tk()` **之前**呼叫 `SetProcessDpiAwareness(1)`（失敗退回 `SetProcessDPIAware()`），
連帶把 `geometry("450x250")` 拿掉——宣告 DPI 感知後寫死像素會在高縮放下裁掉內容。
現在讓 `pack` 依實際字級撐開，`update_idletasks()` 算完版面才 `resizable(False, False)`。

⚠ **不要為了讓文件對上而把固定尺寸加回去。** 實測同一份版面 100% 縮放是 376×202、
125% 是 452×206。README 那句「450×250 的固定視窗」就是這樣走鐘的，已經改成描述行為。

## 遷移狀態（不要當成待辦重做）

- **PyPDF2 → pypdf 已經完成**（2026-07）。`requirements.txt` 是 `pypdf==6.16.0`，
  加密後端從 pycryptodome 換成 `cryptography==50.0.0`，`Crypto.*` 確認 0 筆。
  動機是安全維護管道：PDF 解析器在處理不受信任的輸入，PyPDF2 3.0.1 是終版、
  之後發現的解析漏洞不會有修補。**不要再把它寫成待辦。**
- **DPI 感知已修好**，見上。

## 技術債留帳

- **沒有單元測試框架**：全部的自動化驗證就是 `--self-test` 那一支，
  而它只蓋 `open_unlocked` / `write_copy` / 四種演算法。**GUI 完全沒有自動化測試**，
  動了 `main()` 裡的任何東西只能真的把視窗開起來看。
- **`--self-test` 用的是自己產生的乾淨 PDF**，蓋不到真實世界的畸形檔、權限密碼（擁有者密碼）、
  或加了憑證加密的 PDF。
- **完全沒有深色模式**：`bg="#4CAF50"`、`fg="white"` 寫死。在 plain tkinter 上手刻主題系統
  不划算——真要做的話直接換 `customtkinter`（跟 FetchWeave 一致）比較快。詳見 skill。
- **字體 `FONT = ("微軟正黑體", 11)` 寫死在模組層級常數**。已經抽出來了，別再散回各個 widget，
  但它在沒有這套字體的系統上會退回預設字體。
- **`version.txt` 開頭沒有「請存成 UTF-8 無 BOM」的提醒**（FetchWeave 的有）。
  現況確實是無 BOM，但改檔時沒有東西提醒你——PyInstaller 讀到 BOM 會報版本資訊錯誤。
