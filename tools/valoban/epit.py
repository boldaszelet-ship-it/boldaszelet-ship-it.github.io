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
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageFilter

GYOKER = Path(__file__).resolve().parents[2]
ADAT = Path(__file__).with_name("videok.json")
KERDESEK = Path(__file__).with_name("kerdesek.json")  # kézi: téma, ítélet, rövid válasz; bírálat után kerül ide
SZOVEGEK = Path(__file__).with_name("szovegek.json")  # gyártásból: ~/Valoban/tools/web_adat.py
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
HIRLEVEL = False  # D-valoban-20261031-07: csak a Brevo-fiók és a tájékoztató élesítése után kapcsolható be
FELIRATKOZAS = BOLD + "feliratkozas"  # a pages/_worker.js fogadja, ezért a látogató böngészőjébe nem kerül harmadik fél
E = lambda s: html.escape(str(s), quote=True)
TEMAK = {
    "allatok": ("Állatok és növények", "Mekkora a legnagyobb pók, mire emlékszik az aranyhal, és miért vált színt a kaméleon? Rangsorok és tévhitek az élővilágból, mért számokkal."),
    "test": ("Test és étel", "Tényleg csak az agyunk 10 százalékát használjuk? Mi lesz a lenyelt rágóval? Hétköznapi tévhitek a testünkről és az ételeinkről, forrásokkal."),
    "tortenelem": ("Történelem és közélet", "A Szent Koronától a pengőig és az őszödi beszédig: magyar történetek és állítások, ahogy a korabeli források és az iratok mutatják."),
    "bunugy": ("Bűnügyek", "Kiss Béla hordói és a Szépművészeti Múzeum 1983-as kirablása: ismert magyar bűnügyek, a legendáktól megtisztítva."),
    "magyar": ("Magyarország", "A Balaton, a budai barlangok, a Rubik-kocka és a magyar nyelv: amit mindenki tud Magyarországról, és ami ebből tényleg igaz."),
    "vilag": ("Világ és űr", "A legnagyobb és a legkisebb országok, a Naprendszer holdjai és a Kínai Nagy Fal: érdekességek és rangsorok a világról."),
}
TEMASZO = {"allatok": "állat kutya macska hal madár pók kígyó polip cápa bálna rovar fa növény virág", "test": "agy test egészség étel vitamin szív csont alvás kávé",
           "bunugy": "gyilkos rablás bűn nyomoz lopt", "tortenelem": "háború király történelem forradalom csata korona",
           "magyar": "magyar magyarország budapest balaton duna", "vilag": "ország világ hold bolygó űr nap föld"}
ITELET = {"Igaz": "igaz", "Részben igaz": "reszben", "Vitatott": "reszben", "Tévhit": "hamis"}
ERTEKELES = {"Tévhit": 1, "Részben igaz": 3, "Vitatott": 3, "Igaz": 5}  # ClaimReview: 1 = hamis, 5 = igaz


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


def csip(v):
    i = v.get("itelet")
    return f'<span class="itelet {ITELET[i]}">{E(i)}</span>' if i else ""


def kartya(v, elo=""):
    kis = v["tipus"] == "shorts"
    meta = " · ".join(x for x in (datum(v["ts"]), hossz(v.get("mp", 0)), "Shorts" if kis else "") if x)
    w, h = (360, 640) if kis else (640, 360)
    q = " ".join(x for x in (tiszta_cim(v["cim"]), v.get("rovid", ""), TEMAK.get(v.get("tema"), ("",))[0]) if x).lower()
    return (f'<li class="kartya{" allo" if kis else ""}" data-t="{v["tipus"]}" data-q="{E(q)}">'
            f'<a href="{elo}v/{v["slug"]}.html"><img src="{elo}k/{v["id"]}.jpg" width="{w}" height="{h}" alt="" loading="lazy">'
            f'{csip(v)}<span class="cim">{E(tiszta_cim(v["cim"]))}</span><span class="meta">{E(meta)}</span></a></li>')


def valaszsor(v, elo=""):
    """A főoldal és a tévhitlista sora: kérdés, ítélet, rövid válasz."""
    return (f'<li><a href="{elo}v/{v["slug"]}.html"><span class="kerdes">{E(tiszta_cim(v["cim"]))}</span>{csip(v)}'
            f'<span class="valasz">{E(v["rovid"])}</span></a></li>')


