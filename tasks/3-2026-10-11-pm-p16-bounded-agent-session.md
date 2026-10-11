status: created
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p04-engine-checkpoint.md, 3-2026-10-11-pm-p13-advanced-standard-engine.md, 3-2026-10-11-pm-p14-managed-memory-tools.md, 3-2026-10-11-pm-p15-agent-backend-port.md
group: translation/engine/session
type: feature
estimate:
  time: 55–95 min, implementace + cílené testy + review
  logical_lines: 220–360 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Omezená agentní relace, cílené opravy a recovery.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev extended, leaf P16.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 limity a T03/T06; Tools/AgentBackend contracts a dirty IDs.

## Povolené soubory a symboly

- src/doctranslate/translation/session.py (nový)
- src/doctranslate/translation/advanced.py
- src/doctranslate/translation/checkpoint.py
- test/test_translation_session.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Sekvenční smyčka s max calls/tools/revisions/time/tokens; opakovaný dotaz bez změny zastaví. Cílená revize, source/candidate/context a paměť. Paměť commit před checkpointem; crash/revision reconciliation. Žádná rostoucí historie celého díla.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 30–52 min | 132–216  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 17–29 min | 88–144  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 8–14 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Scripted model nemůže překročit budget ani cyklit; cancel nepřijme stale output.
- Dirty segment se revaliduje nebo explicitně zůstane unresolved dle policy.
- Crash mezi dvěma soubory nezpůsobí reuse neexistující term revision; checkpoint obsahuje text/markup i term bindings.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_session.py test/test_translation_tools.py test/test_translation_checkpoint.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný iterativní konsenzus bez limitu ani plný přepis architektury backendů.
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
