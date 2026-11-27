# GBS Sensoren – Home Assistant omgeving

Standaardopzet voor **9 Zigbee-sensoren** met een overzichtspagina en een
keuzemenu met foto's om per sensor vast te leggen waar die hangt.

| Code | Apparaat | Meet |
|---|---|---|
| **T1–T4** | SONOFF IP65 Zigbee temperatuursensor met display (sonde) | temperatuur, batterij |
| **A1–A5** | SONOFF AirGuard TH Pressure | temperatuur, luchtvochtigheid, luchtdruk, batterij |

Er zijn alleen standaard Home Assistant-kaarten gebruikt, dus HACS is niet nodig.

## Inhoud

Deze repo is een spiegel van `/config` in Home Assistant. De Git pull add-on zet hem daar neer.

```
.
├── configuration.yaml                → HA-hoofdconfig (standaard + packages + dashboard)
├── packages/gbs_sensoren.yaml        → helpers, script en template-sensoren
├── dashboards/gbs_sensoren.yaml      → het dashboard (3 tabbladen)
├── www/sensorlocaties/*.jpg          → foto's per locatie (nu nog placeholders)
├── tools/genereer.py                 → maakt alles opnieuw aan na wijzigen van locaties
└── .github/workflows/                → GitHub controleert bij elke push of de config geldig is
```

De `.gitignore` negeert alles behalve deze bestanden. `secrets.yaml`, de database, `.storage`,
backups en de automations die je in de UI maakt komen dus nooit in git.

## Werkwijze

```
wijzigen op je Mac ──git push──▶ GitHub ──(✓ config check)──▶ HA haalt op (Git pull add-on) ──▶ herstart als het geldig is
```

## Eenmalig instellen op Home Assistant

1. **Maak eerst een volledige backup** (*Instellingen → Systeem → Back-ups*). Bij de eerste
   pull kan de add-on bestaande bestanden in `/config` overschrijven.
2. Had je al een eigen `configuration.yaml`? Zet die regels dan eerst in de `configuration.yaml`
   van deze repo en push. Vanaf nu is de repo de bron.
3. **Deploy key** (alleen nodig voor een privé-repo): maak een SSH-sleutel zonder wachtwoord aan
   ```bash
   ssh-keygen -t ed25519 -N "" -C "ha-gbs" -f ~/.ssh/ha_gbs_deploy
   ```
   Zet `~/.ssh/ha_gbs_deploy.pub` op GitHub onder *Repo → Settings → Deploy keys*
   (alleen leesrechten). De privé-sleutel gaat in de add-on (stap 5).
4. Installeer de add-on **Git pull** (*Instellingen → Add-ons → Add-on store*).
5. Tabblad **Configuratie** van de add-on (*YAML-modus*):
   ```yaml
   repository: "git@github.com:<account>/<repo>.git"
   git_branch: main
   git_remote: origin
   git_prune: false
   git_command: pull
   auto_restart: true
   restart_ignore:
     - README.md
     - tools/
     - .github/
     - www/
     - dashboards/
   repeat:
     active: true
     interval: 300
   deployment_key:
     - "-----BEGIN OPENSSH PRIVATE KEY-----"
     - "<elke regel van ~/.ssh/ha_gbs_deploy als los item>"
     - "-----END OPENSSH PRIVATE KEY-----"
   deployment_key_protocol: ed25519
   ```
   Is de repo openbaar? Gebruik dan `repository: "https://github.com/<account>/<repo>.git"`
   en laat `deployment_key` weg.
6. Start de add-on en kijk in het **Logboek** of de pull lukt. Zet *Starten bij opstarten* aan.
   Daarna kijkt de add-on elke 5 minuten of er iets nieuws op GitHub staat.
7. **Koppel de sensoren** via ZHA of Zigbee2MQTT en **hernoem elk apparaat** precies zo:
   `GBS T1`, `GBS T2`, `GBS T3`, `GBS T4`, `GBS A1` … `GBS A5`.
   - **ZHA:** Apparaat → ✏️ → naam wijzigen → kies *"Entiteit-ID's ook hernoemen"*.
   - **Zigbee2MQTT:** friendly name `gbs_t1` enz., met *"Update Home Assistant entity ID"* aangevinkt.

   Dan krijg je deze entity-id's, waar het dashboard van uitgaat:
   `sensor.gbs_t1_temperature`, `sensor.gbs_t1_battery`,
   `sensor.gbs_a1_temperature`, `sensor.gbs_a1_humidity`, `sensor.gbs_a1_pressure`, `sensor.gbs_a1_battery`.
   Controleer ze onder *Instellingen → Entiteiten*. Wijken ze af? Hernoem dan de entiteit;
   de YAML hoeft niet aangepast te worden.
8. In de zijbalk staat nu **GBS Sensoren**.

## Een wijziging uitrollen

```bash
git add -A && git commit -m "Locaties aangepast" && git push
```

- Kijk op GitHub onder **Actions** of de *HA config check* groen is.
- Binnen 5 minuten haalt HA de wijziging op. De add-on herstart HA alleen als de configuratie
  geldig is. Een wijziging die alleen het dashboard of de foto's raakt, heeft geen herstart nodig:
  ververs dan de browser.
- **Wijzig beheerde bestanden niet op HA zelf.** Doe het in de repo, anders botsen ze bij de volgende pull.

## Gebruik

### Tabblad "Sensoren plaatsen"
1. **Stap 1:** kies de sensor (T1 … A5) die je ophangt of verplaatst.
2. **Stap 2:** tik op de **foto van de locatie** en bevestig. De sensor krijgt die locatie.
3. Vul in het detailvak eventueel een **toelichting** in, bijvoorbeeld "bovenste plank links, 1,2 m hoog".
   Daar kun je de locatie ook kiezen via de keuzelijst.

### Tabblad "Overzicht"
- Bovenaan een **tabel met alle 9 sensoren**: locatie, temperatuur, vocht, druk en batterij.
- Daaronder een kaart per sensor met de **foto van de locatie**, de live meetwaarden en de toelichting.
  Tik op een waarde voor de geschiedenis, of op de foto om naar "plaatsen" te gaan.

### Tabblad "Grafieken"
De temperatuur van alle sensoren, plus vocht en luchtdruk van de AirGuards, over de laatste 24 uur.

## Foto's en locaties aanpassen

**Foto vervangen:** overschrijf het bestand in `/config/www/sensorlocaties/` met dezelfde naam,
bijvoorbeeld `koelunit_inblaas.jpg`. Liggend formaat, rond 800×600, werkt het best.
Ververs daarna de browser (eventueel de cache legen).

**Locaties hernoemen, toevoegen of verwijderen:** pas de lijst `LOCATIES` bovenaan
`tools/genereer.py` aan en voer dan dit uit:

```bash
python3 tools/genereer.py .
```

Het script schrijft het package en het dashboard opnieuw en maakt alleen voor
**nieuwe** locaties een placeholder-foto aan. Bestaande foto's blijven staan. De bestandsnaam van een foto is de locatienaam in kleine
letters, met `_` in plaats van spaties.

> De gekozen locaties en toelichtingen blijven bewaard bij een herstart. Hernoem je een
> locatie die al in gebruik is, dan moet je die sensor opnieuw plaatsen.
