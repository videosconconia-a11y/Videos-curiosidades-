# Descarga las fotos de Wikimedia Commons usadas en render.py (miniaturas de 1920 px) y guarda autor/licencia en img/meta.json.
# Uso: python3 fetch_images.py   (respeta los límites de Wikimedia; puede tardar unos minutos)
import json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img"); os.makedirs(OUT, exist_ok=True)
src = open(os.path.join(HERE, "render.py"), encoding="utf-8").read(); i = src.index("PHOTO = {")
PHOTO = eval(src[i + 8: src.index("}", i) + 1])
UA = {"User-Agent": "VideoBuilder/1.0 (educational video generator)"}
def slug(t): return re.sub(r"[^a-z0-9]+", "_", t.lower())[:50].strip("_")
def get(url, raw=False):
    for k in range(10):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read() if raw else json.load(r)
        except Exception as e:
            print("reintento:", e, flush=True); time.sleep(10 + 10 * k)
mp = os.path.join(OUT, "meta.json"); meta = json.load(open(mp)) if os.path.exists(mp) else {}
for t in PHOTO.values():
    s = slug(t); fp = os.path.join(OUT, s + ".jpg")
    if os.path.exists(fp) and s in meta: continue
    d = get("https://commons.wikimedia.org/w/api.php?action=query&format=json&titles=" + urllib.parse.quote("File:" + t)
            + "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1920&iiextmetadatafilter=LicenseShortName|Artist")
    ii = list(d["query"]["pages"].values())[0]["imageinfo"][0]; m = ii.get("extmetadata", {})
    if not os.path.exists(fp):
        data = get(ii["thumburl"], raw=True)
        if not data or data[:2] != b"\xff\xd8": print("fallo", t); continue
        open(fp, "wb").write(data)
    meta[s] = dict(title="File:" + t, page=ii["descriptionurl"], lic=m.get("LicenseShortName", {}).get("value"),
                   artist=re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip())
    json.dump(meta, open(mp, "w"), ensure_ascii=False, indent=1); print("ok", t, flush=True); time.sleep(6)
