"""GBS Sensoren – app voor Home Assistant.

Bij het starten: package, dashboard en foto's in de HA-configmap zetten, packages aanzetten
in configuration.yaml en zo nodig HA (na een config check) herstarten.
Daarna: paneel "GBS Locaties" (ingress, poort 8099) om locaties en foto's te beheren. Na elke
wijziging worden het package en het dashboard opnieuw geschreven en herlaadt HA de helpers.

Omgevingsvariabelen (voor lokaal testen of CI):
  CONFIG_DIR (standaard /homeassistant), DATA_DIR (/data), OPTIONS_FILE (/data/options.json),
  HA_API (http://supervisor/core/api), SUPERVISOR_API (http://supervisor), SUPERVISOR_TOKEN,
  PORT (8099). Met argument --eenmalig: alleen bestanden neerzetten en stoppen.
"""
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import genereer as g

HIER = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.environ.get("CONFIG_DIR", "/homeassistant")
DATA = os.environ.get("DATA_DIR", "/data")
OPTIES_BESTAND = os.environ.get("OPTIONS_FILE", os.path.join(DATA, "options.json"))
HA_API = os.environ.get("HA_API", "http://supervisor/core/api")
SUP_API = os.environ.get("SUPERVISOR_API", "http://supervisor")
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
PORT = int(os.environ.get("PORT", "8099"))
STANDAARD_FOTOS = os.environ.get("STANDAARD_FOTOS", os.path.join(HIER, "..", "bestanden", "www", "sensorlocaties"))

FOTO_MAP = os.path.join(CONFIG, "www", "sensorlocaties")
PACKAGE = os.path.join(CONFIG, "packages", "gbs_sensoren.yaml")
DASHBOARD = os.path.join(CONFIG, "dashboards", "gbs_sensoren.yaml")
LOCATIES_BESTAND = os.path.join(DATA, "locaties.json")
FOTO_MAX_PX = 1600

SLOT = threading.Lock()


def log(*a):
    print("[GBS]", *a, flush=True)


def opties():
    try:
        return json.load(open(OPTIES_BESTAND))
    except Exception:
        return {}


# ------------------------------------------------------------------ locaties
def lees_locaties():
    try:
        lijst = json.load(open(LOCATIES_BESTAND))
        if isinstance(lijst, list) and all(isinstance(x, str) for x in lijst):
            if g.NIET_GEPLAATST in lijst:
                lijst.remove(g.NIET_GEPLAATST)
            return [g.NIET_GEPLAATST] + lijst
    except FileNotFoundError:
        pass
    except Exception as e:
        log("locaties.json onleesbaar, standaardlijst gebruikt:", e)
    return list(g.STANDAARD_LOCATIES)


def bewaar_locaties(lijst):
    os.makedirs(DATA, exist_ok=True)
    tmp = LOCATIES_BESTAND + ".tmp"
    json.dump(lijst, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, LOCATIES_BESTAND)


def foto_pad(s):
    return os.path.join(FOTO_MAP, f"{s}.jpg")


def versies(lijst):
    v = {}
    for l in lijst:
        try:
            v[g.slug(l)] = int(os.path.getmtime(foto_pad(g.slug(l))))
        except OSError:
            v[g.slug(l)] = 0
    return v


def controleer_naam(naam, lijst, behalve=None):
    naam = re.sub(r"\s+", " ", (naam or "").strip())
    if not g.NAAM_RE.match(naam) or not g.slug(naam):
        return None, "Gebruik 1–40 tekens: letters, cijfers, spaties en . , ( ) / & + ' -"
    for l in lijst:
        if l != behalve and g.slug(l) == g.slug(naam):
            return None, f"Er bestaat al een locatie '{l}'"
    return naam, None


# ------------------------------------------------------------------ foto's
def placeholder(naam, pad):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (800, 600), (90, 90, 90) if naam == g.NIET_GEPLAATST else (38, 70, 83))
    dr = ImageDraw.Draw(img)
    dr.rectangle([20, 20, 780, 580], outline=(233, 196, 106), width=4)
    font = None
    for f in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if os.path.exists(f):
            font = ImageFont.truetype(f, 54)
            break
    font = font or ImageFont.load_default()
    while dr.textlength(naam, font=font) > 720 and getattr(font, "size", 10) > 20:
        font = font.font_variant(size=font.size - 4)
    w = dr.textlength(naam, font=font)
    dr.text(((800 - w) / 2, 270), naam, font=font, fill="white")
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    img.save(pad, quality=85)


