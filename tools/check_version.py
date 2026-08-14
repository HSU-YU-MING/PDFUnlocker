"""比對 git tag 與 version.txt 裡的四個版本號,不一致就讓 CI 紅燈。

為什麼是「檢查」而不是「同步」:
version.txt 才是版本號真正被消費的地方——它會嵌進 exe、顯示在「內容 → 詳細資料」,
winget manifest 也照它填。tag 反而排在後面:發版順序是
「改 version.txt → PyInstaller 建置 → YubiKey 簽章 → 建 Release 順便建 tag」,
建置當下新 tag 還不存在。排在消費者後面的東西當不了真相源,所以不做自動生成。

為什麼那四個版本號不能在 version.txt 裡收斂成一處:
PyInstaller 是用 eval() 讀這個檔（utils/win32/versioninfo.py），只吃單一運算式,
放不進變數賦值。要收斂只能寫成 lambda 之類的花招,不值得——從外面檢查便宜得多。

擋的是什麼:簽章過的 exe 帶著上一版的版本號出門。這種錯不會有任何症狀,
要等使用者在檔案內容裡看到 1.0.2 卻裝著 1.0.3 才會發現,而那時已經散布出去了。

用法:
    python tools/check_version.py v1.0.3     # CI:連 tag 一起比
    python tools/check_version.py            # 本機:只檢查四處彼此一致
"""
import os
import re
import sys

VERSION_FILE = os.path.join(os.path.dirname(__file__), os.pardir, "version.txt")

PATTERNS = {
    "filevers": r"filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)",
    "prodvers": r"prodvers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)",
    "FileVersion": r"StringStruct\('FileVersion',\s*'([\d.]+)'\)",
    "ProductVersion": r"StringStruct\('ProductVersion',\s*'([\d.]+)'\)",
}


def main(argv):
    with open(VERSION_FILE, encoding="utf-8") as f:
        text = f.read()

    found = {}
    for name, pattern in PATTERNS.items():
        match = re.search(pattern, text)
        if not match:
            print(f"FAIL: version.txt 找不到 {name}——格式被改過了,這支檢查也要跟著改")
            return 1
        found[name] = ".".join(match.groups()) if len(match.groups()) > 1 else match.group(1)

    distinct = set(found.values())
    if len(distinct) != 1:
        print("FAIL: version.txt 內部四處版本號不一致")
        for name, value in found.items():
            print(f"  {name:15s} = {value}")
        return 1

    version = distinct.pop()
    print(f"version.txt = {version}")

    if len(argv) < 2:
        return 0

    # tag 是 v1.0.3,version.txt 是四段的 1.0.3.0——比對前先補齊到四段。
    tag = argv[1]
    expected = tag.lstrip("vV").split(".")
    if len(expected) == 3:
        expected.append("0")
    expected = ".".join(expected)

    if version != expected:
        print(f"FAIL: tag {tag} 期望 {expected},但 version.txt 是 {version}")
        print("      發版前忘了改 version.txt,或 tag 打錯了。")
        return 1

    print(f"OK: tag {tag} 與 version.txt 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
