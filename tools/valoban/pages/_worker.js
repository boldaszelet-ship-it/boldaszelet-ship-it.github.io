// valoban.pages.dev: a tartalom a GitHub Pages-ről jön, így a kétórás frissítés Cloudflare-kulcs nélkül is ide ér.
// Telepítés: wrangler pages deploy tools/valoban/pages --project-name valoban --branch main
const FORRAS = "https://boldaszelet-ship-it.github.io";
const BOLD = "https://valoban.pages.dev";
const ORAI_KERET = 5; // ennyi feliratkozás egy IP-ről óránként: a megerősítő levél keretét védi
const TEMA_ORZES = 180 * 86400; // ennyi ideig marad meg egy beküldött téma, utána magától törlődik
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;

const vissza = (ut) => new Response(null, { status: 303, headers: { location: BOLD + ut } });

async function tulKeres(keres) {
  const ora = Math.floor(Date.now() / 3600000);
  const nyers = new TextEncoder().encode(`${keres.headers.get("cf-connecting-ip")}|${ora}`);
  const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", nyers))].map((b) => b.toString(16).padStart(2, "0")).join("");
  const kulcs = new Request(`${BOLD}/__korlat/${hash}`);
  const db = Number((await (await caches.default.match(kulcs))?.text()) || 0) + 1;
  await caches.default.put(kulcs, new Response(String(db), { headers: { "cache-control": "max-age=3600" } }));
  return db > ORAI_KERET;
}

// Az e-mail-cím csak a Brevóba megy tovább: itt nem tárolódik és nem naplózódik.
async function feliratkozas(keres, env) {
  if (!env.BREVO_API_KEY) return new Response("A hírlevél még nem indult el.", { status: 503 });
  if (![BOLD, FORRAS].includes(keres.headers.get("origin"))) return new Response("Tiltott kérés.", { status: 403 });
  const urlap = await keres.formData();
  if (urlap.get("weboldal")) return vissza("/megerosites.html"); // csapdamező: ember nem látja
  const email = String(urlap.get("email") || "").trim().toLowerCase();
  if (!EMAIL.test(email)) return vissza("/hirlevel.html?hiba=email");
  if (urlap.get("hozzajarulas") !== "igen") return vissza("/hirlevel.html?hiba=hozzajarulas");
  if (await tulKeres(keres)) return vissza("/hirlevel.html?hiba=sok");
  const v = await fetch("https://api.brevo.com/v3/contacts/doubleOptinConfirmation", {
    method: "POST",
    headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({
      email,
      includeListIds: [Number(env.BREVO_LISTA_ID)],
      templateId: Number(env.BREVO_DOI_SABLON),
      redirectionUrl: `${BOLD}/koszonjuk.html`,
    }),
  });
  if (!v.ok) {
    console.error("Brevo-hiba", v.status);
    return vissza("/hirlevel.html?hiba=rendszer");
  }
  return vissza("/megerosites.html");
}

// Csak a kérdés szövege kerül a TEMAK KV-be: se IP, se név, se e-mail-cím.
async function temakuldes(keres, env) {
  if (!env.TEMAK) return new Response("A témaküldés még nem indult el.", { status: 503 });
  if (![BOLD, FORRAS].includes(keres.headers.get("origin"))) return new Response("Tiltott kérés.", { status: 403 });
  const urlap = await keres.formData();
  if (urlap.get("weboldal")) return vissza("/tema-koszonjuk.html"); // csapdamező: ember nem látja
  const kerdes = String(urlap.get("kerdes") || "").replace(/\s+/g, " ").trim();
  if (kerdes.length < 8 || kerdes.length > 200) return vissza("/temat-kuldj.html?hiba=rovid");
  if (await tulKeres(keres)) return vissza("/temat-kuldj.html?hiba=sok");
  try {
    await env.TEMAK.put(`${new Date().toISOString()}-${crypto.randomUUID()}`, kerdes, { expirationTtl: TEMA_ORZES });
  } catch (e) {
    console.error("KV-hiba");
    return vissza("/temat-kuldj.html?hiba=rendszer");
  }
  return vissza("/tema-koszonjuk.html");
}

export default {
  async fetch(keres, env) {
    if (keres.method === "POST" && new URL(keres.url).pathname === "/tema") return temakuldes(keres, env);
    if (keres.method === "POST" && new URL(keres.url).pathname === "/feliratkozas") return feliratkozas(keres, env);
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