def urlap(elo=""):
    return f"""<form class="hirlevel-urlap" method="post" action="{FELIRATKOZAS}">
<label for="email">E-mail-címed</label>
<div class="hirlevel-sor"><input id="email" name="email" type="email" required autocomplete="email" inputmode="email" placeholder="nev@pelda.hu"><button class="gomb" type="submit">Kérem a hírlevelet</button></div>
<div class="csapda" aria-hidden="true"><label>Weboldal<input name="weboldal" tabindex="-1" autocomplete="off"></label></div>
<label class="hozzajarulas"><input type="checkbox" name="hozzajarulas" value="igen" required><span>Elmúltam 16 éves, és kérem a Valóban? heti hírlevelét. Bármikor leiratkozhatok. Az <a href="{elo}adatvedelem.html">adatkezelési tájékoztatót</a> elolvastam.</span></label>
</form>"""


KIADO = {"@type": "Organization", "name": "Valóban?", "url": BOLD, "logo": BOLD + "profil.png", "sameAs": [YT, TT, FB]}


def jsonld(adat):
    s = json.dumps(adat, ensure_ascii=False).replace("</", "<\\/")
    return f'\n<script type="application/ld+json">{s}</script>'


def morzsa(*tagok):
    """BreadcrumbList a morzsamenühöz: (név, útvonal a gyökértől) párok."""
    return jsonld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": n + 1, "name": c, "item": BOLD + u} for n, (c, u) in enumerate(tagok)]})


def lap(cim, leiras, tartalom, utvonal, elo="", kep_ut="profil.png", extra="", tipus="website"):
    return f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(cim)}</title>
<meta name="description" content="{E(leiras)}">
<link rel="canonical" href="{BOLD}{utvonal}">
<link rel="icon" href="{elo}profil.png">
<meta property="og:type" content="{tipus}">
<meta property="og:locale" content="hu_HU">
<meta property="og:site_name" content="Valóban?">
<meta property="og:title" content="{E(cim)}">
<meta property="og:description" content="{E(leiras)}">
<meta property="og:url" content="{BOLD}{utvonal}">
<meta property="og:image" content="{BOLD}{kep_ut}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="Valóban?" href="{BOLD}feed.xml">
<meta name="theme-color" content="#07192e">
<link rel="preload" href="{elo}f/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{elo}s.css">{extra}
</head>
<body>
<a class="ugras" href="#tartalom">Ugrás a tartalomra</a>
<header class="fej"><a class="marka" href="{elo or './'}"><img src="{elo}profil.png" width="40" height="40" alt=""><span>Valóban<i>?</i></span></a>
<nav aria-label="Fő"><a href="{elo}tevhitek.html">Tévhitek</a><a href="{elo}videok.html">Videók</a><a href="{elo}modszertan.html">Így dolgozunk</a>{f'<a href="{elo}hirlevel.html">Hírlevél</a>' if HIRLEVEL else ''}<a class="yt" href="{YT}" rel="noopener">YouTube</a></nav></header>
<main id="tartalom">
{tartalom}
</main>
<footer class="lab"><div>
<p class="temalink">{"".join(f'<a href="{elo}tema/{k}.html">{n[0]}</a>' for k, n in TEMAK.items())}</p>
<p class="koveto"><a href="{YT}" rel="noopener">YouTube</a><a href="{TT}" rel="noopener">TikTok</a><a href="{FB}" rel="noopener">Facebook</a></p>
<p>Üzemeltető: Boldurián Gábor, 1191 Budapest, Dobó Katica utca 13. · <a href="mailto:boldaszelet@gmail.com">boldaszelet@gmail.com</a> · Tárhely: GitHub, Inc. · Kiszolgálás: Cloudflare, Inc.</p>
<p><a href="{elo}modszertan.html">Így dolgozunk</a> · <a href="{elo}adatvedelem.html">Adatkezelési tájékoztató</a> · Az oldal nem használ sütit és látogatómérést.</p>
</div></footer>
</body>
</html>
"""


def kereso(elo="", cimke="Mire vagy kíváncsi?"):
    return (f'<form class="kereso" role="search" action="{elo}videok.html"><label for="fo-q">{cimke}</label>'
            '<div><input id="fo-q" name="q" type="search" autocomplete="off" placeholder="Például: polip, korona, Balaton">'
            '<button class="gomb" type="submit">Keresés</button></div></form>')


def kezdolap(v):
    hosszu = [x for x in v if x["tipus"] == "hosszu" and x["id"] not in BEMUTATO]
    shorts = [x for x in v if x["tipus"] == "shorts"]
    fo = next((x for x in v if x["id"] in BEMUTATO), hosszu[0])
    ellenorzott = [x for x in v if x.get("itelet")]
    forras = sum(len(bont(x["leiras"])[1]) for x in v)
    allitas = sum(x.get("allitas", 0) for x in v)
    temak = "".join(f'<li><a href="tema/{k}.html"><b>{E(n[0])}</b><span class="meta">{sum(x.get("tema") == k for x in v)} videó</span></a></li>' for k, n in TEMAK.items())
    t = f"""<section class="hos"><div class="hos-sz">
