"""Maakt het HA-package en het dashboard voor de GBS-sensoren uit de locatielijst.

Namen gaan altijd via json.dumps de YAML in: een JSON-string is ook een geldige
YAML-string en een geldige Jinja-string.
"""
import json
import re
import unicodedata

SONDES = ["t1", "t2", "t3", "t4"]          # SONOFF IP65 temperatuur met display (sonde)
AIRGUARDS = ["a1", "a2", "a3", "a4", "a5"]  # SONOFF AirGuard TH Pressure
ALLE = SONDES + AIRGUARDS

NIET_GEPLAATST = "Niet geplaatst"
STANDAARD_LOCATIES = [
    NIET_GEPLAATST,
    "Binnen voorzijde",
    "Binnen midden",
    "Binnen achterzijde",
    "Plafond",
    "Vloer",
    "Koelunit inblaas",
    "Koelunit retour",
    "Deur",
    "Buiten",
    "Technische ruimte",
]

NAAM_RE = re.compile(r"^[\w .,()/&+'\-]{1,40}$")


def slug(naam):
    s = unicodedata.normalize("NFKD", naam).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def soort(i):
    return "Sonde (IP65, display)" if i in SONDES else "AirGuard TH Pressure"


def q(s):
    return json.dumps(s, ensure_ascii=False)


def foto_url(naam, versies):
    s = slug(naam)
    return f"/local/sensorlocaties/{s}.jpg?v={versies.get(s, 0)}"


# ------------------------------------------------------------------ package
def package(locaties, versies):
    p = ["""# =====================================================================
#  GBS sensoren – package (gemaakt door de app "GBS Sensoren")
#  Niet hier wijzigen: de app schrijft dit bestand opnieuw.
#  Locaties beheer je in het paneel "GBS Locaties".
#
#  4x SONOFF IP65 Zigbee temperatuur met display (sonde)   -> T1..T4
#  5x SONOFF AirGuard TH Pressure (temp / vocht / luchtdruk) -> A1..A5
#  Verwachte entity-id's: sensor.gbs_<id>_{temperature,humidity,pressure,battery}
# =====================================================================

lovelace:
  dashboards:
    gbs-sensoren:
      mode: yaml
      title: GBS Sensoren
      icon: mdi:thermometer-lines
      show_in_sidebar: true
      filename: dashboards/gbs_sensoren.yaml

input_select:
  gbs_actieve_sensor:
    name: "GBS – sensor die je nu plaatst"
    icon: mdi:cursor-default-click
    options: [""" + ", ".join(q(i.upper()) for i in ALLE) + "]\n"]
    for n, i in enumerate(ALLE):
        p.append(f"""  gbs_{i}_locatie:
    name: "GBS {i.upper()} – locatie"
    icon: {"mdi:thermometer-probe" if i in SONDES else "mdi:home-thermometer"}
""")
        if n == 0:
            p.append("    options: &locatie_opties\n")
            p += [f"      - {q(l)}\n" for l in locaties]
        else:
            p.append("    options: *locatie_opties\n")

    p.append("\ninput_text:\n")
    for i in ALLE:
        p.append(f"""  gbs_{i}_toelichting:
    name: "GBS {i.upper()} – toelichting plaatsing"
    icon: mdi:text
    max: 255
""")

    p.append("""
script:
  gbs_locatie_toewijzen:
    alias: "GBS – locatie toewijzen aan actieve sensor"
    icon: mdi:map-marker-check
    mode: queued
    fields:
      locatie:
        name: Locatie
        required: true
        selector:
          text:
    sequence:
      - action: input_select.select_option
        target:
          entity_id: "input_select.gbs_{{ states('input_select.gbs_actieve_sensor') | lower }}_locatie"
        data:
          option: "{{ locatie }}"
      - action: persistent_notification.create
        data:
          notification_id: gbs_locatie_toegewezen
          title: "Sensor geplaatst"
          message: "{{ states('input_select.gbs_actieve_sensor') }} staat nu op: {{ locatie }}"

template:
  - sensor:
""")
    kaart = "{" + ", ".join(f"{q(l)}: {q(foto_url(l, versies))}" for l in locaties) + "}"
    standaard = q(foto_url(NIET_GEPLAATST, versies))
    for i in ALLE:
        attrs = [
            ("soort", q(soort(i))),
            ("toelichting", f"\"{{{{ states('input_text.gbs_{i}_toelichting') }}}}\""),
            ("temperatuur", f"\"{{{{ states('sensor.gbs_{i}_temperature') }}}}\""),
        ]
        if i in AIRGUARDS:
            attrs += [
                ("luchtvochtigheid", f"\"{{{{ states('sensor.gbs_{i}_humidity') }}}}\""),
                ("luchtdruk", f"\"{{{{ states('sensor.gbs_{i}_pressure') }}}}\""),
            ]
        attrs.append(("batterij", f"\"{{{{ states('sensor.gbs_{i}_battery') }}}}\""))
        a = "".join(f"          {k}: {v}\n" for k, v in attrs)
        p.append(f"""      # {i.upper()}: state = gekozen locatie, picture = foto van die locatie
      - name: "GBS {i.upper()} plaatsing"
        unique_id: gbs_{i}_plaatsing
        icon: mdi:map-marker
        state: "{{{{ states('input_select.gbs_{i}_locatie') }}}}"
        picture: >-
          {{% set fotos = {kaart} %}}{{{{ fotos.get(states('input_select.gbs_{i}_locatie'), {standaard}) }}}}
        attributes:
{a}""")
    return "".join(p)


