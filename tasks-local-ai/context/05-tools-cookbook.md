# 05 — Kuchařka nástrojů pro izolovaný běh

Toto je samostatná kopie užitečných postupů. Neodkazuje na stav hlavního
projektu ani na hotové issues. Po každém workaroundu ověř výsledek cíleným
testem a uveď skutečný příkaz i výstup.

## Začátek práce

1. Ověř aktuální pracovní adresář a git status --short.
2. Načti pouze kontext tasku, který právě řešíš.
3. Před zápisem ověř cílový adresář a zachovej existující uživatelské změny.
4. Po změně zkontroluj diff, relevantní testy a případně celý offline test.
5. Necommituj, nepushuj a nespouštěj živý překlad bez explicitního pověření.

## Recept 1 — Shell nástroj selže při vytvoření procesu

Příznak: shell wrapper nebo exec_command skončí chybou CreateProcess nebo
helper_unknown_error.

Postup: použij přímé spuštění přes node:child_process.execFile bez shellu.
Zachyť návratový kód, stdout a stderr. Dlouhé příkazy rozděl na menší kroky.

Ověření: zopakuj stejný cílený příkaz a zaznamenej, že výsledek je
reprodukovatelný.

## Recept 2 — apply_patch z nesprávného pracovního adresáře

Příznak: apply_patch hlásí, že nemůže zapsat soubor, ačkoli cílový adresář
má být zapisovatelný.

Postup: zjisti aktuální launcher pomocí where.exe apply_patch. Pokud jde o
Windows .bat wrapper, načti z něj cestu k aktuálnímu Codex executable a spusť
přímo executable s argumenty --codex-run-as-apply-patch, patch jako jediný
samostatný argument a cwd nastaveným na kořen projektu. Nepoužívej shellovou
interpolaci patch textu.

Ověření: návratový kód, očekávaný diff a znovunačtení změněných souborů.
Přímý fs.writeFile není náhrada za projektovou editaci.

## Recept 3 — Git odmítne repozitář kvůli vlastnictví

Příznak: fatal: detected dubious ownership.

Postup: ke čtecím příkazům přidej explicitní bezpečný adresář:

    git -c safe.directory=C:/path/to/project status --short

Adresář nejprve ověř; nepřidávej široký kořen disku.

## Recept 4 — REPL hlásí redeklaraci

Příznak: opakovaný const nebo let binding koliduje s předchozím během.

Postup: použij nový název bindingu, nebo resetuj REPL a načti jen nutné
moduly. Warning nezaměňuj za úspěch příkazu.

## Recept 5 — Chybí nástroj nebo volitelná závislost

Příznak: Python, pytest, PDF knihovna, Ollama nebo model není dostupný.

Postup: ověř dostupnost malým read-only probe. Pokud je závislost mimo rozsah
tasku, pokračuj fake backendem nebo offline testem. Pokud bez ní nelze
akceptaci ověřit, zapiš blokaci s přesným příkazem, výstupem a návrhem
workaroundu. Nevytvářej falešný zelený výsledek přes tiché přeskočení.

## Evidence

Nový opakovatelný problém zapisuj ve tvaru:

    Recept: stručný název
    Příznak: přesná chyba nebo pozorování
    Postup: ověřené kroky workaroundu
    Ověření: jak bylo potvrzeno
    Stav: funkční / fallback / omezení
    Datum: RRRR-MM-DD
