status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p10-json-glossary-store.md, 3-2026-10-11-pm-p11-bounded-memory-context.md, 3-2026-10-11-pm-p13-advanced-standard-engine.md
group: translation/engine/tools
type: feature
estimate:
  time: 50–90 min, implementace + cílené testy + review
  logical_lines: 180–300 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Spravované memory nástroje a revision návrhy.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev extended, leaf P14.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A18 tabulka nástrojů, A19 memory view/write ordering; accepted/conflict store APIs.

## Povolené soubory a symboly

- src/doctranslate/translation/tools.py (nový)
- src/doctranslate/translation/memory.py
- test/test_translation_tools.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Dispatch allowlist lookup_terms/search_memory/get_occurrences/get_source/propose_term/request_revision. Validovat schéma, scope, IDs a token limit; model nedostane filesystem. Změny paměti označí již dotčené segmenty dirty a vedou revision history.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 28–50 min | 108–180  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 15–27 min | 72–120  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 7–13 min | 0 nových | 0.2–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Neznámý tool, neexistující ID/scope a příliš velký výsledek mají typed error.
- Proposal conflict zůstane návrhem, nové accepted entry mají evidence a idempotenci.
- Nástroj neprovádí vlastní AI smyčku; request_revision pouze vrací validovaný požadavek.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_tools.py test/test_translation_memory.py test/test_translation_context.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný obecný file/shell tool ani samovolné mazání či přepis zdrojových dokumentů.
Necommitovat, nepushovat, nespouštět lokální Qwen/Continue. Runtime/GUI/live
ověření mimo offline testy uvést jako samostatný krok, nikoli tvrdit hotové.

## Restart a comments

S01: done
S02: done
S03: done
Actual time: not measured; completed in one bounded implementation pass
Actual logical lines: approximately 837 including 560 new tool lines, 170 test lines and 107 changed store lines; above estimate due explicit CAS decisions and evidence persistence
Actual tokens: not measured

2026-10-11: Připraveno pro Lunu jako jeden bounded leaf. Implementace nezačala;
dotaz/blokátor/důvod neprovedení doplnit sem, nikoli odhadnout mimo kontrakt.


2026-10-11: P14 implementován. Přidán allowlist MemoryTools pro lookup_terms, search_memory,
get_occurrences, get_source, propose_term, accept_proposal, reject_proposal a
request_revision. Všechny dotazy mají validaci schématu, limit výsledků a tokenový
limit; výsledky vracejí revision a more. Nástroje používají pouze injektovaný store
a datové providery, model nedostává filesystem ani obecné volání metod.

2026-10-11: JsonGlossaryStore rozšířen o evidence u návrhů/schválených termínů,
explicitní CAS reject a ochranu proti přechodu rejected/accepted. Runtime dirty
segment IDs se sbírají při návrhu a žádosti o revizi; trvalé checkpointové
propojení zůstává navazující integrace.

2026-10-11: Validace: cílené testy 23 passed; celá sada 227 passed, 4 subtests
passed; compileall src/doctranslate prošel; git diff --check bez nálezu.

2026-10-11: Omezení pro další task: MemoryTools zatím není zapojen do AI backendu
ani AdvancedTranslationEngine, occurrence/source provider se předává při sestavení
a search_memory prohledává revision history lineárně. Vektorový index, persistentní
dirty segment state a automatická tool-calling smyčka jsou mimo tento leaf.
