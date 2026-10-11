status: created
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p03-basic-engine.md, 3-2026-10-11-pm-p04-engine-checkpoint.md, 3-2026-10-11-pm-p05-legacy-xhtml-bridge.md, 3-2026-10-11-pm-p06-job-volba-modulu.md
group: translation/engine/worker
type: feature
estimate:
  time: 50–90 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Produkční worker dispatch přes registry a bridge.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev integration, leaf P07.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

Worker.run_job, control monitor, translate.main/run_translation/run_html_typesetting; A19 T05.

## Povolené soubory a symboly

- src/doctranslate/queue_worker.py
- src/doctranslate/translate.py
- src/doctranslate/integration/translation_bridge.py
- test/test_translation_worker.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Napojit vybraný engine do samotné překladové fáze, legacy I/O a PDF renderer ponechat. Každý job má nový frozen selection/context. Inject callbacks pro batch/progress/preview/cancel a logger; TypedCancelled mapovat na stávající in_progress/paused, error na failed.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 28–50 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 15–27 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 7–13 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Skutečný Worker.run_job fake test používá zvolený engine, ne jen osamělý JobRunner.
- HTML→out nevytváří engine ani provider; unavailable job neblokuje následující basic.
- Log/state obsahuje modul/revizi; polling heartbeat a 10s preview zůstanou.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_worker.py test/test_queue_app.py test/test_cli_input.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Neprovádět full přepis translate.py/JobRunner ani importní přesuny jiného refaktoringu.
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
