status: created
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p09-semantic-batch-planner.md, 3-2026-10-11-pm-p10-json-glossary-store.md
group: translation/engine/context
type: feature
estimate:
  time: 55–95 min, implementace + cílené testy + review
  logical_lines: 220–360 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Relevantní glosář, konkordance a omezený kontext.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev standard, leaf P11.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 Plánování a paměť; planner/map a GlossaryStore.snapshot.

## Povolené soubory a symboly

- src/doctranslate/translation/retrieval.py (nový)
- src/doctranslate/translation/context.py (nový)
- test/test_translation_context.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

RAM indexes: exact+aliases+casefold+lexical; scope/lang filters, deterministic ranking. Source occurrences a omezené předchozí překlady. ContextEnvelope má source/target/context data oddělené od instrukcí a hlídá prompt i output rezervu.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 30–52 min | 132–216  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 17–29 min | 88–144  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 8–14 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Paměť větší než prompt vrací bounded top výsledky + more indicator, ne celý JSON.
- Read-only okolí se nikdy nepovažuje za překládané segmenty.
- Pořadí a budget jsou deterministické; bez místa pro source vrátit chybu, ne zdroj zkrátit.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_context.py test/test_translation_planning.py test/test_translation_memory.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádné embeddingy/GraphRAG ani kopírování celé historie chatu.
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
