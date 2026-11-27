# GBS Sensoren voor Home Assistant

Home Assistant-app (add-on) die een dashboard met locatiekeuze op foto neerzet voor
4 SONOFF IP65-temperatuursondes en 5 SONOFF AirGuard TH Pressure-sensoren. In het paneel
**GBS Locaties** voeg je locaties toe, hernoem je ze en geef je ze een foto.

## Installeren

1. In Home Assistant: **Instellingen → Apps → store → ⋮ → Repositories**.
2. Voeg toe: `https://github.com/Shipborn/ha-gbs-sensoren`
3. Installeer **GBS Sensoren** en start het.

Zie [gbs_sensoren/DOCS.md](gbs_sensoren/DOCS.md) voor de opties, het koppelen van de sensoren en het gebruik.

## Ontwikkelen

- Locaties beheer je in HA zelf (paneel **GBS Locaties**). De sensoren (T1–T4, A1–A5) en de opbouw van
  het package en het dashboard staan in `gbs_sensoren/app/genereer.py`.
- Lokaal testen: zie [CLAUDE.md](CLAUDE.md).
- **Verhoog `version` in `gbs_sensoren/config.yaml`** bij elke wijziging, anders biedt HA geen update aan.
- Bij elke push controleert GitHub Actions het app-manifest. Daarna doet hij de installatie na op
  een verse HA-config en laat Home Assistant zelf die config controleren.