def bewaar_foto(data, pad):
    from PIL import Image, ImageOps
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((FOTO_MAX_PX, FOTO_MAX_PX))
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    tmp = pad + ".tmp"
    img.save(tmp, "JPEG", quality=85)
    os.replace(tmp, pad)


def zorg_voor_fotos(lijst, overschrijven=False):
    os.makedirs(FOTO_MAP, exist_ok=True)
    for l in lijst:
        pad = foto_pad(g.slug(l))
        standaard = os.path.join(STANDAARD_FOTOS, f"{g.slug(l)}.jpg")
        if os.path.exists(pad) and not overschrijven:
            continue
        if os.path.exists(standaard):
            shutil.copyfile(standaard, pad)
        elif not os.path.exists(pad):
            placeholder(l, pad)
        log("foto:", os.path.basename(pad))


# ------------------------------------------------------------------ configuration.yaml
def zet_packages_aan():
    """True = aangepast, False = al goed of bewust niet aangeraakt."""
    pad = os.path.join(CONFIG, "configuration.yaml")
    regel = "packages: !include_dir_named packages"
    try:
        tekst = open(pad, encoding="utf-8").read()
    except FileNotFoundError:
        log(f"LET OP: {pad} niet gevonden")
        return False
    bestaand = re.search(r"^[ \t]+packages[ \t]*:(.*)$", tekst, re.M)
    if bestaand:
        waarde = bestaand.group(1).strip()
        if not re.match(r"!include_dir_named\s+packages/?(\s*#.*)?$", waarde):
            log(f"LET OP: packages staat al in configuration.yaml als '{waarde}'. Niet aangepast; "
                f"zorg zelf dat packages/gbs_sensoren.yaml geladen wordt.")
        return False
    kop = re.search(r"^homeassistant[ \t]*:[ \t]*(#.*)?$", tekst, re.M)
    if kop:
        inspring = "  "
        for r in tekst[kop.end():].splitlines():
            if r.strip() and not r.lstrip().startswith("#"):
                m = re.match(r"^([ \t]+)", r)
                if m:
                    inspring = m.group(1)
                break
        nieuw = tekst[:kop.end()] + f"\n{inspring}{regel}" + tekst[kop.end():]
    else:
        nieuw = tekst.rstrip("\n") + f"\n\nhomeassistant:\n  {regel}\n"
    shutil.copy2(pad, pad + ".voor-gbs")
    open(pad, "w", encoding="utf-8").write(nieuw)
    log(f"'{regel}' toegevoegd aan configuration.yaml (kopie: configuration.yaml.voor-gbs)")
    return True


# ------------------------------------------------------------------ bestanden schrijven
def schrijf(pad, tekst):
    """True als de inhoud veranderd is."""
    try:
        if open(pad, encoding="utf-8").read() == tekst:
            return False
    except FileNotFoundError:
        pass
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    tmp = pad + ".tmp"
    open(tmp, "w", encoding="utf-8").write(tekst)
    os.replace(tmp, pad)
    log("bijgewerkt:", os.path.relpath(pad, CONFIG))
    return True


def schrijf_alles(lijst):
    v = versies(lijst)
    p = schrijf(PACKAGE, g.package(lijst, v))
    schrijf(DASHBOARD, g.dashboard(lijst, v))
    return p


# ------------------------------------------------------------------ Home Assistant
def verzoek(url, data=None, methode=None, timeout=60):
    if not TOKEN:
        raise RuntimeError("geen SUPERVISOR_TOKEN")
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=methode or ("POST" if data is not None else "GET"),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        tekst = r.read().decode() or "null"
    return json.loads(tekst)


def actie(domein, service, data=None):
    return verzoek(f"{HA_API}/services/{domein}/{service}", data or {})


