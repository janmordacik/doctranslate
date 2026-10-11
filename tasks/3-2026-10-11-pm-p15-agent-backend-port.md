status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p12-contextual-provider-port.md, 3-2026-10-11-pm-p14-managed-memory-tools.md
group: translation/engine/agent-backend
type: feature
estimate:
  time: 55–95 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Volitelný AgentBackend a validované tool turns.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev extended, leaf P15.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 AgentBackend; existující HTTP transport a cancel; P14 schémata, žádná cloud config.

## Povolené soubory a symboly

- src/doctranslate/ai/context_backend.py
- src/doctranslate/ai/ollama.py
- test/test_agent_backend.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

request_turn port a typed final/tool response. Ollama adaptér může použít podporované native tools nebo striktní JSON envelope, ale nesmí automaticky tvrdit schopnost podle jména modelu. Fake scripted turns, odpovědi a chybové parsing testy.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 30–52 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 17–29 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 8–14 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Odmítnout hybridní/malformed response, neznámé nástroje a falešný final.
- Tool schemas jsou bounded; nepatří do výsledného textu.
- Extended capability se enable až po krátkém model-specific smoke; bez něj zůstává nedostupná, standard může fungovat.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_agent_backend.py test/test_contextual_backend.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný LangGraph/ReAct framework, skryté placené cloud volání nebo plný nový provider subsystém.
Necommitovat, nepushovat, nespouštět lokální Qwen/Continue. Runtime/GUI/live
ověření mimo offline testy uvést jako samostatný krok, nikoli tvrdit hotové.

## Restart a comments

S01: done
S02: done
S03: done
Actual time: not measured; completed in one bounded implementation pass
Actual logical lines: approximately 430 including adapter, contract and tests; slightly above estimate due provider validation and strict envelope coverage
Actual tokens: not measured

2026-10-11: Připraveno pro Lunu jako jeden bounded leaf. Implementace nezačala;
dotaz/blokátor/důvod neprovedení doplnit sem, nikoli odhadnout mimo kontrakt.


2026-10-11: P15 implementován. Přidán AgentBackend/AgentTurnRequest/AgentTurnResponse
port, explicitní AgentCapability a strictní decoder final/tool JSON obálky.
Hybridní, malformed, prázdné a neznámé tool odpovědi jsou typed errors; tool
arguments mají bounded payload.

2026-10-11: Ollama adapter podporuje jeden agentní turn pouze při explicitním
agent_tools_enabled=True. Název modelu sám schopnost neaktivuje. Payload používá
striktní JSON envelope a odpověď se validuje proti allowlistu nástrojů. Orchestrace
turnů zůstává mimo provider.

2026-10-11: Validace: cílené testy 11 passed; celá sada 233 passed, 4 subtests
passed; compileall src/doctranslate prošel; git diff --check bez nálezu.

2026-10-11: Omezení pro další task: flag agent_tools_enabled není sám smoke test
proti živému modelu; jeho zapnutí musí řídit vyšší konfigurace po ověření. P15
nepřidává bounded agentní smyčku ani napojení MemoryTools, to řeší P16.
