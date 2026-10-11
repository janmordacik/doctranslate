status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md, 3-2026-10-11-pm-p04-engine-checkpoint.md
group: translation/engine/memory
type: feature
estimate:
  time: 55–95 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: JSON glosář s revizemi a konflikty.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev standard, leaf P10.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A18 Paměť a A19 Checkpoint; checkpoint writer injection z P04.

## Povolené soubory a symboly

- src/doctranslate/translation/memory.py (nový)
- test/test_translation_memory.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Entry/proposal/history schéma, load/snapshot/lookup/propose, idempotence. Oddělit origin, accepted/proposed/conflict; klíč zahrne jazyky+sense/scope. Standard čte schválenou paměť. CAS revision a atomický single-writer zápis.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 30–52 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 17–29 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 8–14 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Homonyma a různé scopes nejsou automaticky sloučené.
- Conflict nepřepíše accepted; opakovaný proposal nezaloží nekonečnou historii.
- Read-only/full disk/crash/invalid JSON vrátí bezpečnou chybu a zachová poslední validní stav.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_memory.py test/test_translation_checkpoint.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádná vektorová DB, NER plošný AI prepass ani globálně sdílený glosář bez concurrency návrhu.
Necommitovat, nepushovat, nespouštět lokální Qwen/Continue. Runtime/GUI/live
ověření mimo offline testy uvést jako samostatný krok, nikoli tvrdit hotové.

## Restart a comments

S01: created
S02: created
S03: created
Actual time: unavailable
Actual logical lines: unavailable
Actual tokens: unavailable

2026-10-11: Připraveno pro Lunu jako jeden bounded leaf. Implementace nezačala;
dotaz/blokátor/důvod neprovedení doplnit sem, nikoli odhadnout mimo kontrakt.