def huidige_plaatsing():
    """{ 't1': 'Binnen voorzijde', ... } of {} als HA niet bereikbaar is."""
    try:
        states = verzoek(f"{HA_API}/states")
    except Exception as e:
        log("HA niet bereikbaar:", e)
        return {}
    uit = {}
    for s in states:
        m = re.match(r"^input_select\.gbs_([ta]\d)_locatie$", s.get("entity_id", ""))
        if m:
            uit[m.group(1)] = s.get("state")
    return uit


def herlaad_ha(voor, hernoemd=None):
    """Helpers/script/templates opnieuw laden en sensoren op de juiste locatie zetten.

    voor = plaatsing vóór de wijziging, hernoemd = {oud: nieuw}. Een sensor op een locatie
    die niet meer bestaat gaat naar 'Niet geplaatst'."""
    if not TOKEN:
        return "HA niet bereikbaar (geen token)"
    try:
        for d in ("input_select", "script", "template"):
            actie(d, "reload")
        lijst = lees_locaties()
        for i, oud in voor.items():
            nieuw = (hernoemd or {}).get(oud, oud)
            if nieuw not in lijst:
                nieuw = g.NIET_GEPLAATST
            actie("input_select", "select_option",
                  {"entity_id": f"input_select.gbs_{i}_locatie", "option": nieuw})
        return None
    except Exception as e:
        log("herladen mislukt:", e)
        return f"Herladen in HA mislukt: {e}"


def check_en_herstart():
    if not TOKEN:
        log("Herstart Home Assistant zelf om de wijzigingen te laden")
        return
    try:
        log("Configuratie controleren...")
        r = verzoek(f"{SUP_API}/core/check", {}, timeout=300)
        if r.get("result") != "ok":
            log("FOUT in de configuratie, NIET herstart:", r.get("message"))
            return
        log("Configuratie is geldig, Home Assistant wordt herstart")
        verzoek(f"{SUP_API}/core/restart", {}, timeout=30)
    except Exception as e:
        log("Herstarten mislukt:", e)


# ------------------------------------------------------------------ opstarten
def opstarten():
    o = opties()
    lijst = lees_locaties()
    if not os.path.exists(LOCATIES_BESTAND):
        bewaar_locaties(lijst[1:])
    herstart = not os.path.exists(PACKAGE) or not os.path.isdir(os.path.join(CONFIG, "www"))
    zorg_voor_fotos(lijst, overschrijven=bool(o.get("fotos_overschrijven")))
    package_anders = schrijf_alles(lijst)
    herstart = zet_packages_aan() or herstart
    if herstart:
        if o.get("auto_restart", True):
            check_en_herstart()
        else:
            log("Herstart Home Assistant om de wijzigingen te laden")
    elif package_anders:
        log("Package bijgewerkt, HA herladen")
        herlaad_ha(huidige_plaatsing())
    else:
        log("Niets veranderd")


