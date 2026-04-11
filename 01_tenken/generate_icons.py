"""
PWAアイコン生成スクリプト
実行: python generate_icons.py
Pillowがインストールされていない場合: pip install Pillow
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    def make_icon(size, path):
        img = Image.new("RGB", (size, size), "#2c5f8a")
        draw = ImageDraw.Draw(img)

        # 背景円
        margin = size * 0.06
        draw.ellipse([margin, margin, size-margin, size-margin], fill="#1a7abf")

        # テキスト（大きめに「点検」）
        fs = int(size * 0.28)
        try:
            # Windows環境での日本語フォント
            font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", fs)
        except Exception:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", fs)
            except Exception:
                font = ImageFont.load_default()

        text = "点検"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) / 2
        y = (size - th) / 2 - size * 0.04
        draw.text((x, y), text, fill="white", font=font)

        # 小さく "APP" の文字
        fs2 = int(size * 0.13)
        try:
            font2 = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", fs2)
        except Exception:
            font2 = ImageFont.load_default()
        text2 = "APP"
        bbox2 = draw.textbbox((0, 0), text2, font=font2)
        tw2 = bbox2[2] - bbox2[0]
        draw.text(((size - tw2) / 2, y + th + size * 0.04), text2, fill="#c8e8ff", font=font2)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path, "PNG")
        print(f"作成: {path} ({size}x{size})")

    base = os.path.join(os.path.dirname(__file__), "static", "icons")
    make_icon(192, os.path.join(base, "icon-192.png"))
    make_icon(512, os.path.join(base, "icon-512.png"))
    print("アイコン生成完了！")

except ImportError:
    # Pillowがない場合はSVGを埋め込んだ最小PNGを手動で作成
    import struct, zlib, os

    def make_minimal_png(size, path):
        """Pillowなしで最小限のPNGを生成（単色）"""
        os.makedirs(os.path.dirname(path), exist_ok=True)

        def png_chunk(tag, data):
            c = zlib.crc32(tag + data) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)

        # 青色(#2c5f8a = 44,95,138)のRGB画像
        row = bytes([0] + [44, 95, 138] * size)
        raw = row * size
        compressed = zlib.compress(raw)

        ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n"
        png += png_chunk(b"IHDR", ihdr)
        png += png_chunk(b"IDAT", compressed)
        png += png_chunk(b"IEND", b"")

        with open(path, "wb") as f:
            f.write(png)
        print(f"作成（単色）: {path}")

    base = os.path.join(os.path.dirname(__file__), "static", "icons")
    make_minimal_png(192, os.path.join(base, "icon-192.png"))
    make_minimal_png(512, os.path.join(base, "icon-512.png"))
    print("アイコン生成完了（Pillowなし・単色版）")
    print("より見やすいアイコンにするには: pip install Pillow && python generate_icons.py")
