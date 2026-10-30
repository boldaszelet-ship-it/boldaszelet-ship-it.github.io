// valoban.pages.dev: a tartalom a GitHub Pages-ről jön, így a kétórás frissítés Cloudflare-kulcs nélkül is ide ér.
// Telepítés: wrangler pages deploy tools/valoban/pages --project-name valoban --branch main
const FORRAS = "https://boldaszelet-ship-it.github.io";

export default {
  async fetch(keres) {
    if (keres.method !== "GET" && keres.method !== "HEAD") {
      return new Response("Nem támogatott kérés.", { status: 405, headers: { allow: "GET, HEAD" } });
    }
    const u = new URL(keres.url);
    const ut = u.pathname === "/robots.txt" ? u.pathname : "/valoban" + u.pathname;
    const v = await fetch(FORRAS + ut, {
      method: keres.method,
      redirect: "manual",
      cf: { cacheEverything: true, cacheTtl: 600 },
    });
    const fej = new Headers(v.headers);
    const hova = fej.get("location");
    if (hova) fej.set("location", hova.replace(FORRAS + "/valoban", "").replace("http://boldaszelet-ship-it.github.io/valoban", "") || "/");
    return new Response(v.body, { status: v.status, headers: fej });
  },
};
