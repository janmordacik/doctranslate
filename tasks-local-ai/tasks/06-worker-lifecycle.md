# 06 — Worker a životní cyklus jobů

status: created
last change: 2026-10-10
dependency: 05-queue-store.md
group: 04-queue
type: feature
description: Vytvořit worker jako samostatný proces s bezpečným singletonem, plánováním a restartem.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/01-architecture.md, context/02-contracts.md,
context/03-operational-constraints.md, zejména pravidla stavů.

## Úkol

Implementuj worker, který přežije restart aplikace a vybere nejdříve
in_progress, potom první prepared podle pořadí seznamu. paused, failed a done
přeskočí. Globální stop a pause se čtou po dokončení aktuální Ollama dávky.
Druhá instance se ukončí bez práce.

## Akceptace

- Start pouze nastartuje worker;
- stop zachová aktuální job jako in_progress s checkpointem;
- failed vyžaduje ruční návrat do prepared;
- pause nepoškodí checkpoint a další start pokračuje;
- worker zapisuje heartbeat a čitelný stav;
- PID/liveness kontrola je bezpečná pro cílový OS.

## Ověření

Fake backend testuj bez Ollamy: pořadí, stop, pause, restart, pád procesu,
singleton a stale worker lock.
