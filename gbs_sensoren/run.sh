#!/bin/bash
# Zet de GBS-bestanden in de HA-configmap en herstart HA als dat nodig is.
set -uo pipefail

OPTIES=${OPTIES:-/data/options.json}
CONFIG=${CONFIG_DIR:-/homeassistant}
BRON=${BRON:-/gbs}
APP_YAML=${APP_YAML:-/gbs_app.yaml}
HULP=${HULP:-/zet_packages_aan.py}
AUTO_RESTART=$(jq -r '.auto_restart // true' "$OPTIES" 2>/dev/null || echo true)
FOTOS_OVERSCHRIJVEN=$(jq -r '.fotos_overschrijven // false' "$OPTIES" 2>/dev/null || echo false)

log() { echo "[GBS] $*"; }
herstart_nodig=0

zet_neer() {  # $1 = pad relatief aan BRON/CONFIG, $2 = 1 als een wijziging een herstart vraagt
    if ! cmp -s "$BRON/$1" "$CONFIG/$1"; then
        mkdir -p "$(dirname "$CONFIG/$1")"
        cp "$BRON/$1" "$CONFIG/$1"
        log "bijgewerkt: $1"
        [ "$2" = 1 ] && herstart_nodig=1
    fi
}

log "Versie $(sed -n 's/^version: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' "$APP_YAML" 2>/dev/null), configmap $CONFIG"

zet_neer packages/gbs_sensoren.yaml 1
zet_neer dashboards/gbs_sensoren.yaml 0   # YAML-dashboard: verversen van de browser is genoeg

# /local werkt pas na een herstart als www/ nieuw is
[ -d "$CONFIG/www" ] || herstart_nodig=1
mkdir -p "$CONFIG/www/sensorlocaties"
for foto in "$BRON"/www/sensorlocaties/*.jpg; do
    naam=$(basename "$foto")
    doel="$CONFIG/www/sensorlocaties/$naam"
    if [ ! -f "$doel" ] || [ "$FOTOS_OVERSCHRIJVEN" = true ]; then
        cmp -s "$foto" "$doel" || { cp "$foto" "$doel"; log "foto: $naam"; }
    fi
done

python3 "$HULP" "$CONFIG/configuration.yaml"
[ $? -eq 10 ] && herstart_nodig=1

if [ "$herstart_nodig" = 1 ]; then
    if [ "$AUTO_RESTART" = true ] && [ -n "${SUPERVISOR_TOKEN:-}" ]; then
        log "Configuratie controleren..."
        antwoord=$(curl -s -X POST -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/core/check)
        if [ "$(echo "$antwoord" | jq -r '.result')" = ok ]; then
            log "Configuratie is geldig, Home Assistant wordt herstart"
            curl -s -X POST -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/core/restart >/dev/null
        else
            log "FOUT in de configuratie, NIET herstart: $(echo "$antwoord" | jq -r '.message')"
        fi
    else
        log "Herstart Home Assistant om de wijzigingen te laden"
    fi
else
    log "Niets veranderd dat een herstart nodig heeft"
fi

log "Klaar. De app blijft draaien zodat een update de bestanden opnieuw neerzet."
[ -n "${GBS_TEST:-}" ] || exec tail -f /dev/null
