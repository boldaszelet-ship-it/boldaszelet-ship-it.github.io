#!/usr/bin/env python3
"""A „Valóban?” weboldal építője: a YouTube nyilvános RSS-éből frissíti a videólistát, és statikus HTML-t ír.

    python3 tools/valoban/epit.py            # csak a meglévő adatból épít
    python3 tools/valoban/epit.py --frissit  # RSS + elérhetőség-ellenőrzés, utána épít (ezt futtatja a GitHub Action)

Nincs szükség kulcsra, és az oldal nem tölt be külső forrást: a borítók és a betűk a repóból jönnek, így nincs süti és
nincs harmadik fél a látogató böngészőjében. Az `adatvedelem.html` és a `profil.png` kézi fájl, ez a szkript nem írja.
"""
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

GYOKER = Path(__file__).resolve().parents[2]
ADAT = Path(__file__).with_name("videok.json")
WEB = GYOKER / "valoban"
BOLD = "https://valoban.pages.dev/"  # a GitHub-cím is él: a Google és a TikTok arra hivatkozik
CSATORNA = "UC7E2Nop5attkRyAdKO_RPlA"
RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={CSATORNA}"
YT = "https://www.youtube.com/@valobanhun"
FB = "https://www.facebook.com/profile.php?id=61594155817912"
TT = "https://www.tiktok.com/@valobanhun"
BP = ZoneInfo("Europe/Budapest")
HONAP = "január február március április május június július augusztus szeptember október november december".split()
UA = {"User-Agent": "Mozilla/5.0 (valoban-weboldal)"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "m": "http://search.yahoo.com/mrss/"}
BEMUTATO = {"AYiHXjghiBo"}  # a csatornabemutató 16:9, nem rész
E = lambda s: html.escape(str(s), quote=True)


def letolt(url, ido=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=ido) as r:
        return r.read()


def rss_olvas():
    for p in range(4):
        try:
            gy = ET.fromstring(letolt(RSS))
            break
        except Exception as e:  # a YouTube a felhős IP-kről néha 404-et vagy 500-at ad
            print(f"RSS hiba ({p + 1}/4): {e}", file=sys.stderr)
            time.sleep(20)
    else:
        return None
    ki = []
    for b in gy.findall("a:entry", NS):
        g = b.find("m:group", NS)
        link = b.find("a:link", NS).get("href")
        ts = dt.datetime.fromisoformat(b.find("a:published", NS).text)
        ki.append({"id": b.find("yt:videoId", NS).text, "cim": b.find("a:title", NS).text,
                   "leiras": g.find("m:description", NS).text or "", "ts": int(ts.timestamp()),
                   "tipus": "shorts" if "/shorts/" in link else "hosszu"})
    return ki


def elerheto(vid):
    """False csak akkor, ha a YouTube kimondja, hogy nincs (törölt vagy privát); hálózati hibán None."""
    url = f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={vid}"
    try:
        letolt(url, 10)
        return True
    except urllib.error.HTTPError as e:
        return False if e.code in (401, 403, 404) else None
    except Exception:
        return None


