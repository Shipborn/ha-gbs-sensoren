# GBS Sensoren voor Home Assistant

Home Assistant-app (add-on) die een dashboard met locatiekeuze op foto neerzet voor
4 SONOFF IP65-temperatuursondes en 5 SONOFF AirGuard TH Pressure-sensoren.

## Installeren

1. In Home Assistant: **Instellingen → Apps → store → ⋮ → Repositories**.
2. Voeg toe: `https://github.com/Shipborn/ha-gbs-sensoren`
3. Installeer **GBS Sensoren** en start het.

Zie [gbs_sensoren/DOCS.md](gbs_sensoren/DOCS.md) voor de opties, het koppelen van de sensoren en het gebruik.

## Ontwikkelen

- Locaties of sensoren wijzigen: pas `tools/genereer.py` aan en voer `python3 tools/genereer.py` uit.
  Dat schrijft `gbs_sensoren/bestanden/` opnieuw.
- **Verhoog `version` in `gbs_sensoren/config.yaml`** bij elke wijziging, anders biedt HA geen update aan.
- Bij elke push controleert GitHub Actions het app-manifest. Daarna doet hij de installatie na op
  een verse HA-config en laat Home Assistant zelf die config controleren.