<h1>Valóban<i>?</i></h1>
<p class="szlog">Végére járunk.</p>
<p class="lede">Magyar ismeretterjesztő csatorna. Ismert történeteket és állításokat ellenőrzünk, rangsorokat és érdekességeket gyűjtünk, és mindig megmondjuk, honnan tudjuk.</p>
{kereso()}
<p class="gombok"><a class="gomb" href="{YT}?sub_confirmation=1" rel="noopener">Feliratkozom</a><a class="gomb masod" href="videok.html">Mind a {len(v)} videó</a></p>
</div>
<a class="kiemelt" href="v/{fo['slug']}.html"><img src="k/{fo['id']}.jpg" width="640" height="360" alt=""><span class="cimke">Kezdd itt</span><span class="cim">{E(tiszta_cim(fo['cim']))}</span></a>
</section>
<section class="szamok" aria-label="Számokban"><dl><div><dt>videó</dt><dd>{len(v)}</dd></div><div><dt>forrás a videók leírásában</dt><dd>{forras}</dd></div><div><dt>forrással igazolt állítás</dt><dd>{allitas}</dd></div></dl></section>
<section><div class="sor"><h2>Legutóbb ellenőriztük</h2><a href="tevhitek.html">Az összes</a></div>
<ul class="valaszok">{''.join(valaszsor(x) for x in ellenorzott[:6])}</ul></section>
<section><h2 class="alatt">Témák</h2><ul class="temak">{temak}</ul></section>
<section><div class="sor"><h2>Hosszú részek</h2><a href="videok.html#hosszu">Összes</a></div>
<ul class="racs">{''.join(kartya(x) for x in hosszu[:6])}</ul></section>
<section><div class="sor"><h2>Legújabb Shorts-videók</h2><a href="videok.html#shorts">Összes</a></div>
<ul class="racs szuk">{''.join(kartya(x) for x in shorts[:6])}</ul></section>
{hirlevel_blokk() if HIRLEVEL else ''}<section id="igy" class="igy"><div class="sor"><h2>Így dolgozunk</h2><a href="modszertan.html">Részletesen</a></div><ol>
<li><b>Egy téma, világos válasz</b>Minden rész egy kérdésre, állításra vagy rangsorra épül. Nem az a cél, hogy jól hangozzon, hanem hogy kiderüljön, mi igaz.</li>
<li><b>A források nyilvánosak</b>Minden videónál felsoroljuk, honnan tudjuk, amit mondunk, így bárki utánanézhet. Itt az oldalon is, videónként.</li>
<li><b>Nyíltan a gépi hangról</b>A narrációt gép olvassa fel, nem ember. Ezt minden videó leírásában közöljük.</li>
</ol><p class="hiba">Hibát találtál? Írd meg: <a href="mailto:boldaszelet@gmail.com">boldaszelet@gmail.com</a></p></section>
<section class="app"><h2>A feltöltő alkalmazásról</h2><p>A „Valoban Feltolto” a csatorna saját, belső eszköze: a YouTube Data API-n keresztül tölti fel és ütemezi a csatorna saját videóit. Más felhasználók nem használják, és más fiók adataihoz nem fér hozzá. Részletek: <a href="adatvedelem.html">adatkezelési tájékoztató</a>.</p></section>"""
    ld = jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": "Valóban?", "url": BOLD, "inLanguage": "hu",
                 "publisher": KIADO, "potentialAction": {"@type": "SearchAction", "target": BOLD + "videok.html?q={search_term_string}",
                                                         "query-input": "required name=search_term_string"}})
    return lap("Valóban? – magyar ismeretterjesztő csatorna",
               "Valóban? – magyar ismeretterjesztő csatorna: ismert történetek, állítások és rangsorok, forrásokkal. Végére járunk.",
               t, "", extra=ld)


def hirlevel_blokk():
    return f"""<section class="hirlevel"><h2>A hét legjobb kérdései, forrással</h2>
