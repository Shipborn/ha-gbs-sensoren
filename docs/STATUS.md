# Status

**1.1.0 (2026-11-27)**: paneel **GBS Locaties** (ingress). Daarin voeg je locaties toe, hernoem je ze, verwijder je ze, zet je ze op volgorde en upload je foto's (camera of galerij). Na een wijziging herlaadt de app HA, zonder herstart. Lokaal getest tegen `tools/nep_ha.py`.

**1.0.0**: eerste app-versie (installer en dashboard).

Nog te doen:
- Op een echte HA testen: de build, de ingress, het herladen, en foto-upload vanuit de HA-app op telefoon.
- Entity-id's van de AirGuard TH Pressure controleren (luchtdruk-entiteit) zodra die gekoppeld is.
