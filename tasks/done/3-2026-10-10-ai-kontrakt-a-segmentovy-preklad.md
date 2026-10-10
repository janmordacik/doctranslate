status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-kanonicke-xhtml-a-codec.md
group: translation/core/segments
type: refactor
description:
M04: Samostatné textové API a neutrální segmentová pipeline
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A06, A07, A10; UML A03/P04/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
ai/contracts.py, ai/registry.py, ai/prompts.py, translate_core/pipeline.py; prepare_text_translation/restore_text_translation/validate_batch_translation z legacy.

Recommended change:
1. Zavést translate(text, source_language,target_language)->str. Provider/model/options jsou immutable instance config; text samostatně použitelný bez dokumentů/PDF.
2. Volitelný translate_segments(SegmentRequest)->SegmentResult s IDs/text/context a per-segment chyby. Žádné PDF/XHTML style typy v provider kontraktu.
3. Core zajišťuje DOM segmentaci, placeholders/čísla/spaces/hard breaks a aplikaci výsledků; zachovat validované partial výsledky, block done jen všechny fragmenty.
4. Sdílený PromptBuilder: dokument data, ne instrukce; prompt revision pro cache. Strukturovaný režim capability-based, nikoli Ollama payload v pipeline.
5. BackendError code/message/remedy/retryable/request_id/retry_after; bezpečný transport/error boundary a společný konečný retry budget.
6. Empty/whitespace bez requestu; jazyky normalizovat, und/auto jen podporuje-li backend.

Acceptance:
1. Fake plain/backend batch přeloží stejné fragmenty a zachová tags/entities/IDs/TOC čísla/line breaks.
2. Missing/duplicate/extra IDs, None, unsafe markup, moved markers, empty/refusal/truncated output odmítnout; partial přeložené jednotky lze obnovit.
3. Prompt injection text v dokumentu zůstane datovým vstupem pod skutečnou instrukcí; payload test ověří oddělení.
4. Backend ani core neimportují PDF/GUI/provider SDK. Retry 429/5xx vs quota/auth je konečný, Stop brání dalšímu requestu.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován provider-neutral text/segment kontrakt, PromptBuilder, validace ID/placeholders a bounded retry.

comments:
2026-10-10: M04 dokončen; segmentová a prompt-safety regrese prošly.
2026-10-10: Založeno jako M04; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Nehádat přiřazení stylů z poměru délek přeložené věty. Regrese done XHTML tasku musí zůstat pokryté.
