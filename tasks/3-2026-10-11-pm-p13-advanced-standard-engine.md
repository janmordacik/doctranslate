status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p03-basic-engine.md, 3-2026-10-11-pm-p04-engine-checkpoint.md, 3-2026-10-11-pm-p07-worker-engine-dispatch.md, 3-2026-10-11-pm-p09-semantic-batch-planner.md, 3-2026-10-11-pm-p10-json-glossary-store.md, 3-2026-10-11-pm-p11-bounded-memory-context.md, 3-2026-10-11-pm-p12-contextual-provider-port.md
group: translation/engine/advanced
type: feature
estimate:
  time: 65–110 min, implementace + cílené testy + review
  logical_lines: 240–380 včetně testů/dokumentace
  tokens: 3–6 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Standardní advanced engine a jeho aktivace.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev standard, leaf P13.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 kontrakt/Checkpoint; standard-only pipeline; P03–P12 public APIs, ne celé legacy.

## Povolené soubory a symboly

- src/doctranslate/translation/advanced.py (nový)
- src/doctranslate/translation/registry.py
- src/doctranslate/translation/checkpoint.py
- test/test_advanced_translation_engine.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Orchestrace planner→context→backend→validate→commit, bounded targeted retry. Schválený glosář snapshot a term_bindings do checkpointu. Progress/metrics po batch, cancel i během HTTP pokud backend podporuje. Registrovat advanced standard až po fake integraci.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 36–61 min | 144–228  | 1.7–3.3 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 20–33 min | 96–152  | 1–2.1 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 9–16 min | 0 nových | 0.3–0.6 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Bez tool calling zpracuje unikátní dlouhý fake dokument v omezeném kontextu.
- Resume nevolá AI pro validní segmenty; text/markup/resources jsou zachované.
- Strict vs warn je explicitní; strukturální/neúplný výstup nikdy done. Registry advanced standard available jen s compatible backendem.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_advanced_translation_engine.py test/test_translation_worker.py test/test_translation_checkpoint.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný úplný druhý AI průchod nebo autonomní extraction prepass. Nesilent fallback basic.
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


2026-10-11: P13 implementován v translation/advanced.py a aktivaci registry. Standard advanced engine orchestruje planner → bounded context → contextual backend → quality validation → XHTML apply → checkpoint, bez tool calling; podporuje warn/strict, bounded retry, cancel, progress/preview, glossary term bindings a resume. Registry helper advanced označí jako unavailable bez kompatibilního factory a neprovádí silent fallback.

2026-10-11: Validace: cílené testy 15 passed; celá sada 217 passed, 4 subtests passed. git diff --check bez nálezu.

2026-10-11: Omezení: composition root queue worker stále nedodává konkrétní advanced factory; P13 připravuje engine a registry contract, skutečné runtime zapojení backendu je samostatná integrační práce.