def frissit(videok):
    regi = {v["id"]: v for v in videok}
    friss = rss_olvas()
    if friss is None:
        legujabb = max(v["ts"] for v in videok)
        if time.time() - legujabb > 2 * 86400:  # így a tulajdonos kap GitHub-levelet, nem némán avul az oldal
            sys.exit("Az RSS nem olvasható, és 2 napja nincs új videó az oldalon.")
        return videok
    for v in friss:
        v["rejtett"] = False
        if v["id"] in regi:
            regi[v["id"]].update(v)
        else:
            regi[v["id"]] = v
    # a lekerült videó az oldalról is lekerül; ha az eredmény gyanús (blokkolt IP), nem nyúlunk semmihez
    allapot = {i: elerheto(i) for i in regi}
    nincs = [i for i, a in allapot.items() if a is False]
    if len(nincs) > max(3, len(regi) // 5):
        print(f"Gyanús: {len(nincs)} videó nem elérhető, nem rejtek el semmit.", file=sys.stderr)
    else:
        for i, a in allapot.items():
            if a is not None:
                regi[i]["rejtett"] = not a
    return sorted(regi.values(), key=lambda v: -v["ts"])


def kep(v):
    cel = WEB / "k" / f"{v['id']}.jpg"
    if cel.exists():
        return
    meret = (360, 640) if v["tipus"] == "shorts" else (640, 360)
    nevek = ["oar2", "oar3", "maxresdefault", "hq720", "hqdefault"] if v["tipus"] == "shorts" else ["maxresdefault", "hq720", "hqdefault"]
    for n in nevek:
        try:
            k = Image.open(BytesIO(letolt(f"https://i.ytimg.com/vi/{v['id']}/{n}.jpg"))).convert("RGB")
        except Exception:
            continue
        w, h = k.size
        ar = meret[0] / meret[1]
        if w / h > ar:
            uj = int(h * ar)
            k = k.crop(((w - uj) // 2, 0, (w + uj) // 2, h))
        else:
            uj = int(w / ar)
            k = k.crop((0, (h - uj) // 2, w, (h + uj) // 2))
        cel.parent.mkdir(exist_ok=True)
        k.resize(meret, Image.LANCZOS).save(cel, quality=74, optimize=True, progressive=True)
        return
    print(f"Nincs borító: {v['id']}", file=sys.stderr)


def tiszta_cim(c):
    c = re.sub(r"\s*·\s*Valóban\?\s*(#\d+)?\s*$", "", c)
    c = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️‍]", "", c)
    return re.sub(r"\s{2,}", " ", c).strip()


def bont(leiras):
    """A YouTube-leírásból: bekezdések, források, kreditek, gépi-hang közlés."""
    bek, forras, kredit, gep = [], [], [], []
    hol = "szoveg"
    for s in leiras.splitlines():
        s = s.strip()
        if not s or s.startswith(("🔔", "#")) or re.match(r"\d{1,2}:\d\d ", s):
            continue
        k = s.lower()
        if "iratkozz fel" in k or k.endswith("honnan tudjuk.") or k.startswith(("mit ellenőrizzünk", "„valóban?” –", "„valóban?” -")):
            continue
        m = re.match(r"forrás\s*:\s*(.*?)\s*(https?://\S+)$", s, re.I)
        if m:
            forras.append((m.group(1).rstrip(" :–-") or m.group(2), m.group(2)))
            continue
        if re.match(r"(források|forrasok)\s*:?$", k):
            hol = "forras"
            continue
        if k.startswith("kreditek") or k.startswith("képek (wikimed"):
            hol = "kredit"
            kredit.append(s) if len(s) > 12 and not s.endswith(":") and "kreditek" not in k else None
            continue
        if "gépi hang" in k or "mesterséges intelligencia" in k or "narráció szintetikus" in k:
            gep.append(s)
            continue
        if hol == "forras":
            m = re.search(r"https?://\S+", s)
            if m:
                nev = re.sub(r"^[•·\-–]\s*", "", s[:m.start()]).rstrip(" :–-")
                forras.append((nev or m.group(0), m.group(0)))
            else:
                hol = "kredit"
                kredit.append(s)
        elif hol == "kredit":
            kredit.append(s)
        else:
            bek.append(s)
    return bek, forras, kredit, gep


def linkes(s):
    ki, poz = [], 0
    for m in re.finditer(r"https?://[^\s<>]+", s):
        ki += [E(s[poz:m.start()]), f'<a href="{E(m.group(0))}" rel="noopener nofollow">{E(m.group(0))}</a>']
        poz = m.end()
    return "".join(ki) + E(s[poz:])


def datum(ts):
    d = dt.datetime.fromtimestamp(ts, BP)
    return f"{d.year}. {HONAP[d.month - 1]} {d.day}."


def hossz(mp):
    return f"{mp // 60}:{mp % 60:02d}" if mp else ""


def kartya(v, elo=""):
    kis = v["tipus"] == "shorts"
    meta = " · ".join(x for x in (datum(v["ts"]), hossz(v.get("mp", 0)), "Shorts" if kis else "") if x)
    w, h = (360, 640) if kis else (640, 360)
    return (f'<li class="kartya{" allo" if kis else ""}" data-t="{v["tipus"]}" data-q="{E(tiszta_cim(v["cim"]).lower())}">'
            f'<a href="{elo}v/{v["id"]}.html"><img src="{elo}k/{v["id"]}.jpg" width="{w}" height="{h}" alt="" loading="lazy">'
            f'<span class="cim">{E(tiszta_cim(v["cim"]))}</span><span class="meta">{E(meta)}</span></a></li>')


def lap(cim, leiras, tartalom, utvonal, elo="", kep_ut="profil.png", extra=""):
    return f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(cim)}</title>
<meta name="description" content="{E(leiras)}">
<link rel="canonical" href="{BOLD}{utvonal}">
<link rel="icon" href="{elo}profil.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="hu_HU">
<meta property="og:site_name" content="Valóban?">
<meta property="og:title" content="{E(cim)}">
<meta property="og:description" content="{E(leiras)}">
<meta property="og:url" content="{BOLD}{utvonal}">
<meta property="og:image" content="{BOLD}{kep_ut}">
<meta name="theme-color" content="#07192e">
<link rel="preload" href="{elo}f/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{elo}s.css">{extra}
</head>
<body>
<a class="ugras" href="#tartalom">Ugrás a tartalomra</a>
<header class="fej"><a class="marka" href="{elo or './'}"><img src="{elo}profil.png" width="40" height="40" alt=""><span>Valóban<i>?</i></span></a>
<nav aria-label="Fő"><a href="{elo}videok.html">Videók</a><a href="{elo or './'}#igy">Így dolgozunk</a><a class="yt" href="{YT}" rel="noopener">YouTube</a></nav></header>
<main id="tartalom">
{tartalom}
</main>
<footer class="lab"><div>
<p class="koveto"><a href="{YT}" rel="noopener">YouTube</a><a href="{TT}" rel="noopener">TikTok</a><a href="{FB}" rel="noopener">Facebook</a></p>
<p>Üzemeltető: Boldurián Gábor, 1191 Budapest, Dobó Katica utca 13. · <a href="mailto:boldaszelet@gmail.com">boldaszelet@gmail.com</a> · Tárhely: GitHub, Inc. · Kiszolgálás: Cloudflare, Inc.</p>
<p><a href="{elo}adatvedelem.html">Adatkezelési tájékoztató</a> · Az oldal nem használ sütit és látogatómérést.</p>
</div></footer>
</body>
</html>
"""


def kezdolap(v):
    hosszu = [x for x in v if x["tipus"] == "hosszu" and x["id"] not in BEMUTATO]
    shorts = [x for x in v if x["tipus"] == "shorts"]
    fo = next((x for x in v if x["id"] in BEMUTATO), hosszu[0])
    t = f"""<section class="hos"><div class="hos-sz">
<h1>Valóban<i>?</i></h1>
<p class="szlog">Végére járunk.</p>
<p class="lede">Magyar ismeretterjesztő csatorna. Ismert történeteket és állításokat ellenőrzünk, rangsorokat és érdekességeket gyűjtünk, és mindig megmondjuk, honnan tudjuk.</p>
<p class="gombok"><a class="gomb" href="{YT}?sub_confirmation=1" rel="noopener">Feliratkozom</a><a class="gomb masod" href="videok.html">Mind a {len(v)} videó</a></p>
</div>
<a class="kiemelt" href="v/{fo['id']}.html"><img src="k/{fo['id']}.jpg" width="640" height="360" alt=""><span class="cimke">Kezdd itt</span><span class="cim">{E(tiszta_cim(fo['cim']))}</span></a>
</section>
<section><div class="sor"><h2>Hosszú részek</h2><a href="videok.html#hosszu">Összes</a></div>
<ul class="racs">{''.join(kartya(x) for x in hosszu[:6])}</ul></section>
<section><div class="sor"><h2>Legújabb Shorts-videók</h2><a href="videok.html#shorts">Összes</a></div>
<ul class="racs szuk">{''.join(kartya(x) for x in shorts[:12])}</ul></section>
<section id="igy" class="igy"><h2>Így dolgozunk</h2><ol>
<li><b>Egy téma, világos válasz</b>Minden rész egy kérdésre, állításra vagy rangsorra épül. Nem az a cél, hogy jól hangozzon, hanem hogy kiderüljön, mi igaz.</li>
<li><b>A források nyilvánosak</b>Minden videónál felsoroljuk, honnan tudjuk, amit mondunk, így bárki utánanézhet. Itt az oldalon is, videónként.</li>
<li><b>Nyíltan a gépi hangról</b>A narrációt gép olvassa fel, nem ember. Ezt minden videó leírásában közöljük.</li>
</ol><p class="hiba">Hibát találtál? Írd meg: <a href="mailto:boldaszelet@gmail.com">boldaszelet@gmail.com</a></p></section>
<section class="app"><h2>A feltöltő alkalmazásról</h2><p>A „Valoban Feltolto” a csatorna saját, belső eszköze: a YouTube Data API-n keresztül tölti fel és ütemezi a csatorna saját videóit. Más felhasználók nem használják, és más fiók adataihoz nem fér hozzá. Részletek: <a href="adatvedelem.html">adatkezelési tájékoztató</a>.</p></section>"""
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Valóban?", "url": BOLD, "inLanguage": "hu",
                     "publisher": {"@type": "Organization", "name": "Valóban?", "logo": BOLD + "profil.png", "sameAs": [YT, TT, FB]}},
                    ensure_ascii=False)
    return lap("Valóban? – magyar ismeretterjesztő csatorna",
               "Valóban? – magyar ismeretterjesztő csatorna: ismert történetek, állítások és rangsorok, forrásokkal. Végére járunk.",
               t, "", extra=f'\n<script type="application/ld+json">{ld}</script>')


def archivum(v):
    t = f"""<section class="archiv"><h1>Videók</h1>
<form class="szuro" role="search" onsubmit="return false"><label for="q">Keresés a címekben</label><input id="q" type="search" autocomplete="off" placeholder="Például: korona, Balaton, polip">
<div class="fulek" role="group" aria-label="Videótípus"><button type="button" data-f="" aria-pressed="true">Mind</button><button type="button" data-f="hosszu" aria-pressed="false">Hosszú részek</button><button type="button" data-f="shorts" aria-pressed="false">Shorts</button></div></form>
<p id="db" class="meta" aria-live="polite">{len(v)} videó</p>
<ul id="lista" class="racs vegyes">{''.join(kartya(x) for x in v)}</ul></section>
<script>
(function(){{var q=document.getElementById('q'),db=document.getElementById('db'),k=[].slice.call(document.querySelectorAll('#lista>li')),g=[].slice.call(document.querySelectorAll('.fulek button')),f=(location.hash||'').slice(1);
if(f!=='hosszu'&&f!=='shorts')f='';
function m(){{var s=q.value.trim().toLowerCase(),n=0;k.forEach(function(e){{var i=(!f||e.dataset.t===f)&&e.dataset.q.indexOf(s)>-1;e.hidden=!i;if(i)n++}});g.forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.f===f)}});db.textContent=n?n+' videó':'Nincs találat'}}
g.forEach(function(b){{b.addEventListener('click',function(){{f=b.dataset.f;m()}})}});q.addEventListener('input',m);m()}})();
</script>"""
    return lap("Videók – Valóban?", f"A Valóban? csatorna {len(v)} videója: keresés cím szerint, hosszú részek és Shorts-videók.", t, "videok.html")


def videolap(x, tobbi):
    bek, forras, kredit, gep = bont(x["leiras"])
    cim = tiszta_cim(x["cim"])
    url = f"https://www.youtube.com/shorts/{x['id']}" if x["tipus"] == "shorts" else f"https://www.youtube.com/watch?v={x['id']}"
    meta = " · ".join(y for y in (datum(x["ts"]), hossz(x.get("mp", 0)), "Shorts" if x["tipus"] == "shorts" else "") if y)
    osszeg = bek[0] if bek else cim
    if len(osszeg) > 155:
        m = re.match(r".{40,155}[.?!](?=\s)", osszeg, re.S)
        osszeg = m.group(0) if m else osszeg[:154].rsplit(" ", 1)[0] + "…"
    szov = "".join(f"<p>{linkes(p)}</p>" for p in bek)
    src = "".join(f'<li><a href="{E(u)}" rel="noopener nofollow">{E(n)}</a></li>' for n, u in forras)
    t = f"""<article class="vid{' vid-allo' if x['tipus'] == 'shorts' else ''}">
