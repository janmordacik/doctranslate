status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p08-gui-cli-volba-modulu.md, 3-2026-10-11-pm-p13-advanced-standard-engine.md
group: quality/translation-engine/standard
type: test
estimate:
  time: 60–100 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Standardní moduly – integrace a výkonový experiment.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev verification, leaf P17.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 A05; současné benchmark model/style režimy a PerformanceRecorder; celý task strom jen index/status.

## Povolené soubory a symboly

- test/test_translation_engine_integration.py (nový)
- src/doctranslate/ai/benchmark.py
- src/doctranslate/benchmark_cli.py
- doc/technical-overview.md
- doc/user-manual.md
- doc/modularization-analysis.md

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

End-to-end fake Worker a adapters, mixed basic/advanced joby, render-only, cancel/resume, failure. Krátký engine benchmark stejného unique fixture a modelu pro basic vs standard: stdout+JSONL, čas/token/opravy/quality metadata. Stávající model benchmark neporušit.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 33–55 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 18–30 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 9–15 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Full offline suite a compileall + diff check; žádný live AI v default unit tests.
- Live EN→CS krátký warm/cold běh a ruční quality review vykázat odděleně, bez smyšleného score.
- Aktualizovat implemented vs proposed a process index; bez live výsledků task test, nikoli tvrzení o zrychlení.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_engine_integration.py test/test_benchmark_cli.py test/test_performance.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný 493/1000stránkový benchmark ani velká sazba PDF; neřešit stylový backlog.
Necommitovat, nepushovat, nespouštět lokální Qwen/Continue. Runtime/GUI/live
ověření mimo offline testy uvést jako samostatný krok, nikoli tvrdit hotové.

## Restart a comments

S01: done
S02: done
S03: done
Actual time: not measured; completed in one bounded implementation pass
Actual logical lines: approximately 407 including 215 integration-test lines, 130 benchmark lines and documentation; above estimate due mixed-engine coverage
Actual tokens: not measured

2026-10-11: Připraveno pro Lunu jako jeden bounded leaf. Implementace nezačala;
dotaz/blokátor/důvod neprovedení doplnit sem, nikoli odhadnout mimo kontrakt.


2026-10-11: P17 implementován. Přidán EngineBenchmarkRunner pro basic/advanced
nad jedním fixture hash, s časem, textem, tokenovou bilancí, počtem oprav,
quality stavem a serializací JSONL. Stávající Ollama modelový benchmark zůstal
beze změny.

2026-10-11: Přidána offline integrační sada pro WorkerTranslationDispatcher,
smíšenou volbu basic/advanced, cancel, failure, stejný fixture a failure
izolaci. Dokumentace technical-overview, user-manual a modularization-analysis
obsahuje aktuální implemented/proposed stav a Mermaid proces T07.

2026-10-11: Validace: cílené testy 13 passed; celá sada 245 passed, 4 subtests
passed; compileall src/doctranslate prošel; git diff --check bez nálezu.
Mermaid byl ověřen textově; v prostředí nebyl k dispozici renderer.

2026-10-11: Omezení pro další task: benchmark runner je provider-neutral API,
nepřidává nový CLI switch pro engine comparison a live EN→CS quality/throughput
zůstává samostatným ručním během s Ollamou.
