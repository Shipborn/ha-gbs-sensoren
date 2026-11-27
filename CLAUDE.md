# Projectnotities

Home Assistant-app **GBS Sensoren** (map en slug `gbs_sensoren`, repository `Shipborn/ha-gbs-sensoren`, openbaar). Zelfde opzet als de Shipborn App (`Shipborn/Shipborn_App`). UI en teksten in het Nederlands.

## Structuur
- `repository.yaml`: maakt de repo installeerbaar als HA-app-repository.
- `gbs_sensoren/config.yaml`: app-manifest. **Verhoog `version` bij elke wijziging**, anders biedt HA geen update aan.
- `gbs_sensoren/Dockerfile`: `FROM alpine:3.22` (geen `BUILD_FROM`, zie Shipborn App). Bevat bash, curl, jq en python3.
- `gbs_sensoren/run.sh`: zet bij de start `bestanden/` neer in `/homeassistant` (map `homeassistant_config`, rw). Package of nieuwe `www/` = herstart nodig, dashboard niet. Foto's alleen als ze ontbreken (optie `fotos_overschrijven`). Daarna `zet_packages_aan.py`, en bij een wijziging Supervisor `core/check` → `core/restart` (`hassio_role: homeassistant`). Blijft draaien (`tail -f /dev/null`) zodat een update opnieuw neerzet. Paden zijn via env te overschrijven om lokaal of in CI te testen (`GBS_TEST=1` stopt aan het eind).
- `gbs_sensoren/zet_packages_aan.py`: voegt `packages: !include_dir_named packages` toe onder `homeassistant:` (of maakt dat blok), met een kopie `configuration.yaml.voor-gbs`. Exit 0 = al goed, 10 = aangepast, 3 = andere packages-regel (niet aangeraakt), 2 = geen bestand.
- `gbs_sensoren/bestanden/`: **gegenereerd** door `tools/genereer.py` (niet met de hand wijzigen). Het package bevat ook `lovelace: dashboards:` (YAML-dashboard `gbs-sensoren`).
- `tools/genereer.py`: bron van de waarheid voor `LOCATIES`, `SONDES` (t1–t4) en `AIRGUARDS` (a1–a5). Maakt placeholder-foto's alleen voor nieuwe locaties (Pillow).
- `.github/workflows/controle.yaml`: lint het manifest, doet `run.sh` na op een verse config en controleert die met `frenck/action-home-assistant`.

## Gedrag
- Entity-id's van de echte sensoren: `sensor.gbs_<id>_{temperature,humidity,pressure,battery}` (apparaten hernoemd naar "GBS T1" enz.).
- Per sensor: `input_select.gbs_<id>_locatie`, `input_text.gbs_<id>_toelichting` en een template-sensor `sensor.gbs_<id>_plaatsing` (state = locatie, picture = `/local/sensorlocaties/<locatie|slugify>.jpg`).
- Foto kiezen: `input_select.gbs_actieve_sensor` + picture-kaarten met `script.gbs_locatie_toewijzen` (veld `locatie`).
- Alleen standaardkaarten (geen HACS).

## Testen lokaal
```
cd gbs_sensoren && GBS_TEST=1 OPTIES=<opties.json> BRON=bestanden APP_YAML=config.yaml HULP=zet_packages_aan.py CONFIG_DIR=<scratchpad>/config bash run.sh
```

## Maintaining project context
Houd CLAUDE.md, docs/STATUS.md en docs/DECISIONS.md kort en actueel. Commit of push alleen op verzoek.