<p>Hetente egy levél: mit ellenőriztünk, mi derült ki, és honnan tudjuk.</p>{urlap()}</section>
"""


def hirlevel_lapok():
    nincs = '\n<meta name="robots" content="noindex">'
    hibak = {"email": "Ez nem tűnik érvényes e-mail-címnek.", "hozzajarulas": "A feliratkozáshoz be kell jelölnöd a négyzetet.",
             "sok": "Túl sok próbálkozás érkezett innen. Próbáld újra egy óra múlva.",
             "rendszer": "Most nem sikerült a feliratkozás. Próbáld újra később."}
    jelzo = f"""<p id="hiba" class="hirlevel-hiba" role="alert" hidden></p>
<script>(function(){{var h={json.dumps(hibak, ensure_ascii=False)}[new URLSearchParams(location.search).get('hiba')],e=document.getElementById('hiba');if(h){{e.textContent=h;e.hidden=false}}}})();</script>"""
    return {
        "hirlevel.html": lap("Hírlevél – Valóban?", "A Valóban? heti hírlevele: a hét legjobb kérdései, a válaszokkal és a forrásokkal.",
                             f"""<section class="hirlevel"><h1>A hét legjobb kérdései, forrással</h1>
<p>Hetente egy levél: mit ellenőriztünk, mi derült ki, és honnan tudjuk. Nincs reklám, és egy kattintással leiratkozhatsz.</p>{jelzo}{urlap()}</section>""",
                             "hirlevel.html"),
        "megerosites.html": lap("Már csak egy kattintás – Valóban?", "Erősítsd meg a feliratkozásodat a Valóban? hírlevelére.",
                                """<section class="hirlevel"><h1>Már csak egy kattintás</h1>
<p>Küldtünk egy levelet. Kattints a benne lévő gombra, és kész. Ha nem találod, nézd meg a levélszemét mappát is.</p></section>""",
                                "megerosites.html", extra=nincs),
        "koszonjuk.html": lap("Feliratkoztál – Valóban?", "Feliratkoztál a Valóban? hírlevelére.",
                              f"""<section class="hirlevel"><h1>Köszönjük, feliratkoztál</h1>
<p>Az első levél a következő heti kiadással érkezik. Addig is itt az összes rész forrásokkal.</p>
<p class="gombok"><a class="gomb" href="videok.html">Videók</a><a class="gomb masod" href="{YT}?sub_confirmation=1" rel="noopener">Feliratkozom YouTube-on</a></p></section>""",
                              "koszonjuk.html", extra=nincs),
    }


def archivum(v):
    t = f"""<section class="archiv"><h1>Videók</h1>
