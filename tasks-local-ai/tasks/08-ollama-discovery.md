# 08 — Discovery modelů Ollamy

status: created
last change: 2026-10-10
dependency: 01-baseline-and-bootstrap.md, 07-frontend-controls.md
group: 06-backend
type: feature
description: Zobrazit dostupné lokální modely a odlišit offline, empty a invalid stav bez automatické instalace.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/02-contracts.md, context/03-operational-constraints.md
a GUI část 07-frontend-controls.md.

## Úkol

Přidej discovery přes Ollama /api/tags s timeoutem mimo GUI thread.
Combobox modelu zobrazuje dostupné modely podle aktuální nabídky. Rozlišuj
available, empty, offline a invalid. Uložený model nepřepisuj jen proto, že
discovery selhalo. Neinstaluj model automaticky.

## Akceptace

- UI se nezablokuje při pomalé nebo mrtvé Ollamě;
- invalid JSON/HTTP/timeout je diagnostikovatelný;
- prázdný seznam není prezentován jako offline;
- job si nese vlastní model;
- fake HTTP testy pokryjí všechny čtyři stavy.

## Ověření

Použij fake endpoint; živou Ollamu nepovažuj za nutnou pro uzavření tasku.
