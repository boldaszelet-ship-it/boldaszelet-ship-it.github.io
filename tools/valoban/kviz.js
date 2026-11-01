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
