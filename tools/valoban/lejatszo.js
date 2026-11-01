// Csak LEJATSZO = True mellett kerül az oldalra: a YouTube-kapcsolat az első kattintásig nem jön létre.
(function () {
  var a = document.querySelector("[data-yt]");
  if (!a) return;
  a.addEventListener("click", function (ev) {
    ev.preventDefault();
    var k = a.querySelector("img"), f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + a.dataset.yt + "?autoplay=1";
    f.title = "Videó a YouTube-ról";
    f.allow = "autoplay; encrypted-media; picture-in-picture";
    f.allowFullscreen = true;
    f.style.width = "100%";
    f.style.aspectRatio = k.width + "/" + k.height;
    f.style.border = "0";
    a.replaceWith(f);
  });
})();
