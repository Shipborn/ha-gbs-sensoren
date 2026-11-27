"""Zorgt dat configuration.yaml de packages-map laadt.

Exitcodes: 0 = al goed, 10 = aangepast, 3 = packages staat er anders in (niet aangepast),
2 = geen configuration.yaml.
"""
import re
import shutil
import sys

REGEL = "packages: !include_dir_named packages"

pad = sys.argv[1]
try:
    tekst = open(pad, encoding="utf-8").read()
except FileNotFoundError:
    print(f"[GBS] {pad} niet gevonden")
    sys.exit(2)

bestaand = re.search(r"^[ \t]+packages[ \t]*:(.*)$", tekst, re.M)
if bestaand:
    waarde = bestaand.group(1).strip()
    if re.match(r"!include_dir_named\s+packages/?(\s*#.*)?$", waarde):
        sys.exit(0)
    print(f"[GBS] LET OP: packages staat al in configuration.yaml als '{waarde}'. "
          f"Niet aangepast; zorg zelf dat /config/packages/gbs_sensoren.yaml geladen wordt.")
    sys.exit(3)

kop = re.search(r"^homeassistant[ \t]*:[ \t]*(#.*)?$", tekst, re.M)
if kop:
    inspring = "  "
    for regel in tekst[kop.end():].splitlines():
        if regel.strip() and not regel.lstrip().startswith("#"):
            gevonden = re.match(r"^([ \t]+)", regel)
            if gevonden:
                inspring = gevonden.group(1)
            break
    nieuw = tekst[:kop.end()] + f"\n{inspring}{REGEL}" + tekst[kop.end():]
else:
    nieuw = tekst.rstrip("\n") + f"\n\nhomeassistant:\n  {REGEL}\n"

shutil.copy2(pad, pad + ".voor-gbs")
open(pad, "w", encoding="utf-8").write(nieuw)
print(f"[GBS] '{REGEL}' toegevoegd aan configuration.yaml (kopie: configuration.yaml.voor-gbs)")
sys.exit(10)
