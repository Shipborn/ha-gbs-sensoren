# GBS Sensoren

Deze app zet een kant-en-klaar dashboard **GBS Sensoren** in Home Assistant voor:

| Code | Apparaat | Meet |
|---|---|---|
| **T1–T4** | SONOFF IP65 Zigbee temperatuursensor met display (sonde) | temperatuur, batterij |
| **A1–A5** | SONOFF AirGuard TH Pressure | temperatuur, luchtvochtigheid, luchtdruk, batterij |

De app draait geen eigen webpagina. Bij elke start zet hij deze bestanden in je HA-configmap:

- `packages/gbs_sensoren.yaml`: keuzelijsten, toelichtingen, het toewijs-script, sensoren met foto, en de aanmelding van het dashboard;
- `dashboards/gbs_sensoren.yaml`: het dashboard;
- `www/sensorlocaties/*.jpg`: een foto per locatie (alleen als die er nog niet staat).

In `configuration.yaml` voegt hij zo nodig `packages: !include_dir_named packages` toe onder
`homeassistant:`. Hij bewaart eerst een kopie als `configuration.yaml.voor-gbs`. Daarna
controleert hij de configuratie en herstart hij Home Assistant, maar alleen als de configuratie
geldig is.

## Installeren

1. In Home Assistant: **Instellingen → Apps → store → ⋮ → Repositories**, voeg `https://github.com/Shipborn/ha-gbs-sensoren` toe.
2. Installeer **GBS Sensoren** en klik op **Starten**. Zet **Starten bij opstarten** aan.
3. Kijk in het **Logboek** van de app. HA herstart één keer, daarna staat **GBS Sensoren** in de zijbalk.

## Opties

| Optie | Uitleg |
|---|---|
| `auto_restart` | Home Assistant herstarten na een wijziging, alleen als de configuratie geldig is. Uit = zelf herstarten. |
| `fotos_overschrijven` | Aan = de standaardfoto's terugzetten en daarmee je eigen foto's overschrijven. Laat dit normaal uit. |

## Sensoren koppelen

Koppel de sensoren via ZHA of Zigbee2MQTT en **hernoem elk apparaat** precies zo:
`GBS T1` … `GBS T4` en `GBS A1` … `GBS A5`.

- **ZHA:** Apparaat → ✏️ → naam wijzigen → kies *"Entiteit-ID's ook hernoemen"*.
- **Zigbee2MQTT:** friendly name `gbs_t1` enz., met *"Update Home Assistant entity ID"* aangevinkt.

Het dashboard gaat uit van deze entity-id's:
`sensor.gbs_t1_temperature`, `sensor.gbs_t1_battery`, `sensor.gbs_a1_temperature`,
`sensor.gbs_a1_humidity`, `sensor.gbs_a1_pressure` en `sensor.gbs_a1_battery`.
Wijken ze af? Hernoem dan de entiteit in *Instellingen → Entiteiten*.

## Gebruik

- **Sensoren plaatsen:** kies de sensor, tik op de foto van de locatie en vul eventueel een toelichting in.
- **Overzicht:** een tabel met alle sensoren, en per sensor de foto van zijn locatie met de live waarden.
- **Grafieken:** de laatste 24 uur.

## Eigen foto's

Zet je foto in `/config/www/sensorlocaties/` met dezelfde naam, bijvoorbeeld `koelunit_inblaas.jpg`.
De app laat bestaande foto's staan, tenzij `fotos_overschrijven` aan staat.

## Let op

`packages/gbs_sensoren.yaml` en `dashboards/gbs_sensoren.yaml` worden bij elke start en update
overschreven. Wijzig ze dus niet in HA zelf. De gekozen locaties en toelichtingen blijven wel bewaard.
De app verwijderen haalt de bestanden **niet** weg. Wil je dat, verwijder ze dan zelf en herstart HA.
