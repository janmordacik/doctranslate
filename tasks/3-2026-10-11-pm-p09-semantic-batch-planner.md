status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md, 3-2026-10-11-pm-p05-legacy-xhtml-bridge.md
group: translation/engine/planning
type: feature
estimate:
  time: 40–70 min, implementace + cílené testy + review
  logical_lines: 180–300 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Sémantické segmenty a token-bounded dávky.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev standard, leaf P09.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 Plánování; XhtmlBlock/fragment mapping z P05, chráněné literály a style IDs.

## Povolené soubory a symboly

- src/doctranslate/translation/planning.py (nový)
- test/test_translation_planning.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Planner podle odstavců/vět při překročení limitu, vždy stable IDs/mapa. Injektovaný TokenCounter a konzervativní fallback. Page number jen metadata; okolní text nikdy není output. Zahrnout rezervy instrukcí/schema/výstupu.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 22–39 min | 108–180  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 12–21 min | 72–120  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 6–10 min | 0 nových | 0.2–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Hranice, prázdný text, oversized věta a chráněný fragment mají definovaný výsledek.
- Žádná ztráta/duplikace segmentů po zpětném mapování.
- Odhad je explicitně estimated; sama input délka nepředstírá celý context budget.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_planning.py test/test_translation_bridge.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádné velké NLP dependencies ani univerzální optimální velikost kontextu.
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
