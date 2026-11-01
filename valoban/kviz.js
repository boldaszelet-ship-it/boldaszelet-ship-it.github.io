var KERDESEK=[{"a": "1946 júliusában Magyarországon 15 óránként duplázódtak az árak.", "i": "reszben", "c": "Vitatott", "r": "Két számítás két választ ad. Egy 2012-es táblázat szerint 1946 júliusában 15 óránként duplázódtak az árak, Danyi Pál 2022-es újraszámítása szerint viszont a júliusi átlagos infláció nagyságrendekkel kisebb volt.", "u": "magyarorszag-1946-mennyit-ert-a-fizetesed-mire-hazaertel-vele"}, {"a": "Kiss Béla 24 embert ölt meg, és alkoholban tartotta őket.", "i": "hamis", "c": "Tévhit", "r": "Nem 24 áldozatot találtak: a korabeli források szerint hét hordó volt, mindegyikben egy-egy nő. A 23–24 a későbbi, főleg külföldi irodalom száma.", "u": "kiss-bela-legendaja-hany-hordot-talaltak-valojaban-cinkotan"}, {"a": "A Kínai Nagy Fal látszik az űrből.", "i": "hamis", "c": "Tévhit", "r": "A NASA szerint ez mítosz: alacsony Föld körüli pályáról szabad szemmel általában nem látszik, a Holdról pedig biztosan nem.", "u": "latszik-a-kinai-nagy-fal-az-urbol"}, {"a": "Csak az agyunk 10 százalékát használjuk.", "i": "hamis", "c": "Tévhit", "r": "Nem. Képalkotó vizsgálatok szerint egy nap alatt az agyterületek többsége működik, csak nem egyszerre.", "u": "csak-az-agyunk-10-szazalekat-hasznaljuk"}, {"a": "A kaméleon a rejtőzködéshez vált színt.", "i": "reszben", "c": "Részben igaz", "r": "Főleg nem. Egy 2008-as vizsgálat 21 törpekaméleon-csoportnál nem talált bizonyítékot arra, hogy a képesség az álcázásra fejlődött; a szerzők szerint a látványos színváltást főleg a társas jelzés hajtotta. A fényerő változása azért a rejtőzésben is számít.", "u": "tenyleg-a-rejtozkodeshez-valt-szint-a-kameleon"}, {"a": "A lenyelt rágó 7 évig a gyomrunkban marad.", "i": "hamis", "c": "Tévhit", "r": "Nem. Egy gyermekgasztroenterológus szerint ez orvosilag megalapozatlan: a gumialap nagyrészt nem emészthető, de az emésztőrendszer továbbtolja. A rendszeresen lenyelt rágó viszont baj lehet: egy 1998-as beszámoló két gyereknél írja le, hogy a belőle összeállt massza székrekedést okozott.", "u": "7-evig-a-gyomrunkban-marad-a-lenyelt-rago"}, {"a": "Budapestnek köze van a Halloweenhez.", "i": "reszben", "c": "Részben igaz", "r": "Csak lazán. A mai Budapest helyén kelták éltek, de hogy megülték-e a Samhaint, biztosan nem tudjuk. A kapocs a hely, nem az ünnep.", "u": "budapestnek-koze-van-a-halloweenhez"}, {"a": "Egy magyar orvos látta el a Titanic túlélőit.", "i": "reszben", "c": "Részben igaz", "r": "Igen, de nem egyedül. Lengyel Árpád egyike volt a Carpathia három orvosának, és a harmadosztályú ebédlőt kapta.", "u": "egy-magyar-orvos-latta-el-a-titanic-tuleloit"}, {"a": "A paprika magyar növény.", "i": "hamis", "c": "Tévhit", "r": "Nem. A növény Mexikóból és Közép-Amerikából származik, Magyarországra a 16. században jutott el. A paprika szót a világ tőlünk vette át, mi viszont délszláv szomszédainktól kaptuk.", "u": "tenyleg-magyar-noveny-a-paprika"}, {"a": "A magyar a világ egyik legnehezebb nyelve.", "i": "reszben", "c": "Részben igaz", "r": "Nehéz, de angol anyanyelvűeknek nem a legnehezebb csoportba tartozik. Az amerikai külügy nyelviskolája a magyarra nagyjából 44 hetet becsül, a legnehezebb csoportra 88 hetet. A nehézség attól függ, honnan indulsz.", "u": "tenyleg-a-magyar-a-vilag-egyik-legnehezebb-nyelve"}, {"a": "Az Esterházy-madonnát feltekerve lopták el.", "i": "hamis", "c": "Tévhit", "r": "Nem. Az Esterházy-madonna 28,5 cm magas fatábla, azt nem lehet feltekerni. A képeket nem kivágták, hanem kiszerelték a díszkeretükből.", "u": "feltekerve-loptak-el-az-esterhazy-madonnat"}, {"a": "A kocsi Kocs faluról kapta a nevét.", "i": "igaz", "c": "Igaz", "r": "Igen. A Komárom megyei Kocs kézművesei fejlesztették ki a könnyű, lóhúzta kocsi szekeret, ebből rövidült a szó. Az viszont csak legenda, hogy Mátyás király találta fel a kocsit.", "u": "tenyleg-kocs-falurol-kapta-nevet-a-kocsi"}, {"a": "Az aranyhal memóriája csak 3 másodperces.", "i": "hamis", "c": "Tévhit", "r": "Nem. Culum Brown halkutató szerint az aranyhal emlékei hetekig, hónapokig, sőt évekig is megmaradhatnak.", "u": "tenyleg-csak-3-masodperces-az-aranyhal-memoriaja"}, {"a": "A spenót tele van vassal.", "i": "hamis", "c": "Tévhit", "r": "Nem, a spenót nem kiemelkedő vasforrás. A nyers spenót 100 grammjában nagyjából 2,7 milligramm vas van, és a benne lévő oxálsav gátolja a felszívódását. A tizedesvessző-legenda maga is mítosz.", "u": "tenyleg-tele-van-vassal-a-spenot"}];
// Igaz vagy hamis? A kérdéseket az epit.py teszi a fájl elejére. Nincs süti, nincs helyi tárolás, nincs hálózati kérés.
(function () {
  var GOMBOK = [["igaz", "Igaz"], ["reszben", "Részben igaz vagy vitatott"], ["hamis", "Tévhit"]];
  var CIM = "https://valoban.pages.dev/kviz.html";

  function el(cimke, osztaly, szoveg) {
    var e = document.createElement(cimke);
    if (osztaly) e.className = osztaly;
    if (szoveg !== undefined) e.textContent = szoveg;
    return e;
  }

  function napszam() {
    var d = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Budapest" }).format(new Date()).split("-");
    return Math.floor(Date.UTC(+d[0], +d[1] - 1, +d[2]) / 864e5);
  }

  function kever(lista) {
    var a = lista.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  // Egy kérdés: gombok, majd a válasz. A kész() kapja meg, eltalálta-e.
  function kerdes(hely, k, elo, kesz) {
    var doboz = el("div", "kviz-kerdes");
    var all = el("p", "kviz-allitas", "„" + k.a + "”");
    var sor = el("div", "kviz-gombok");
    sor.setAttribute("role", "group");
    sor.setAttribute("aria-label", "Mit gondolsz?");
    doboz.appendChild(all);
    doboz.appendChild(sor);
    GOMBOK.forEach(function (g) {
      var b = el("button", "gomb masod", g[1]);
      b.type = "button";
      b.addEventListener("click", function () {
        var jo = g[0] === k.i;
        [].forEach.call(sor.children, function (x) { x.disabled = true; });
        b.classList.add("valasztott");
        var v = el("div", "kviz-valasz");
        v.tabIndex = -1;
        var fej = el("p", "kviz-fej", jo ? "Eltaláltad. " : "Most nem jött össze. ");
        fej.appendChild(el("span", "itelet " + k.i, k.c));
        v.appendChild(fej);
        v.appendChild(el("p", "", k.r));
        var l = el("a", "", "Forrásokkal, részletesen");
        l.href = elo + "v/" + k.u + ".html";
        v.appendChild(el("p", "")).appendChild(l);
        doboz.appendChild(v);
        v.focus({ preventScroll: true });
        kesz(jo, v);
      });
      sor.appendChild(b);
    });
    hely.appendChild(doboz);
  }

  function ertekeles(p, n) {
    var a = p / n;
    if (a >= 0.8) return "Téged nehéz becsapni.";
    if (a >= 0.5) return "Több mint a felét tudtad. A többi is csak egy kattintás.";
    return "Ezek makacs állítások. A válaszok mögött ott a forrás.";
  }

  function megoszt(p, n, racs) {
    var cim = CIM + "#e=" + p + "-" + n;
    var szoveg = "Igaz vagy hamis? " + p + "/" + n + " pont a Valóban? kvízén.\n" + racs + "\n";
    return function (ev) {
      var b = ev.currentTarget;
      if (navigator.share) {
        navigator.share({ text: szoveg, url: cim }).catch(function () {});
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(szoveg + cim).then(function () { b.textContent = "Kimásolva"; }, function () { b.textContent = cim; });
      } else {
        b.textContent = cim;
      }
    };
  }

  function kor(hely) {
    var sor = kever(KERDESEK), n = 0, pont = 0, racs = "";
    var allas = el("p", "meta");
    allas.setAttribute("aria-live", "polite");
    var ter = el("div");
    hely.textContent = "";
    hely.appendChild(allas);
    hely.appendChild(ter);

    function kovetkezo() {
      ter.textContent = "";
      if (n === sor.length) return vege();
      allas.textContent = (n + 1) + ". kérdés a " + sor.length + "-ból · " + pont + " pont";
      kerdes(ter, sor[n], "", function (jo, v) {
        pont += jo ? 1 : 0;
        racs += jo ? "🟩" : "🟥";
        n++;
        var t = el("button", "gomb", n === sor.length ? "Eredmény" : "Következő kérdés");
        t.type = "button";
        t.addEventListener("click", kovetkezo);
        v.appendChild(t);
      });
      ter.scrollIntoView({ block: "nearest" });
    }

    function vege() {
      allas.textContent = "";
      var e = el("div", "kviz-eredmeny");
      e.tabIndex = -1;
      e.appendChild(el("p", "kviz-pont", pont + "/" + sor.length));
      e.appendChild(el("p", "", ertekeles(pont, sor.length)));
      e.appendChild(el("p", "kviz-racs", racs));
      var g = el("p", "gombok");
      var m = el("button", "gomb", "Megosztom az eredményt");
      m.type = "button";
      m.addEventListener("click", megoszt(pont, sor.length, racs));
      var u = el("button", "gomb masod", "Újra játszom");
      u.type = "button";
      u.addEventListener("click", function () { kor(hely); });
      g.appendChild(m);
      g.appendChild(u);
      e.appendChild(g);
      ter.appendChild(e);
      e.focus({ preventScroll: true });
    }

    kovetkezo();
  }

  function kihivas(hely) {
    var m = /^#e=(\d{1,3})-(\d{1,3})$/.exec(location.hash);
    if (m && +m[1] <= +m[2] && +m[2] > 0) {
      hely.parentNode.insertBefore(el("p", "kviz-kihivas", "Aki ezt a linket küldte, " + m[1] + "/" + m[2] + " pontot ért el. Te hányat tudsz?"), hely);
    }
  }

  var nap = document.querySelector("[data-kviz=nap]");
  if (nap) {
    nap.textContent = "";
    kerdes(nap, KERDESEK[napszam() % KERDESEK.length], nap.dataset.elo || "", function (jo, v) {
      var l = el("a", "gomb", "Játszom az összessel");
      l.href = (nap.dataset.elo || "") + "kviz.html";
      v.appendChild(l);
    });
  }
  var fo = document.querySelector("[data-kviz=kor]");
  if (fo) {
    kihivas(fo);
    kor(fo);
  }
})();
