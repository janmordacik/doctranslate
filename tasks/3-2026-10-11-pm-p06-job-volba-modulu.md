status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md
group: translation/engine/job-schema
type: feature
estimate:
  time: 40–70 min, implementace + cílené testy + review
  logical_lines: 160–260 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: JSON job selection a bezpečné publikování změn.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev integration, leaf P06.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

QueueStore._normalise, make_job, merge_queue_jobs, copy_selected_job, JobOptions.from_job a JobSpec.

## Povolené soubory a symboly

- src/doctranslate/queue_app.py
- src/doctranslate/queue_worker.py
- src/doctranslate/job_runner.py
- test/test_queue_app.py
- test/test_translation_job_selection.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Přidat translator_id/options, legacy default basic, copy a merge invariants. Store validuje syntaxi, nikoli runtime dostupnost: jeden unavailable ID nesmí znepřístupnit celou frontu. Změna aktivního translator fingerprint musí invalidovat daný job po Update.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 22–39 min | 96–156  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 12–21 min | 64–104  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 6–10 min | 0 nových | 0.2–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Missing ID → basic, kopie zachová options bez sdílené mutovatelné mapy.
- Syntakticky platný unavailable modul lze v detailu zobrazit; worker později hlásí konkrétní chybu.
- Update nesouvisejícího jobu neruší AI; změna aktivního ID/options ruší pouze jeho běh.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_job_selection.py test/test_queue_app.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný draft status ani nový IPC/server; neměnit pořadí jobů, stop/start chování nebo lokální koncept Update jobs.
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
