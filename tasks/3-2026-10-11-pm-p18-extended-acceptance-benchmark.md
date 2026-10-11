status: created
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p16-bounded-agent-session.md, 3-2026-10-11-pm-p17-standard-acceptance-benchmark.md
group: quality/translation-engine/extended
type: test
estimate:
  time: 35–65 min, implementace + cílené testy + review
  logical_lines: 120–220 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Extended režim – ověření schopností a režie.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev extended-verification, leaf P18.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

T02/T03/T06 a P17 benchmark; explicitní provider/model capability evidence.

## Povolené soubory a symboly

- test/test_translation_engine_integration.py
- test/test_translation_session.py
- src/doctranslate/ai/benchmark.py
- doc/modularization-analysis.md
- doc/technical-overview.md

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Doplnit benchmark standard vs extended na stejných unique fixtures. Scripted fake quality issues, tool budgets a restart; krátký live tool smoke + porovnání oprav jen pokud dostupný kompatibilní model.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 19–36 min | 72–132  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 11–20 min | 48–88  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 5–9 min | 0 nových | 0.2–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Ollama model a digest/quant/context uvedené; fake test není vydáván za ověřenou jazykovou kvalitu.
- Report uvádí AI/tool calls, overhead, unresolved a konkrétní EN→CS chyby.
- Chybějící capability nebo live přístup zaznamenat do comments; basic/standard milestone zůstává použitelný.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_engine_integration.py test/test_translation_session.py test/test_benchmark_cli.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Nespouštět nepodporované cloud tool calls ani automaticky měnit výchozí modul na advanced.
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