# ------------------------------------------------------------------ webserver
def overzicht():
    lijst = lees_locaties()
    plaats = huidige_plaatsing()
    v = versies(lijst)
    return {
        "locaties": [{
            "naam": l,
            "slug": g.slug(l),
            "v": v[g.slug(l)],
            "vast": l == g.NIET_GEPLAATST,
            "sensoren": [i.upper() for i in g.ALLE if plaats.get(i) == l],
        } for l in lijst],
        "ha": bool(plaats),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "GBS"

    def log_message(self, *a):
        pass

    def stuur(self, code, data=None, soort="application/json", body=None):
        if body is None:
            body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", soort)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def fout(self, tekst, code=400):
        self.stuur(code, {"fout": tekst})

    def body(self, max_bytes=25_000_000):
        n = int(self.headers.get("Content-Length") or 0)
        if n > max_bytes:
            raise ValueError("Bestand te groot")
        return self.rfile.read(n)

    def json_body(self):
        try:
            return json.loads(self.body(100_000) or b"{}")
        except Exception:
            return {}

    def pad(self):
        return self.path.split("?", 1)[0].lstrip("/")

    # --- GET
    def do_GET(self):
        p = self.pad()
        if p in ("", "index.html"):
            return self.stuur(200, soort="text/html; charset=utf-8",
                              body=open(os.path.join(HIER, "static", "index.html"), "rb").read())
        if p == "api/locaties":
            return self.stuur(200, overzicht())
        m = re.match(r"^foto/([a-z0-9_]+)\.jpg$", p)
        if m and os.path.exists(foto_pad(m.group(1))):
            return self.stuur(200, soort="image/jpeg", body=open(foto_pad(m.group(1)), "rb").read())
        self.fout("Niet gevonden", 404)

    # --- wijzigingen
    def wijzig(self, functie):
        with SLOT:
            voor = huidige_plaatsing()
            lijst = lees_locaties()
            try:
                resultaat = functie(lijst)
            except ValueError as e:
                return self.fout(str(e))
            if resultaat is None:
                return
            nieuw, hernoemd = resultaat
            bewaar_locaties(nieuw[1:])
            zorg_voor_fotos(nieuw)
            schrijf_alles(nieuw)
            waarschuwing = herlaad_ha(voor, hernoemd)
        data = overzicht()
        data["waarschuwing"] = waarschuwing
        self.stuur(200, data)

    def vind(self, lijst, s):
        for l in lijst:
            if g.slug(l) == s:
                return l
        raise ValueError("Locatie niet gevonden")

    def do_POST(self):
        p = self.pad()
        if p == "api/locaties":
            naam = self.json_body().get("naam")

            def toevoegen(lijst):
                n, f = controleer_naam(naam, lijst)
                if f:
                    raise ValueError(f)
                return lijst + [n], None
            return self.wijzig(toevoegen)

        if p == "api/volgorde":
            slugs = self.json_body().get("slugs") or []

            def volgorde(lijst):
                per = {g.slug(l): l for l in lijst}
                if sorted(slugs) != sorted(per) or slugs[0] != g.slug(g.NIET_GEPLAATST):
                    raise ValueError("Ongeldige volgorde")
                return [per[s] for s in slugs], None
            return self.wijzig(volgorde)

        m = re.match(r"^api/locaties/([a-z0-9_]+)/foto$", p)
        if m:
            try:
                data = self.body()
            except ValueError as e:
                return self.fout(str(e))

            def foto(lijst):
                l = self.vind(lijst, m.group(1))
                try:
                    bewaar_foto(data, foto_pad(g.slug(l)))
                except Exception:
                    raise ValueError("Dit bestand is geen bruikbare foto")
                return lijst, None
            return self.wijzig(foto)
        self.fout("Niet gevonden", 404)

    def do_PUT(self):
        m = re.match(r"^api/locaties/([a-z0-9_]+)$", self.pad())
        if not m:
            return self.fout("Niet gevonden", 404)
        naam = self.json_body().get("naam")

        def hernoem(lijst):
            oud = self.vind(lijst, m.group(1))
            if oud == g.NIET_GEPLAATST:
                raise ValueError("'Niet geplaatst' kun je niet hernoemen")
            n, f = controleer_naam(naam, lijst, behalve=oud)
            if f:
                raise ValueError(f)
            if n == oud:
                return lijst, None
            if g.slug(n) != g.slug(oud) and os.path.exists(foto_pad(g.slug(oud))):
                os.replace(foto_pad(g.slug(oud)), foto_pad(g.slug(n)))
            return [n if l == oud else l for l in lijst], {oud: n}
        self.wijzig(hernoem)

    def do_DELETE(self):
        m = re.match(r"^api/locaties/([a-z0-9_]+)$", self.pad())
        if not m:
            return self.fout("Niet gevonden", 404)

        def verwijder(lijst):
            l = self.vind(lijst, m.group(1))
            if l == g.NIET_GEPLAATST:
                raise ValueError("'Niet geplaatst' kun je niet verwijderen")
            try:
                os.remove(foto_pad(g.slug(l)))
            except OSError:
                pass
            return [x for x in lijst if x != l], None
        self.wijzig(verwijder)


def main():
    opstarten()
    if "--eenmalig" in sys.argv:
        return
    log(f"Paneel 'GBS Locaties' luistert op poort {PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