<a class="vid-kep" href="{url}" rel="noopener"><img src="../k/{x['id']}.jpg" alt="" width="{360 if x['tipus'] == 'shorts' else 640}" height="{640 if x['tipus'] == 'shorts' else 360}"><span class="play">Megnézem a YouTube-on</span></a>
<div class="vid-sz"><p class="meta">{E(meta)}</p><h1>{E(cim)}</h1>{szov}
{f'<h2>Források</h2><ol class="forrasok">{src}</ol>' if src else ''}
{f'<p class="meta kozles">{linkes(" ".join(gep))}</p>' if gep else ''}
{'<details class="kredit"><summary>Képek és kreditek</summary>' + ''.join(f'<p>{linkes(k)}</p>' for k in kredit) + '</details>' if kredit else ''}
</div></article>
<section><div class="sor"><h2>Ez is érdekelhet</h2><a href="../videok.html">Összes videó</a></div><ul class="racs{' szuk' if x['tipus'] == 'shorts' else ''}">{''.join(kartya(y, '../') for y in tobbi)}</ul></section>"""
    return lap(f"{cim} – Valóban?", osszeg, t, f"v/{x['id']}.html", "../", f"k/{x['id']}.jpg")


def terkep(v):
    u = [BOLD, BOLD + "videok.html", BOLD + "adatvedelem.html"] + [f"{BOLD}v/{x['id']}.html" for x in v]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{E(a)}</loc></url>\n" for a in u) + "</urlset>\n")


def main():
    videok = json.loads(ADAT.read_text())
    if "--frissit" in sys.argv:
        videok = frissit(videok)
        ADAT.write_text(json.dumps(videok, ensure_ascii=False, indent=1) + "\n")
    lathato = [v for v in videok if not v.get("rejtett")]
    for v in lathato:
        kep(v)
    (WEB / "v").mkdir(exist_ok=True)
    elo = {f"{v['id']}.html" for v in lathato}
    for f in (WEB / "v").glob("*.html"):
        if f.name not in elo:
            f.unlink()
    for n, v in enumerate(lathato):
        tobbi = [x for x in lathato[n + 1:] + lathato[:n] if x["tipus"] == v["tipus"] and x["id"] not in BEMUTATO][:6]
        (WEB / "v" / f"{v['id']}.html").write_text(videolap(v, tobbi))
    (WEB / "index.html").write_text(kezdolap(lathato))
    (WEB / "videok.html").write_text(archivum(lathato))
    (WEB / "sitemap.xml").write_text(terkep(lathato))
    print(f"{len(lathato)} videó, {len(videok) - len(lathato)} rejtett")


if __name__ == "__main__":
    main()
