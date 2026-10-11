status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md, 3-2026-10-11-pm-p05-legacy-xhtml-bridge.md, 3-2026-10-11-pm-p11-bounded-memory-context.md
group: translation/engine/backend
type: feature
estimate:
  time: 55–95 min, implementace + cílené testy + review
  logical_lines: 200–320 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: ContextualBackend port a Ollama payload.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev standard, leaf P12.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

PromptBuilder.build, HttpAiBackend.translate_precomposed a translate_segments; OllamaBackend._call_precomposed; A19 provider porty.

## Povolené soubory a symboly

- src/doctranslate/ai/context_backend.py (nový)
- src/doctranslate/ai/ollama.py
- src/doctranslate/ai/translation.py
- test/test_contextual_backend.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Volitelný contextual translate_batch port se zachovanými IDs/markup mapping. Fake transport a Ollama adapter skutečně předají envelope, ne jen nevyužité request.context. Capability check pro model/prompt; stávající plain AiBackend zůstane kompatibilní.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 30–52 min | 120–192  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 17–29 min | 80–128  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 8–14 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Fake payload obsahuje kontext/glosář oddělený od instrukcí a nepřidává jej do překladu.
- Provider/model bez capability je odmítnut jen pro advanced režim, basic funguje.
- Specializovaný TranslateGemma prompt se nepřepisuje univerzálním agentním promptem bez ověření.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_contextual_backend.py test/test_ai_style_payloads.py test/test_ai_providers.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Neměnit OAuth/cloud konfiguraci ani přidávat cloud SDK. Live smoke jen explicitně a krátký.
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


2026-10-11: P12 implementován. Nový ai/context_backend.py definuje volitelný ContextualBackend, capability check, request/result kontrakt a strict ID/markup decoder. OllamaBackend přidává contextual_capability() a translate_batch(), který posílá source, instructions a bounded context jako oddělené payload části; TranslateGemma zachovává vlastní prompt strategy. Legacy AiBackend/translate_segments se nemění.

2026-10-11: Validace: cílené testy 11 passed, 4 subtests passed; celá sada 211 passed, 4 subtests passed. git diff --check bez nálezu.

2026-10-11: Omezení: capability je deklarovaná adaptérem a živý Ollama smoke nebyl spuštěn; skutečnou dostupnost konkrétního modelu musí ověřit provider probe/runtime.
