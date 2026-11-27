import os, re, sys
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HIER, "..", "gbs_sensoren", "bestanden")

LOCATIES = [
    "Niet geplaatst",
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

SONDES = ["t1", "t2", "t3", "t4"]          # SONOFF IP65 temperatuur met display (sonde)
AIRGUARDS = ["a1", "a2", "a3", "a4", "a5"]  # SONOFF AirGuard TH Pressure
ALLE = SONDES + AIRGUARDS


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def soort(i):
    return "Sonde (IP65, display)" if i in SONDES else "AirGuard TH Pressure"


# ---------------------------------------------------------------- package
p = []
p.append("""# =====================================================================
#  GBS sensoren – package
#  4x SONOFF IP65 Zigbee temperatuur met display (sonde)   -> T1..T4
#  5x SONOFF AirGuard TH Pressure (temp / vocht / luchtdruk) -> A1..A5
#
#  Verwachte entity-id's (na hernoemen van de Zigbee-apparaten naar
#  "GBS T1" ... "GBS A5", zie README):
#    sensor.gbs_t1_temperature, sensor.gbs_t1_battery
#    sensor.gbs_a1_temperature, sensor.gbs_a1_humidity,
#    sensor.gbs_a1_pressure,    sensor.gbs_a1_battery
#
#  Dit bestand wordt gemaakt door tools/genereer.py en neergezet door
#  de app "GBS Sensoren". Niet in HA zelf wijzigen: een update van de
#  app overschrijft het.
# =====================================================================

# Het dashboard in de zijbalk (bestand wordt door de app neergezet)
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
    options: [""" + ", ".join(f'"{i.upper()}"' for i in ALLE) + """]
""")
first = True
for i in ALLE:
    p.append(f"""  gbs_{i}_locatie:
    name: "GBS {i.upper()} – locatie"
    icon: {"mdi:thermometer-probe" if i in SONDES else "mdi:home-thermometer"}
""")
    if first:
        p.append("    options: &locatie_opties\n")
        for l in LOCATIES:
            p.append(f'      - "{l}"\n')
        first = False
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
        example: "Binnen voorzijde"
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
for i in ALLE:
    attrs = [
        ("soort", f'"{soort(i)}"'),
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
        picture: "/local/sensorlocaties/{{{{ states('input_select.gbs_{i}_locatie') | slugify }}}}.jpg"
        attributes:
{a}""")

os.makedirs(f"{OUT}/packages", exist_ok=True)
open(f"{OUT}/packages/gbs_sensoren.yaml", "w").write("".join(p))

# ---------------------------------------------------------------- dashboard
d = []
d.append("""# =====================================================================
#  GBS sensoren – dashboard (YAML-modus)
#  Aangemeld via 'lovelace:' in packages/gbs_sensoren.yaml
# =====================================================================
title: GBS Sensoren
views:
  # ------------------------------------------------------------ OVERZICHT
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
""")


def sensor_section(i):
    tiles = [("temperature", "Temperatuur")]
    if i in AIRGUARDS:
        tiles += [("humidity", "Luchtvochtigheid"), ("pressure", "Luchtdruk")]
    tiles.append(("battery", "Batterij"))
    t = "".join(
        f"""          - type: tile
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


d.append("      - type: grid\n        column_span: 4\n        cards:\n          - type: heading\n            heading: Temperatuursondes (IP65)\n")
for i in SONDES:
    d.append(sensor_section(i))
d.append("      - type: grid\n        column_span: 4\n        cards:\n          - type: heading\n            heading: AirGuard TH Pressure\n")
for i in AIRGUARDS:
    d.append(sensor_section(i))

# ------------------------------------------------------------ PLAATSEN
d.append("""
  # ------------------------------------------------------------ PLAATSEN
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
              columns: 6
            content: |
              **T1–T4** = IP65 sonde met display · **A1–A5** = AirGuard TH Pressure

              Nu geselecteerd: **{{ states('input_select.gbs_actieve_sensor') }}**
              → huidige locatie: **{{ states('input_select.gbs_' ~ (states('input_select.gbs_actieve_sensor') | lower) ~ '_locatie') }}**
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
for l in LOCATIES:
    d.append(f"""          - type: picture
            image: /local/sensorlocaties/{slug(l)}.jpg
            grid_options:
              columns: 4
            tap_action:
              action: perform-action
              perform_action: script.gbs_locatie_toewijzen
              data:
                locatie: "{l}"
              confirmation:
                text: "Actieve sensor op '{l}' zetten?"
          - type: heading
            heading: "{l}"
            heading_style: subtitle
            grid_options:
              columns: 4
""")
# fix: heading under picture needs same column width; use vertical-stack instead
# ------------------------------------------------------------ GRAFIEKEN
d.append("""
  # ------------------------------------------------------------ GRAFIEKEN
  - title: Grafieken
    path: grafieken
    icon: mdi:chart-line
    type: sections
    max_columns: 3
    sections:
      - type: grid
        column_span: 3
        cards:
          - type: history-graph
            title: Temperatuur – alle sensoren (24 u)
            hours_to_show: 24
            grid_options:
              columns: full
            entities:
""")
for i in ALLE:
    d.append(f"              - entity: sensor.gbs_{i}_temperature\n                name: {i.upper()}\n")
d.append("""          - type: history-graph
            title: Luchtvochtigheid (24 u)
            hours_to_show: 24
            grid_options:
              columns: full
            entities:
""")
for i in AIRGUARDS:
    d.append(f"              - entity: sensor.gbs_{i}_humidity\n                name: {i.upper()}\n")
d.append("""          - type: history-graph
            title: Luchtdruk (24 u)
            hours_to_show: 24
            grid_options:
              columns: full
            entities:
""")
for i in AIRGUARDS:
    d.append(f"              - entity: sensor.gbs_{i}_pressure\n                name: {i.upper()}\n")

dash = "".join(d)
# Replace picture+heading pairs by vertical-stacks so caption stays under its photo
blocks = []
for l in LOCATIES:
    old = f"""          - type: picture
            image: /local/sensorlocaties/{slug(l)}.jpg
            grid_options:
              columns: 4
            tap_action:
              action: perform-action
              perform_action: script.gbs_locatie_toewijzen
              data:
                locatie: "{l}"
              confirmation:
                text: "Actieve sensor op '{l}' zetten?"
          - type: heading
            heading: "{l}"
            heading_style: subtitle
            grid_options:
              columns: 4
"""
    new = f"""          - type: vertical-stack
            grid_options:
              columns: 4
            cards:
              - type: picture
                image: /local/sensorlocaties/{slug(l)}.jpg
                tap_action:
                  action: perform-action
                  perform_action: script.gbs_locatie_toewijzen
                  data:
                    locatie: "{l}"
                  confirmation:
                    text: "Actieve sensor op '{l}' zetten?"
              - type: markdown
                text_only: true
                content: "**{l}**"
"""
    assert old in dash
    dash = dash.replace(old, new)
dash = dash.replace("# fix: heading under picture needs same column width; use vertical-stack instead\n", "")

os.makedirs(f"{OUT}/dashboards", exist_ok=True)
open(f"{OUT}/dashboards/gbs_sensoren.yaml", "w").write(dash)

# ---------------------------------------------------------------- placeholders
os.makedirs(f"{OUT}/www/sensorlocaties", exist_ok=True)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 54)
    small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
except Exception:
    font = small = ImageFont.load_default()
for n, l in enumerate(LOCATIES):
    if os.path.exists(f"{OUT}/www/sensorlocaties/{slug(l)}.jpg"):
        continue  # bestaande (echte) foto niet overschrijven
    img = Image.new("RGB", (800, 600), (38, 70, 83) if l != "Niet geplaatst" else (90, 90, 90))
    dr = ImageDraw.Draw(img)
    dr.rectangle([20, 20, 780, 580], outline=(233, 196, 106), width=4)
    w = dr.textlength(l, font=font)
    dr.text(((800 - w) / 2, 250), l, font=font, fill="white")
    s = f"vervang door foto: {slug(l)}.jpg"
    w2 = dr.textlength(s, font=small)
    dr.text(((800 - w2) / 2, 340), s, font=small, fill=(233, 196, 106))
    img.save(f"{OUT}/www/sensorlocaties/{slug(l)}.jpg", quality=85)

print("ok", [slug(l) for l in LOCATIES])