<form class="szuro" role="search" onsubmit="return false"><label for="q">Keresés a címekben és a válaszokban</label><input id="q" type="search" autocomplete="off" placeholder="Például: korona, Balaton, polip">
<div class="fulek" role="group" aria-label="Videótípus"><button type="button" data-f="" aria-pressed="true">Mind</button><button type="button" data-f="hosszu" aria-pressed="false">Hosszú részek</button><button type="button" data-f="shorts" aria-pressed="false">Shorts</button></div></form>
<p id="db" class="meta" aria-live="polite">{len(v)} videó</p>
<ul id="lista" class="racs vegyes">{''.join(kartya(x) for x in v)}</ul></section>
<script>
(function(){{var q=document.getElementById('q'),db=document.getElementById('db'),k=[].slice.call(document.querySelectorAll('#lista>li')),g=[].slice.call(document.querySelectorAll('.fulek button')),f=(location.hash||'').slice(1),u=new URLSearchParams(location.search).get('q');
if(f!=='hosszu'&&f!=='shorts')f='';if(u)q.value=u;
function m(){{var s=q.value.trim().toLowerCase(),n=0;k.forEach(function(e){{var i=(!f||e.dataset.t===f)&&e.dataset.q.indexOf(s)>-1;e.hidden=!i;if(i)n++}});g.forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.f===f)}});db.textContent=n?n+' videó':'Nincs találat'}}
g.forEach(function(b){{b.addEventListener('click',function(){{f=b.dataset.f;m()}})}});q.addEventListener('input',m);m()}})();
</script>"""
    return lap("Videók – Valóban?", f"A Valóban? csatorna {len(v)} videója: keresés cím szerint, hosszú részek és Shorts-videók.", t, "videok.html")


def parok(v):
    """Shorts → teljes rész: a leírásban lévő youtu.be-link adja a párt."""
    hosszuk = {x["id"]: x for x in v if x["tipus"] == "hosszu"}
    ki = {}
    for x in v:
        if x["tipus"] == "shorts":
            m = next((i for i in re.findall(r"youtu\.be/([\w-]{11})", x["leiras"]) if i in hosszuk), None)
            if m:
                ki[x["id"]] = hosszuk[m]
    return ki


def rovid(x):
    """A kézi rövid válasz, vagy a leírás első mondatai."""
    if x.get("rovid"):
        return x["rovid"]
    bek = bont(x["leiras"])[0]
    s = re.sub(r"\s*A teljes .*$", "", bek[0]) if bek else tiszta_cim(x["cim"])
    m = re.match(r".{40,300}?[.?!](?=\s|$)", s, re.S)
    return m.group(0) if m else s[:299].rsplit(" ", 1)[0] + "…"


def cimke_leiras(s):
    if len(s) <= 155:
        return s
    m = re.match(r".{40,155}[.?!](?=\s)", s, re.S)
    return m.group(0) if m else s[:154].rsplit(" ", 1)[0] + "…"


def vekony(x):
    """A hosszú rész rövid vágata: a teljes rész a kanonikus oldal, a kereső ne ezt kapja."""
    return x["tipus"] == "shorts" and x.get("par") and not x.get("itelet") and sum(len(p.split()) for p in bont(x["leiras"])[0]) < 70


def iso(ts):
    return dt.datetime.fromtimestamp(ts, BP).isoformat()


def videolap(x, tobbi, par=None):
    bek, forras, kredit, gep = bont(x["leiras"])
    cim = tiszta_cim(x["cim"])
    allo = x["tipus"] == "shorts"
    url = f"https://www.youtube.com/shorts/{x['id']}" if allo else f"https://www.youtube.com/watch?v={x['id']}"
    meta = " · ".join(y for y in (datum(x["ts"]), hossz(x.get("mp", 0)), "Shorts" if allo else "") if y)
    valasz = rovid(x)
    osszeg = cimke_leiras(valasz)
    tema = x.get("tema")
    szov = "".join(f"<p>{linkes(re.sub(r' *A teljes [^.:]*: *https?://youtu[^ ]+', '', p))}</p>" for p in bek)
    atirat = x.get("atirat")
    src = "".join(f'<li><a href="{E(u)}" rel="noopener nofollow">{E(n)}</a></li>' for n, u in forras)
    allitas = x.get("allitas")
    nap = x.get("ellenorizve")
    ell = " · ".join(y for y in (f"{allitas} forrással igazolt állítás" if allitas else "", f"{len(forras)} forrás" if forras else "",
                                 f"utoljára ellenőrizve: {datum(int(dt.datetime.fromisoformat(nap).replace(tzinfo=BP).timestamp()))}" if nap else "") if y)
    targy = f"Hiba: {cim}"
    utak = [("Valóban?", "")] + ([(TEMAK[tema][0], f"tema/{tema}.html")] if tema in TEMAK else []) + [(cim, f"v/{x['slug']}.html")]
    mm = "".join(f'<a href="../{u}">{E(c)}</a> › ' for c, u in utak[:-1]) + f'<span aria-current="page">{E(cim)}</span>'
    t = f"""<nav class="morzsa" aria-label="Morzsamenü">{mm}</nav>