# ---------------------------------------------------------------- dashboard
def _sensor_sectie(i):
    tiles = [("temperature", "Temperatuur")]
    if i in AIRGUARDS:
        tiles += [("humidity", "Luchtvochtigheid"), ("pressure", "Luchtdruk")]
    tiles.append(("battery", "Batterij"))
    t = "".join(f"""          - type: tile
            entity: sensor.gbs_{i}_{k}
            name: {n}
            grid_options:
              columns: 6
""" for k, n in tiles)
    return f"""      - type: grid
        cards:
          - type: heading
            heading: "{i.upper()} · {soort(i)}"
            heading_style: subtitle
          - type: picture-entity
            entity: sensor.gbs_{i}_plaatsing
            name: "{i.upper()}"
            show_name: true
            show_state: true
            tap_action:
              action: navigate
              navigation_path: /gbs-sensoren/plaatsen
{t}          - type: markdown
            content: "📍 {{{{ states('input_text.gbs_{i}_toelichting') }}}}"
            visibility:
              - condition: state
                entity: input_text.gbs_{i}_toelichting
                state_not: ""
"""


def dashboard(locaties, versies):
    d = ["""# =====================================================================
#  GBS sensoren – dashboard (gemaakt door de app "GBS Sensoren")
#  Niet hier wijzigen: de app schrijft dit bestand opnieuw.
# =====================================================================
title: GBS Sensoren
views:
  - title: Overzicht
    path: overzicht
    icon: mdi:view-dashboard
    type: sections
    max_columns: 4
    sections:
      - type: grid
        column_span: 4
        cards:
          - type: heading
            heading: Alle sensoren
          - type: markdown
            grid_options:
              columns: full
            content: |
              | | Sensor | Locatie | Temp | Vocht | Druk | Batterij |
              |---|---|---|---|---|---|---|
              {% for id in [""" + ", ".join(f"'{i}'" for i in ALLE) + """] -%}
              {% set t = states('sensor.gbs_' ~ id ~ '_temperature') -%}
              {% set h = states('sensor.gbs_' ~ id ~ '_humidity') -%}
              {% set p = states('sensor.gbs_' ~ id ~ '_pressure') -%}
              {% set b = states('sensor.gbs_' ~ id ~ '_battery') -%}
              | {{ '🌡️' if id[0] == 't' else '🌬️' }} | **{{ id | upper }}** | {{ states('input_select.gbs_' ~ id ~ '_locatie') }} | {{ t ~ ' °C' if is_number(t) else '–' }} | {{ h ~ ' %' if is_number(h) else '–' }} | {{ p ~ ' hPa' if is_number(p) else '–' }} | {{ b ~ ' %' if is_number(b) else '–' }} |
              {% endfor %}
"""]
    d.append("      - type: grid\n        column_span: 4\n        cards:\n          - type: heading\n            heading: Temperatuursondes (IP65)\n")
    d += [_sensor_sectie(i) for i in SONDES]
    d.append("      - type: grid\n        column_span: 4\n        cards:\n          - type: heading\n            heading: AirGuard TH Pressure\n")
    d += [_sensor_sectie(i) for i in AIRGUARDS]

    d.append(f"""
  - title: Sensoren plaatsen
    path: plaatsen
    icon: mdi:map-marker-plus
    type: sections
    max_columns: 4
    sections:
      - type: grid
        column_span: 4
        cards:
          - type: heading
            heading: "Stap 1 – kies de sensor"
          - type: tile
            entity: input_select.gbs_actieve_sensor
            name: Sensor
            grid_options:
              columns: 6
            features:
              - type: select-options
          - type: markdown
            grid_options:
              columns: full
            content: |
              **T1–T4** = IP65 sonde met display · **A1–A5** = AirGuard TH Pressure

              Nu geselecteerd: **{{{{ states('input_select.gbs_actieve_sensor') }}}}**
              → huidige locatie: **{{{{ states('input_select.gbs_' ~ (states('input_select.gbs_actieve_sensor') | lower) ~ '_locatie') }}}}**

              *Locaties toevoegen, hernoemen of een foto geven: paneel **GBS Locaties** in de zijbalk.*
""")
    for i in ALLE:
        d.append(f"""          - type: conditional
            grid_options:
              columns: full
            conditions:
              - condition: state
                entity: input_select.gbs_actieve_sensor
                state: "{i.upper()}"
            card:
              type: entities
              title: "{i.upper()} – details"
              entities:
                - entity: input_select.gbs_{i}_locatie
                  name: Locatie (ook via foto's hieronder)
                - entity: input_text.gbs_{i}_toelichting
                  name: Toelichting (bv. 'bovenste plank, links')
""")
    d.append("""      - type: grid
        column_span: 4
        cards:
          - type: heading
            heading: "Stap 2 – tik op de foto van de locatie"
""")
    for l in locaties:
        d.append(f"""          - type: vertical-stack
            grid_options:
              columns: 4
            cards:
              - type: picture
                image: {q(foto_url(l, versies))}
                tap_action:
                  action: perform-action
                  perform_action: script.gbs_locatie_toewijzen
                  data:
                    locatie: {q(l)}
                  confirmation:
                    text: {q(f"Actieve sensor op '{l}' zetten?")}
              - type: markdown
                text_only: true
                content: {q(f"**{l}**")}
""")

    def grafiek(titel, ids, soort_):
        r = [f"""          - type: history-graph
            title: {titel}
            hours_to_show: 24
            grid_options:
              columns: full
            entities:
"""]
        r += [f"              - entity: sensor.gbs_{i}_{soort_}\n                name: {i.upper()}\n" for i in ids]
        return "".join(r)

    d.append("""
  - title: Grafieken
    path: grafieken
    icon: mdi:chart-line
    type: sections
    max_columns: 3
    sections:
      - type: grid
        column_span: 3
        cards:
""")
    d.append(grafiek("Temperatuur – alle sensoren (24 u)", ALLE, "temperature"))
    d.append(grafiek("Luchtvochtigheid (24 u)", AIRGUARDS, "humidity"))
    d.append(grafiek("Luchtdruk (24 u)", AIRGUARDS, "pressure"))
    return "".join(d)
