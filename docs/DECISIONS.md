# Beslissingen

- **2026-11-27 – App in plaats van Git pull.** Eerst gedeployed met de Git pull add-on met `/config` als repo. Dat liep vast op een bug bij de eerste kloon (BusyBox `chmod --reference`, home-assistant/app-git-pull#10). Bovendien gooit die eerste kloon de `.yaml`-bestanden weg die niet in de repo staan. Nu is het een app zoals de Shipborn App: alleen eigen bestanden neerzetten en `configuration.yaml` minimaal aanpassen.
- **Dashboard aangemeld in het package** (`lovelace: dashboards:`), zodat `configuration.yaml` alleen de packages-regel nodig heeft.
- **Alleen standaard HA-kaarten**: geen HACS-afhankelijkheid op de boot.
- **Vaste codes T1–T4 / A1–A5** via hernoemde apparaten, zodat dezelfde YAML op elke installatie werkt, met ZHA en met Zigbee2MQTT.