<article class="vid{' vid-allo' if allo else ''}">
<a class="vid-kep" href="{url}" rel="noopener"><img src="../k/{x['id']}.jpg" alt="" width="{360 if allo else 640}" height="{640 if allo else 360}"><span class="play">Megnézem a YouTube-on</span></a>
<div class="vid-sz"><p class="meta">{E(meta)}</p><h1>{E(cim)}</h1>
<div class="rovid">{csip(x)}<p><b>Röviden:</b> {E(valasz)}</p></div>
{szov}
<p class="gombok">{f'<a class="gomb" href="{par["slug"]}.html">A teljes rész</a>' if par else ''}<a class="gomb{' masod' if par else ''}" href="{YT}?sub_confirmation=1" rel="noopener">Feliratkozom</a>{'<a class="gomb masod" href="../hirlevel.html">Hírlevél</a>' if HIRLEVEL else ''}</p>
{'<h2>A rész teljes szövege</h2>' + ''.join(f'<p>{E(p)}</p>' for p in atirat) if atirat else ''}
{f'<h2>Források</h2><ol class="forrasok">{src}</ol>' if src else ''}
{f'<p class="ellenorzes">{E(ell)} · <a href="../modszertan.html">Hogyan ellenőrzünk?</a></p>' if ell else ''}
<p class="hiba">Hibát találtál? <a href="mailto:boldaszelet@gmail.com?subject={urllib.parse.quote(targy)}">Írd meg nekünk</a>, és kijavítjuk.</p>
{f'<p class="meta kozles">{linkes(" ".join(gep))}</p>' if gep else ''}
{'<details class="kredit"><summary>Képek és kreditek</summary>' + ''.join(f'<p>{linkes(k)}</p>' for k in kredit) + '</details>' if kredit else ''}
</div></article>
<section><div class="sor"><h2>Ez is érdekelhet</h2><a href="../videok.html">Összes videó</a></div><ul class="racs{' szuk' if allo else ''}">{''.join(kartya(y, '../') for y in tobbi)}</ul></section>"""
    cikk = {"@context": "https://schema.org", "@type": "Article", "headline": cim[:110], "description": osszeg, "inLanguage": "hu",
            "image": f"{BOLD}o/{x['id']}.jpg", "datePublished": iso(x["ts"]), "author": KIADO, "publisher": KIADO,
            "mainEntityOfPage": f"{BOLD}v/{x['slug']}.html", "citation": [u for _, u in forras][:30]}
    if nap:
        cikk["dateModified"] = nap
    ld = jsonld(cikk) + morzsa(*utak)
    if x.get("itelet"):
        ld += jsonld({"@context": "https://schema.org", "@type": "ClaimReview", "url": f"{BOLD}v/{x['slug']}.html", "claimReviewed": cim,
                      "author": KIADO, "datePublished": dt.datetime.fromtimestamp(x["ts"], BP).date().isoformat(),
                      "reviewRating": {"@type": "Rating", "ratingValue": ERTEKELES[x["itelet"]], "bestRating": 5, "worstRating": 1, "alternateName": x["itelet"]}})
    return lap(f"{cim} – Valóban?", osszeg, t, f"v/{(par['slug'] if vekony(x) else x['slug'])}.html", "../", f"o/{x['id']}.jpg", ld, "article")


def atiranyit(x):
    """A régi, videóazonosítós cím: nincs a sitemapben, csak a korábbi linkek miatt marad."""
    c = f"{x['slug']}.html"
    return (f'<!doctype html><html lang="hu"><meta charset="utf-8"><title>{E(tiszta_cim(x["cim"]))}</title>'
            f'<link rel="canonical" href="{BOLD}v/{c}"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={c}">'
            f'<a href="{c}">Tovább</a></html>\n')


def temalap(k, v):
    nev, bev = TEMAK[k]
    sor = [x for x in v if x.get("tema") == k]
    ell = [x for x in sor if x.get("itelet")]
    t = f"""<section class="archiv"><nav class="morzsa" aria-label="Morzsamenü"><a href="../">Valóban?</a> › <span aria-current="page">{E(nev)}</span></nav>
<h1>{E(nev)}</h1><p class="lede">{E(bev)}</p></section>
{f'<section><h2 class="alatt">Ellenőrzött állítások</h2><ul class="valaszok">{"".join(valaszsor(x, "../") for x in ell)}</ul></section>' if ell else ''}
<section><h2 class="alatt">Minden videó</h2><ul class="racs vegyes">{''.join(kartya(x, '../') for x in sor)}</ul></section>"""
    ld = morzsa(("Valóban?", ""), (nev, f"tema/{k}.html"))
    return lap(f"{nev} – Valóban?", bev, t, f"tema/{k}.html", "../", extra=ld)


def tevhitek(v):
    sor = [x for x in v if x.get("itelet")]
    bev = "Igaz, részben igaz vagy tévhit? Elterjedt magyar és nemzetközi állítások, mindegyik egyértelmű válasszal és nyilvános forrásokkal."
    t = f"""<section class="archiv"><h1>Tévhitek és ellenőrzött állítások</h1><p class="lede">{E(bev)}</p></section>
<section><ul class="valaszok egysoros">{''.join(valaszsor(x) for x in sor)}</ul></section>"""
    return lap("Tévhitek és ellenőrzött állítások – Valóban?", bev, t, "tevhitek.html")


def modszertan():
    bev = "Hogyan készül a Valóban?: forrásellenőrzés, kiadás előtti ellenőrzések, gépi hang és hibajavítás."
    t = f"""<section class="szoveg"><h1>Így dolgozunk</h1><p class="lede">Azt ellenőrizzük, amit mindenki tud. A cél nem az, hogy jól hangozzon, hanem hogy kiderüljön, mi igaz, és bárki utánanézhessen.</p>
