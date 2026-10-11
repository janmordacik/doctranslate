status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md
group: translation/engine/regression
type: bug
estimate:
  time: 30–60 min, implementace + cílené testy + review
  logical_lines: 100–180 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Regresní ochrana prvního výstupu JobRunner.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev foundation, leaf P01.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

JobRunner.run, _load_checkpoint/_save_checkpoint; translated_markup; test_run_writes_output_and_restart_uses_checkpoint.

## Povolené soubory a symboly

- src/doctranslate/job_runner.py
- src/doctranslate/translate_core/pipeline.py
- test/test_job_runner.py

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Nejprve zachytit první output_adapter.write ještě před resume. Opravit aplikaci nových i obnovených výsledků do dokumentu a bezpečné mapování markup. Složitý markup bez mapy odmítnout, nesmazat tagy.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 17–33 min | 60–108  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 9–18 min | 40–72  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 4–9 min | 0 nových | 0.2–0.4 k | S02 |

U tohoto bug tasku začít S02 reprodukcí před S01 opravou; nový regression test nejprve musí selhat.

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- První i obnovený výstup obsahuje překlad, nikoli pouze checkpoint.
- Text/markup jsou konzistentní; metadata/resources/ID/pořadí zůstávají.
- Test první fáze před opravou reprodukuje nález; do comments uložit výsledek.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_job_runner.py test/test_translate_core.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Neměnit produkční legacy PDF tok ani zobecňovat renderer.
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
