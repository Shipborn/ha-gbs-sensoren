# Beslissingen

- **2026-11-27 – App in plaats van Git pull.** Eerst gedeployed met de Git pull add-on met `/config` als repo. Dat liep vast op een bug bij de eerste kloon (BusyBox `chmod --reference`, home-assistant/app-git-pull#10). Bovendien gooit die eerste kloon de `.yaml`-bestanden weg die niet in de repo staan. Nu is het een app zoals de Shipborn App: alleen eigen bestanden neerzetten en `configuration.yaml` minimaal aanpassen.
- **Dashboard aangemeld in het package** (`lovelace: dashboards:`), zodat `configuration.yaml` alleen de packages-regel nodig heeft.
- **Alleen standaard HA-kaarten**: geen HACS-afhankelijkheid op de boot.
- **Vaste codes T1–T4 / A1–A5** via hernoemde apparaten, zodat dezelfde YAML op elke installatie werkt, met ZHA en met Zigbee2MQTT.
- **2026-11-27 – Locaties beheren in een eigen paneel (1.1.0)**: de gebruiker wil zelf locaties toevoegen en aanpassen. Met alleen standaardkaarten kan een dashboard geen dynamische lijst met foto's tonen, dus schrijft de app het package en het dashboard opnieuw vanuit `/data/locaties.json` en herlaadt hij HA. Stdlib-server in plaats van Flask: maar een paar routes, en geen pip in de build.
- **Foto-URL via een dict in plaats van `| slugify`**: zo hangt de app niet af van precies hoe HA slugify'd, en kan er `?v=<mtime>` achter tegen de cache.