<h2>Forrás nélkül nincs mondat</h2>
<p>Minden videóhoz állítástábla készül: a szöveg minden tényállítása külön sort kap, a forrással és a forrás fokozatával. Az a tényállítás, amely mögött nincs megfelelő forrás, nem maradhat a szövegben. A felhasznált forrásokat minden videó oldalán felsoroljuk.</p>
<h2>Mit jelentenek az ítéletek?</h2>
<dl class="fogalmak"><dt><span class="itelet igaz">Igaz</span></dt><dd>A források alátámasztják az állítást.</dd>
<dt><span class="itelet reszben">Részben igaz</span></dt><dd>Van benne igazság, de pontosítani kell.</dd>
<dt><span class="itelet reszben">Vitatott</span></dt><dd>A megbízható források más-más eredményre jutnak, ezért mindkettőt bemutatjuk.</dd>
<dt><span class="itelet hamis">Tévhit</span></dt><dd>A források nem támasztják alá, vagy ellentmondanak neki.</dd></dl>
<h2>Kiadás előtt</h2>
<p>Egy videó csak akkor jelenik meg, ha átment a tényellenőrzésen, a jogi és a minőségi bírálaton, a nyelvi ellenőrzésen és a képek licencvizsgálatán. A vitatott állításoknál megnevezzük, ki állítja, és nem írunk fenntartás nélküli felsőfokot.</p>
<h2>Gép és ember</h2>
<p>A Valóban? mesterséges intelligenciával támogatott gyártósoron készül: a szöveg megírásában, a bírálatban és a vágásban is gépi eszközök dolgoznak, a narrációt pedig gép olvassa fel, nem ember. Ezt minden videó leírásában közöljük. A csatorna üzemeltetője: Boldurián Gábor.</p>
<h2>Hibát találtál?</h2>
<p>Írd meg a <a href="mailto:boldaszelet@gmail.com?subject=Hiba%20a%20Val%C3%B3ban%3F%20oldal%C3%A1n">boldaszelet@gmail.com</a> címre, lehetőleg a forrással együtt. Ha igazad van, kijavítjuk az oldalon és a videó leírásában.</p></section>"""
    return lap("Így dolgozunk – Valóban?", bev, t, "modszertan.html")


def csatorna(v):
    tetel = "".join(f"<item><title>{E(tiszta_cim(x['cim']))}</title><link>{BOLD}v/{x['slug']}.html</link><guid>{BOLD}v/{x['slug']}.html</guid>"
                    f"<pubDate>{dt.datetime.fromtimestamp(x['ts'], dt.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate><description>{E(rovid(x))}</description></item>\n"
                    for x in v[:30])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Valóban?</title>'
            f"<link>{BOLD}</link><description>Magyar ismeretterjesztő csatorna: ismert állítások, forrásokkal.</description><language>hu</language>\n{tetel}</channel></rss>\n")


def llms(v):
    sor = "\n".join(f"- [{tiszta_cim(x['cim'])}]({BOLD}v/{x['slug']}.html): {rovid(x)}" for x in v if x.get("itelet"))
    return (f"# Valóban?\n\n> Magyar ismeretterjesztő csatorna. Elterjedt állításokat ellenőrzünk, nyilvános forrásokkal.\n\n"
            f"- [Így dolgozunk]({BOLD}modszertan.html)\n- [Minden videó]({BOLD}videok.html)\n\n## Ellenőrzött állítások\n\n{sor}\n")


def megosztokep(x):
    """1200×630-as megosztási kép: a függőleges borító nem fér a Facebook-kártyára."""
    cel = WEB / "o" / f"{x['id']}.jpg"
    forras = WEB / "k" / f"{x['id']}.jpg"
    if cel.exists() or not forras.exists():
        return
    cel.parent.mkdir(exist_ok=True)
    k = Image.open(forras).convert("RGB")
    w, h = k.size
    hatter = k.crop((0, (h - int(w * 630 / 1200)) // 2, w, (h + int(w * 630 / 1200)) // 2)).resize((1200, 630), Image.LANCZOS)
    if x["tipus"] == "shorts":
        hatter = hatter.filter(ImageFilter.GaussianBlur(28)).point(lambda p: int(p * .55))
        kozep = k.resize((int(w * 630 / h), 630), Image.LANCZOS)
        hatter.paste(kozep, ((1200 - kozep.width) // 2, 0))
    hatter.save(cel, quality=78, optimize=True, progressive=True)


def slugosit(cim, foglalt):
    s = unicodedata.normalize("NFKD", cim.lower())
    s = re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if not unicodedata.combining(c))).strip("-")
    s = s[:70].rsplit("-", 1)[0] if len(s) > 70 else s
    a, n = s, 2
    while a in foglalt:
        a, n = f"{s}-{n}", n + 1
    return a


def gazdagit(videok):
    """Összefűzi a kézi és a gyártási adatot. A cím (slug) egyszer dől el, és a videok.json megtartja."""
    kezi = json.loads(KERDESEK.read_text())
    gy = json.loads(SZOVEGEK.read_text())
    foglalt = {v["slug"] for v in videok if v.get("slug")}
    for v in sorted(videok, key=lambda x: (x["tipus"] != "hosszu", x["ts"])):
        if not v.get("slug"):
            v["slug"] = slugosit(tiszta_cim(v["cim"]), foglalt)
            foglalt.add(v["slug"])
    ki = []
    for v in videok:
        x = {**v, **gy.get(v["id"], {}), **kezi.get(v["id"], {})}
        if not x.get("tema"):  # új videó: kulcsszóból, amíg kézzel be nem sorolják
            c = tiszta_cim(x["cim"]).lower()
            x["tema"] = next((k for k, sz in TEMASZO.items() if any(w in c for w in sz.split())), None)
        ki.append(x)
    return ki


def terkep(v):
    nap = lambda ts: dt.datetime.fromtimestamp(ts, BP).date().isoformat()
    u = [(BOLD, nap(v[0]["ts"])), (BOLD + "videok.html", nap(v[0]["ts"])), (BOLD + "tevhitek.html", nap(v[0]["ts"])), (BOLD + "modszertan.html", None),
         (BOLD + "adatvedelem.html", None)] + ([(BOLD + "hirlevel.html", None)] if HIRLEVEL else [])
    u += [(f"{BOLD}tema/{k}.html", nap(v[0]["ts"])) for k in TEMAK]
    u += [(f"{BOLD}v/{x['slug']}.html", x.get("ellenorizve") or nap(x["ts"])) for x in v if not vekony(x)]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{E(a)}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>\n" for a, d in u) + "</urlset>\n")


def main():
    videok = json.loads(ADAT.read_text())
    if "--frissit" in sys.argv:
        videok = frissit(videok)
    gazdag = gazdagit(videok)  # a slugot a videok elemeibe is beírja
    ADAT.write_text(json.dumps(videok, ensure_ascii=False, indent=1) + "\n")
    lathato = [v for v in gazdag if not v.get("rejtett")]
    for v in lathato:
        v["rovid"] = rovid(v)
    for v in lathato:
        kep(v)
        megosztokep(v)
    (WEB / "v").mkdir(exist_ok=True)
    (WEB / "tema").mkdir(exist_ok=True)
    par = parok(lathato)
    for v in lathato:
        v["par"] = par.get(v["id"], {}).get("id")
    elo = {f"{v['slug']}.html" for v in lathato} | {f"{v['id']}.html" for v in lathato}
    for f in (WEB / "v").glob("*.html"):
        if f.name not in elo:
            f.unlink()
    for n, v in enumerate(lathato):
        rokon = lathato[n + 1:] + lathato[:n]
        jo = [x for x in rokon if x["tipus"] == v["tipus"] and x["id"] not in BEMUTATO]
        tobbi = ([x for x in jo if x.get("tema") == v.get("tema")] + [x for x in jo if x.get("tema") != v.get("tema")])[:6]
        (WEB / "v" / f"{v['slug']}.html").write_text(videolap(v, tobbi, par.get(v["id"])))
        (WEB / "v" / f"{v['id']}.html").write_text(atiranyit(v))
    (WEB / "index.html").write_text(kezdolap(lathato))
    (WEB / "videok.html").write_text(archivum(lathato))
    (WEB / "tevhitek.html").write_text(tevhitek(lathato))
    (WEB / "modszertan.html").write_text(modszertan())
    for k in TEMAK:
        (WEB / "tema" / f"{k}.html").write_text(temalap(k, lathato))
    (WEB / "sitemap.xml").write_text(terkep(lathato))
    (WEB / "feed.xml").write_text(csatorna(lathato))
    (WEB / "llms.txt").write_text(llms(lathato))
    if HIRLEVEL:
        for nev, tartalom in hirlevel_lapok().items():
            (WEB / nev).write_text(tartalom)
    print(f"{len(lathato)} videó, {len(videok) - len(lathato)} rejtett")


if __name__ == "__main__":
    main()
