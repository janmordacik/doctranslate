# 03 — Překladová pipeline

status: created
last change: 2026-10-10
dependency: 02-xhtml-contract.md
group: 02-core
type: feature
description: Oddělit překlad XHTML bloků od formátového vstupu a bezpečně zachovat inline markup.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/01-architecture.md, context/02-contracts.md,
context/03-operational-constraints.md.

## Úkol

Implementuj Strategy/protokol pro překlad backendem a pipeline, která přijme
XHTML dokument a vrátí nový dokument. Výsledek backendu musí jednoznačně
odpovídat vstupu. Entity, inline tagy, hard breaks a textové uzly nesmí být
tiše poškozeny. Při nejednoznačném plain-text výsledku operaci odmítni.

## Akceptace

- pipeline neimportuje PyMuPDF ani renderer;
- backend lze nahradit fake implementací v testu;
- platný inline markup se zachová;
- None, chybná cardinalita a nevalidní výsledek mají čitelnou chybu;
- testy ověří, že vstupní dokument není mutován.

## Ověření

Spusť unit testy pipeline včetně entity, tagu, více uzlů, exception a fake
backendu. Živý Ollama běh není podmínkou.
