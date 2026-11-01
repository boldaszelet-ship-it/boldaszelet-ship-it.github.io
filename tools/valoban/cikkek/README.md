# Valóban? cikkformátum

Egy cikk egy fájl: `tools/valoban/cikkek/<slug>.md`. A fejléc `kulcs: érték` sorok, utána `---`, utána a törzs.

```
cim: A cikk címe (legfeljebb 70 karakter, kérdés vagy állítás, kattintásvadászat nélkül)
alcim: Lead, 1-2 mondat, legfeljebb 220 karakter; megmondja a tétet.
leiras: Keresőleírás és megosztási leírás, legfeljebb 155 karakter.
datum: 2026-11-02
rovat: <a TEMAK-kulcs: tortenelem, bunugy, magyar ...>
video: <YouTube-azonosító>
kep: c/<slug>-1.jpg
kepalairas: Mi látható a képen.
kepkredit: Szerző, fájlcím, licenc, változtatás | forrás-URL | licenc-URL (saját képnél csak: Valóban?, saját illusztráció)
biralat: A bírálatok fájlja vagy dátuma. Enélkül a cikk nem jelenik meg.
fb: A Facebook-poszt szövege, 2-4 mondat, link nélkül, horoggal, a válasz elárulása nélkül.
forras: Forrás neve | https://...
forras: Második forrás | https://...
---
Bevezető bekezdés.

## Alcím

Bekezdés.

> Kiemelt mondat: legfeljebb kettő, a törzsben szó szerint szereplő, magában is érthető mondat, nem közvetlenül a saját mondata után.

![Képaláírás | Kredit | forrás-URL | licenc-URL](c/<slug>-2.jpg)
```

Csak ezek a jelölők léteznek: `## `, `> `, `![...|...](...)`, üres sor. Félkövér és link nincs a törzsben.
