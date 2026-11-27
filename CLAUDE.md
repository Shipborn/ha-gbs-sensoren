# Projectnotities

Home Assistant-app **GBS Sensoren** (map en slug `gbs_sensoren`, repository `Shipborn/ha-gbs-sensoren`, openbaar). Zelfde opzet als de Shipborn App (`Shipborn/Shipborn_App`). UI en teksten in het Nederlands.

## Structuur
- `repository.yaml`: maakt de repo installeerbaar als HA-app-repository.
- `gbs_sensoren/config.yaml`: app-manifest. **Verhoog `version` bij elke wijziging**, anders biedt HA geen update aan. Ingress op 8099, paneel "GBS Locaties"; `homeassistant_api` (states/services) en `hassio_api` met `hassio_role: homeassistant` (core/check, core/restart); map `homeassistant_config` rw → `/homeassistant`.
- `gbs_sensoren/Dockerfile`: `FROM alpine:3.22` (geen `BUILD_FROM`, zie Shipborn App), python3 + py3-pillow + font-dejavu. Geen pip-pakketten: de server is stdlib (`ThreadingHTTPServer`).
- `gbs_sensoren/app/genereer.py`: `SONDES`/`AIRGUARDS`, `STANDAARD_LOCATIES`, `slug()`, `NAAM_RE` en de functies `package(locaties, versies)` / `dashboard(locaties, versies)`. Namen altijd via `q()` (= `json.dumps`, geldig in YAML én Jinja). `versies` = {slug: mtime van de foto}, als `?v=` achter de foto-URL tegen de browsercache.
- `gbs_sensoren/app/main.py`: opstarten (foto's aanvullen, package en dashboard schrijven, `zet_packages_aan()` in configuration.yaml met kopie `.voor-gbs`; nieuw package of nieuwe `www/` of aangepaste configuration.yaml → `core/check` + `core/restart`, alleen een gewijzigd package → herladen) en daarna de webserver. `--eenmalig` = alleen opstarten (CI).
  - Locaties in `/data/locaties.json` (lijst zonder "Niet geplaatst"; die staat altijd vooraan en is vast). Foto's als `/homeassistant/www/sensorlocaties/<slug>.jpg` (Pillow: EXIF-rotatie, max. 1600 px).
  - API: `GET api/locaties` ({locaties: [{naam, slug, v, vast, sensoren}], ha}), `POST api/locaties {naam}`, `PUT api/locaties/<slug> {naam}` (foto verhuist mee), `DELETE api/locaties/<slug>`, `POST api/volgorde {slugs}`, `POST api/locaties/<slug>/foto` (ruwe JPEG-body), `GET foto/<slug>.jpg`.
  - Elke wijziging (onder `SLOT`): de plaatsing vóór de wijziging lezen, opslaan, bestanden schrijven, `input_select`/`script`/`template` herladen en daarna elke sensor met `select_option` terugzetten (hernoemd → nieuwe naam, verdwenen → Niet geplaatst).
- `gbs_sensoren/app/static/index.html`: het paneel (vanilla JS, relatieve URL's vanwege ingress). Foto's worden in de browser verkleind naar JPEG via een canvas (dus ook HEIC). Bestandsinputs met `<label for>` en niet `display:none` (HA Android-app, zie Shipborn App).
- `gbs_sensoren/bestanden/www/sensorlocaties/`: standaardfoto's voor de standaardlocaties. Nieuwe locaties krijgen een placeholder van Pillow.
- `tools/nep_ha.py`: nep-HA en nep-Supervisor op 8123 voor lokaal testen.
- `.github/workflows/controle.yaml`: addon-linter, daarna `main.py --eenmalig` op een verse config (met lastige namen) en `frenck/action-home-assistant`.

## Gedrag
- Entity-id's van de echte sensoren: `sensor.gbs_<id>_{temperature,humidity,pressure,battery}` (apparaten hernoemd naar "GBS T1" enz.).
- Per sensor: `input_select.gbs_<id>_locatie`, `input_text.gbs_<id>_toelichting` en een template-sensor `sensor.gbs_<id>_plaatsing` (state = locatie, picture = een Jinja-dict naam → foto-URL).
- Plaatsen in het dashboard: `input_select.gbs_actieve_sensor` + picture-kaarten met `script.gbs_locatie_toewijzen` (veld `locatie`).
- Alleen standaardkaarten (geen HACS). Het YAML-dashboard ververst bij herladen van de browser.

## Testen lokaal
```
python3 tools/nep_ha.py &
cd gbs_sensoren/app && CONFIG_DIR=<scratchpad>/config DATA_DIR=<scratchpad>/data \
  HA_API=http://127.0.0.1:8123/api SUPERVISOR_API=http://127.0.0.1:8123 SUPERVISOR_TOKEN=test python3 main.py
```
Open http://127.0.0.1:8099. `<scratchpad>/config` moet een `configuration.yaml` hebben. Pillow is nodig.

## Maintaining project context
Houd CLAUDE.md, docs/STATUS.md en docs/DECISIONS.md kort en actueel. Commit of push alleen op verzoek.
