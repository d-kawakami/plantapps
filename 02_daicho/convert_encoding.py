"""
CSV moji-code conversion script
CP932 (Windows Shift-JIS) -> UTF-8 with BOM

Usage:
  python convert_encoding.py                  # convert all CSV in current dir
  python convert_encoding.py kikilist.csv     # convert specified file
  python convert_encoding.py *.csv            # wildcard
"""

import sys
import glob
from pathlib import Path


def detect_and_convert(file_path: Path) -> bool:
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp"]

    raw = file_path.read_bytes()

    if raw[:3] == b"\xef\xbb\xbf":
        print(f"[SKIP] {file_path.name} - already UTF-8 BOM")
        return True

    for enc in encodings:
        try:
            text = raw.decode(enc)
            file_path.write_text(text, encoding="utf-8-sig", newline="")
            print(f"[OK]   {file_path.name} - {enc} -> UTF-8 BOM")
            return True
        except (UnicodeDecodeError, LookupError):
            continue

    print(f"[ERR]  {file_path.name} - encoding detection failed")
    return False


def main():
    args = sys.argv[1:]

    if not args:
        targets = list(Path(".").glob("*.csv"))
    else:
        targets = []
        for arg in args:
            matched = [Path(p) for p in glob.glob(arg)]
            if matched:
                targets.extend(matched)
            else:
                targets.append(Path(arg))

    if not targets:
        print("No CSV files found.")
        return

    ok = sum(detect_and_convert(p) for p in targets if p.is_file())
    print(f"\nDone: {ok}/{len(targets)} file(s) converted.")


if __name__ == "__main__":
    main()
