# GBS Sensoren

Deze app zet een kant-en-klaar dashboard **GBS Sensoren** in Home Assistant voor:

| Code | Apparaat | Meet |
|---|---|---|
| **T1–T4** | SONOFF IP65 Zigbee temperatuursensor met display (sonde) | temperatuur, batterij |
| **A1–A5** | SONOFF AirGuard TH Pressure | temperatuur, luchtvochtigheid, luchtdruk, batterij |

Daarnaast krijg je in de zijbalk het paneel **GBS Locaties**, waar je de locaties zelf beheert.

De app schrijft deze bestanden in je HA-configmap:

- `packages/gbs_sensoren.yaml`: keuzelijsten, toelichtingen, het toewijs-script, sensoren met foto, en de aanmelding van het dashboard;
- `dashboards/gbs_sensoren.yaml`: het dashboard;
- `www/sensorlocaties/*.jpg`: een foto per locatie.

In `configuration.yaml` voegt hij zo nodig `packages: !include_dir_named packages` toe onder
`homeassistant:`. Hij bewaart eerst een kopie als `configuration.yaml.voor-gbs`. Daarna
controleert hij de configuratie en herstart hij Home Assistant, maar alleen als de configuratie
geldig is.

## Installeren

1. In Home Assistant: **Instellingen → Apps → store → ⋮ → Repositories**, voeg `https://github.com/Shipborn/ha-gbs-sensoren` toe.
2. Installeer **GBS Sensoren** en klik op **Starten**. Zet **Starten bij opstarten** en **Weergeven in zijbalk** aan.
3. Kijk in het **Logboek** van de app. HA herstart één keer, daarna staan **GBS Sensoren** (dashboard) en **GBS Locaties** (beheer) in de zijbalk.

## Locaties beheren (paneel GBS Locaties)

- **Toevoegen:** typ een naam en klik op *Toevoegen*. Een nieuwe locatie krijgt eerst een grijze voorbeeldfoto.
- **Foto:** 📷 maakt direct een foto, *🖼 Foto* kiest er een uit je galerij of bestanden. De foto wordt verkleind opgeslagen.
- **Naam wijzigen:** *✎ Naam*. Sensoren die op die locatie staan, verhuizen mee.
- **Volgorde:** ↑ en ↓ bepalen de volgorde in de keuzelijst en op het dashboard.
- **Verwijderen:** sensoren die daar stonden gaan naar *Niet geplaatst*.
- *Niet geplaatst* is vast. Je kunt hem een andere foto geven, maar niet hernoemen of verwijderen.

Na elke wijziging herlaadt HA de keuzelijsten zelf, een herstart is niet nodig. Ververs het dashboard
**GBS Sensoren** in je browser om de nieuwe tegels en foto's te zien.

## Opties

| Optie | Uitleg |
|---|---|
| `auto_restart` | Home Assistant herstarten na een wijziging, alleen als de configuratie geldig is. Uit = zelf herstarten. |
| `fotos_overschrijven` | Aan = bij de start de standaardfoto's terugzetten voor de standaardlocaties. Je eigen foto's van die locaties gaan dan verloren. Laat dit normaal uit. |

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
  Locaties en foto's beheer je in het paneel **GBS Locaties**.
- **Overzicht:** een tabel met alle sensoren, en per sensor de foto van zijn locatie met de live waarden.
- **Grafieken:** de laatste 24 uur.

## Let op

`packages/gbs_sensoren.yaml` en `dashboards/gbs_sensoren.yaml` worden door de app geschreven. Wijzig ze
dus niet in HA zelf, maar gebruik het paneel. De locatielijst staat in de app zelf en gaat mee in een HA-backup. De gekozen locaties en toelichtingen blijven wel bewaard.
De app verwijderen haalt de bestanden **niet** weg. Wil je dat, verwijder ze dan zelf en herstart HA.
