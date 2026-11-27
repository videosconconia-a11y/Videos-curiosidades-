# Portada (1080x1920) y storyboard (hoja con un fotograma por plano).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render as R
from PIL import Image, ImageDraw, ImageFilter
from base import font, FB, FXB, FM, ctext, fit_font, rgba
from script_data import SHOTS

def cover():
    t = 0.9
    img = R.shot("hook", t, 0.0, 1.95)
    img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 70)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 250, 1020, 640], 40, fill=(255, 214, 0, 255), outline=(20, 20, 30, 255), width=8)
    ctext(d, 280, "LE ESTÁN ROBANDO…", fit_font(d, "LE ESTÁN ROBANDO…", FB, 92, 880), (20, 20, 30, 255))
    ctext(d, 400, "Y ÉL EXPLICA", font(FB, 92), (20, 20, 30, 255))
    ctext(d, 515, "QUÉ ES UNA NFC", fit_font(d, "QUÉ ES UNA NFC", FB, 92, 880), (220, 30, 60, 255))
    d.rounded_rectangle([300, 1450, 780, 1560], 55, fill=(10, 14, 28, 235))
    ctext(d, 1468, "Melilla · 30 €", font(FB, 60), (255, 255, 255, 255))
    img.convert("RGB").save(os.path.join(HERE, "portada.jpg"), quality=92)

def storyboard():
    cols, tw, th = 6, 300, 533
    rows = (len(SHOTS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 70)), (16, 18, 26)); d = ImageDraw.Draw(sheet)
    for i, (a, b, name) in enumerate(SHOTS):
        tt = a + (b - a) * 0.6
        fr = R.frame(tt, int(tt * 30)).resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + 70)
        sheet.paste(fr, (x, y + 70))
        d.text((x + 10, y + 8), f"{i + 1:02}  {a:.1f}–{b:.1f} s", font=font(FM, 22), fill=(255, 214, 0))
        d.text((x + 10, y + 36), name, font=font(FXB, 22), fill=(230, 235, 245))
    sheet.save(os.path.join(HERE, "storyboard.jpg"), quality=88)

if __name__ == "__main__":
    cover(); storyboard(); print("portada.jpg y storyboard.jpg")
