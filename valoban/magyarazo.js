// A két interaktív magyarázó. Az adat a lapba épül, hálózati kérés és tárolás nincs.
(function () {
  function szam(x, tized) {
    return x.toLocaleString("hu-HU", { maximumFractionDigits: tized === undefined ? 2 : tized }).replace(/ /g, " ");
  }

  // Egész számra: a -szor/-szer/-ször a szám kiejtett végéhez igazodik. Tizedes törtre nem használjuk.
  function szoros(s) {
    var jegy = s.replace(/\D/g, "");
    var utolso = jegy.slice(-1);
    if (utolso !== "0") return s + "-" + ["", "szer", "szer", "szor", "szer", "ször", "szor", "szer", "szor", "szer"][+utolso];
    var tizes = { 1: "szer", 2: "szor", 3: "szor", 4: "szer", 5: "szer", 6: "szor", 7: "szer", 8: "szor", 9: "szer" }[jegy.slice(-2, -1)];
    if (tizes) return s + "-" + tizes;
    if (/000000$/.test(jegy)) return s + "-szor";
    return s + (/000$/.test(jegy) ? "-szer" : "-szor");
  }

  // Az arány nem lehet pontosabb a kiinduló számoknál: 1000 fölött három értékes jegy, becslésnél kettő.
  function aranymondat(r, a, b, kb, d) {
    if (r >= 10) {
      var e = r >= 1000 ? +r.toPrecision(3) : kb ? +r.toPrecision(2) : Math.round(r);
      return a + " " + (kb || r >= 1000 ? "nagyjából " : "") + szoros(szam(e, 0)) + " " + d.ige + ", mint " + b + ".";
    }
    var o = Math.round(r * (kb ? 10 : 100)) / (kb ? 10 : 100);
    if (kb && o === 1) return a + " és " + b + " nagyjából egyforma.";
    return a + " a " + d.kozep + ": a kettő aránya " + (kb ? "nagyjából " : "") + szam(o) + " : 1.";
  }

  function rangsor(hely) {
    var adat = JSON.parse(document.getElementById("rangsor-adat").textContent);
    var fulek = hely.querySelector(".fulek"), a = hely.querySelector("#r-a"), b = hely.querySelector("#r-b");
    var mondat = hely.querySelector("#r-mondat"), rajz = hely.querySelector("#r-rajz"), merce = hely.querySelector("#r-merce");
    var aktiv;

    function nev(r, t) {
      if (!r.nevelo && !t.nevelo) return t.n;
      return (/^[aáeéiíoóöőuúüű]/i.test(t.n) ? "az " : "a ") + t.n;
    }

    function nagybetu(s) {
      return s.charAt(0).toUpperCase() + s.slice(1);
    }

    function ertek(t, r) {
      return (t.kb ? "kb. " : "") + szam(t.v) + " " + r.egyseg;
    }

    function rajzol() {
      var ta = aktiv.tetelek[a.selectedIndex], tb = aktiv.tetelek[b.selectedIndex];
      var nagy = ta.v >= tb.v ? ta : tb, kis = ta.v >= tb.v ? tb : ta, r = nagy.v / kis.v;
      if (ta === tb) mondat.textContent = "Ugyanazt választottad kétszer.";
      else if (ta.v === tb.v) mondat.textContent = nagybetu(nev(aktiv, nagy)) + " és " + nev(aktiv, kis) + " nagyjából egyforma.";
      else mondat.textContent = aranymondat(r, nagybetu(nev(aktiv, nagy)), nev(aktiv, kis), nagy.kb || kis.kb, aktiv);
      rajz.textContent = "";
      [ta, tb].forEach(function (t, i) {
        var s = document.createElement("div"), j = document.createElement("span"), f = document.createElement("p");
        s.className = "r-sor";
        j.className = "r-jel" + (i ? " masik" : "");
        var arany = t.v / nagy.v;
        if (aktiv.forma === "terulet") {
          var ol = Math.sqrt(arany) * 100;
          j.style.width = ol + "%";
          j.style.aspectRatio = "1";
        } else {
          j.style.width = arany * 100 + "%";
        }
        f.textContent = t.n + ": " + ertek(t, aktiv);
        s.appendChild(f);
        s.appendChild(j);
        rajz.appendChild(s);
      });
    }

    function valt(r) {
      aktiv = r;
      [].forEach.call(fulek.children, function (x) { x.setAttribute("aria-pressed", x.dataset.k === r.kulcs); });
      [a, b].forEach(function (s, i) {
        s.textContent = "";
        r.tetelek.forEach(function (t) {
          var o = document.createElement("option");
          o.textContent = t.n;
          o.selected = t.n === r.alap[i];
          s.appendChild(o);
        });
      });
      merce.textContent = r.merce + (r.megjegyzes ? " " + r.megjegyzes : "");
      rajzol();
    }

    adat.forEach(function (r) {
      var g = document.createElement("button");
      g.type = "button";
      g.textContent = r.cim;
      g.dataset.k = r.kulcs;
      g.addEventListener("click", function () { valt(r); });
      fulek.appendChild(g);
    });
    a.addEventListener("change", rajzol);
    b.addEventListener("change", rajzol);
    valt(adat[0]);
  }

  function pengo(hely) {
    var be = hely.querySelector("#p-ft"), ki = hely.querySelector("#p-ki");
    var P_FT = 4n * 10n ** 29n, AP_FT = 200000000n, BANKJEGY = 10n ** 20n;

    function teres(n) {
      return n.toString().replace(/\B(?=(\d{3})+$)/g, " ");
    }

    function szamol() {
      var nyers = be.value.replace(/\s/g, "");
      if (!/^\d{1,12}$/.test(nyers) || nyers === "0" || /^0+$/.test(nyers)) {
        ki.hidden = true;
        return;
      }
      var ft = BigInt(nyers), p = ft * P_FT;
      ki.hidden = false;
      hely.querySelector("#p-penz").textContent = teres(p);
      hely.querySelector("#p-jegy").textContent = p.toString().length;
      hely.querySelector("#p-ap").textContent = teres(ft * AP_FT);
      hely.querySelector("#p-db").textContent = teres(p / BANKJEGY);
    }

    be.addEventListener("input", szamol);
    [].forEach.call(hely.querySelectorAll("[data-ft]"), function (g) {
      g.addEventListener("click", function () {
        be.value = g.dataset.ft;
        szamol();
      });
    });
    szamol();
  }

  function olvadas(hely) {
    var cs = hely.querySelector("#o-ora"), ora = hely.querySelector("#o-felirat");
    function maradek(t, felezes) {
      return 100 * Math.pow(2, -t / felezes);
    }
    function ir() {
      var t = +cs.value;
      ora.textContent = t + " óra múlva";
      [["hu", 15], ["da", 34], ["zw", 24.7]].forEach(function (s) {
        var m = maradek(t, s[1]);
        hely.querySelector("#o-" + s[0]).textContent = szam(m, 1) + "%";
        hely.querySelector("#o-" + s[0] + "j").style.width = m + "%";
      });
    }
    cs.addEventListener("input", ir);
    ir();
  }

  var r = document.getElementById("rangsor");
  if (r) rangsor(r);
  var p = document.getElementById("pengo");
  if (p) pengo(p);
  var o = document.getElementById("olvadas");
  if (o) olvadas(o);
})();
