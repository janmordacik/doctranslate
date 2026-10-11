status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md
group: translation/engine
type: feature
estimate:
  time: 900–1565 min (15–26 hodin), součet leaf tasků včetně testů a review
  logical_lines: 3360–5600, součet substantivních změn včetně testů; ne počty přesunutých řádků
  tokens: 47k–84k pracovní odhad přes celý strom, nikoli pevný limit ani naměřená spotřeba
  subtasks: P01–P18 v samostatných issue souborech
description: Implementovat volitelné basic/advanced překladové moduly podle prvního návrhu v0.1 bez změny PDF sazby.

## Stav a rozsah

Toto je koordinační parent issue, nikoli jeden task pro Lunu.
[Autoritativní návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Návrh čeká na review; žádný leaf nezačal, tato dokumentační práce není
souhlas se spuštěním agenta nebo s implementací. Qwen/Continue zůstává vypnutý.

Jeden leaf je jeden samostatně reviewovatelný výsledek. Hierarchii vyjadřuje
tento index a group, dependency znamená skutečný předpoklad, ne parent category.
Každý leaf závisí na schváleném návrhu; další dependencies jsou konkrétní kód.
Koordinační parent nemá implementační prerequisite vazbu sám na sebe ani z dětí
zpět na roll-up dokončení. Uzavře se až po splnění zvoleného rozsahu a dětí.

## Hierarchie subtasků

### 1. Základní hranice

Součet: 175–305 min; 640–1060 logických řádků; 9–17 k pracovních tokenů.

| ID / task | Čas | Řádky | Tokeny | Závislost po schválení návrhu | Stav |
|---|---:|---:|---:|---|---|
| [P01 Regresní ochrana prvního výstupu JobRunner](3-2026-10-11-pm-p01-jobrunner-prvni-vystup.md) | 30–60 min | 100–180  | 2–4 k | none | created |
| [P02 Společný kontrakt engine a explicitní registr](3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md) | 40–70 min | 160–260  | 2–4 k | P01 | created |
| [P03 Basic engine nad injektovaným dávkovým executorem](3-2026-10-11-pm-p03-basic-engine.md) | 60–100 min | 200–320  | 3–5 k | P02 | created |
| [P04 Verzovaný checkpoint a účinná identita](3-2026-10-11-pm-p04-engine-checkpoint.md) | 45–75 min | 180–300  | 2–4 k | P02 | created |

### 2. Produkční napojení a volba jobu

Součet: 200–350 min; 760–1280 logických řádků; 11–19 k pracovních tokenů.

| ID / task | Čas | Řádky | Tokeny | Závislost po schválení návrhu | Stav |
|---|---:|---:|---:|---|---|
| [P05 Bezztrátový legacy XHTML a batch bridge](3-2026-10-11-pm-p05-legacy-xhtml-bridge.md) | 60–100 min | 200–340  | 3–5 k | P02, P03, P04 | created |
| [P06 JSON job selection a bezpečné publikování změn](3-2026-10-11-pm-p06-job-volba-modulu.md) | 40–70 min | 160–260  | 2–4 k | P02 | created |
| [P07 Produkční worker dispatch přes registry a bridge](3-2026-10-11-pm-p07-worker-engine-dispatch.md) | 50–90 min | 200–340  | 3–5 k | P03, P04, P05, P06 | created |
| [P08 Volba modulu v GUI a CLI](3-2026-10-11-pm-p08-gui-cli-volba-modulu.md) | 50–90 min | 200–340  | 3–5 k | P06, P07 | created |

### 3. Pokročilý standardní režim

Součet: 270–465 min; 1040–1700 logických řádků; 14–25 k pracovních tokenů.

| ID / task | Čas | Řádky | Tokeny | Závislost po schválení návrhu | Stav |
|---|---:|---:|---:|---|---|
| [P09 Sémantické segmenty a token-bounded dávky](3-2026-10-11-pm-p09-semantic-batch-planner.md) | 40–70 min | 180–300  | 2–4 k | P02, P05 | created |
| [P10 JSON glosář s revizemi a konflikty](3-2026-10-11-pm-p10-json-glossary-store.md) | 55–95 min | 200–340  | 3–5 k | P02, P04 | created |
| [P11 Relevantní glosář, konkordance a omezený kontext](3-2026-10-11-pm-p11-bounded-memory-context.md) | 55–95 min | 220–360  | 3–5 k | P09, P10 | created |
| [P12 ContextualBackend port a Ollama payload](3-2026-10-11-pm-p12-contextual-provider-port.md) | 55–95 min | 200–320  | 3–5 k | P02, P05, P11 | created |
| [P13 Standardní advanced engine a jeho aktivace](3-2026-10-11-pm-p13-advanced-standard-engine.md) | 65–110 min | 240–380  | 3–6 k | P03, P04, P07, P09, P10, P11, P12 | created |

### 4. Volitelné agentní rozšíření

Součet: 160–280 min; 600–1000 logických řádků; 8–14 k pracovních tokenů.

| ID / task | Čas | Řádky | Tokeny | Závislost po schválení návrhu | Stav |
|---|---:|---:|---:|---|---|
| [P14 Spravované memory nástroje a revision návrhy](3-2026-10-11-pm-p14-managed-memory-tools.md) | 50–90 min | 180–300  | 2–4 k | P10, P11, P13 | created |
| [P15 Volitelný AgentBackend a validované tool turns](3-2026-10-11-pm-p15-agent-backend-port.md) | 55–95 min | 200–340  | 3–5 k | P12, P14 | created |
| [P16 Omezená agentní relace, cílené opravy a recovery](3-2026-10-11-pm-p16-bounded-agent-session.md) | 55–95 min | 220–360  | 3–5 k | P04, P13, P14, P15 | created |

### 5. Ověření

Součet: 95–165 min; 320–560 logických řádků; 5–9 k pracovních tokenů.

| ID / task | Čas | Řádky | Tokeny | Závislost po schválení návrhu | Stav |
|---|---:|---:|---:|---|---|
| [P17 Standardní moduly – integrace a výkonový experiment](3-2026-10-11-pm-p17-standard-acceptance-benchmark.md) | 60–100 min | 200–340  | 3–5 k | P08, P13 | created |
| [P18 Extended režim – ověření schopností a režie](3-2026-10-11-pm-p18-extended-acceptance-benchmark.md) | 35–65 min | 120–220  | 2–4 k | P16, P17 | created |

## Milníky a pořadí

- M1: P01–P08. Basic zachová současný překlad, uživatel může volit modul
  a fronta eviduje ID/options. Advanced ještě není vydávaný za dostupný.
- M2: P09–P13 + P17. Standard advanced má relevantní glosář/kontext a checkpoint;
  bez tool calling. Tento milník může být dokončen nezávisle na extended.
- M3: P14–P16 + P18. Volitelné tools a omezené cílené revize; dostupnost
  až po model-specific ověření, nikoli podle názvu modelu.
- Doporučený lineární průchod: P01, P02, P03, P04, P05, P06, P07, P08,
  P09, P10, P11, P12, P13, P17; potom P14, P15, P16, P18.
  Nezávislé větve lze plánovat souběžně, ale ne editovat stejný repo dvěma agenty.

Odhady jsou engineering effort s implementací/testy/review, ne stopky Luny;
jednoduché generování může trvat podstatně kratší dobu. Nejde o závazek
provést vše během jednoho chatu. Nejistota vyšší u P05, P12, P15 a P16.
Čas live inference a ručního čtení překladu závisí na stroji a vzorku;
nepovažovat jej za přesně změřenou součást odhadu.

## Pravidla předání Luně

1. Předat jen jeden schválený leaf; vstupní kontext tvoří jeho Read sekce,
   uvedené zdroje a odpovídající část A19. Nečíst automaticky celé doc/tmp.
2. Znovu ověřit skutečné soubory/symboly. Nové plánované cesty jsou označené;
   pokud už existují, neprovádět overwrite, načíst a upravit task.
3. Dodržet veřejný kontrakt a forbidden scope. Nesilný agent nesmí řešit
   nejasný provider nebo markup heuristickou náhradou bez review.
4. V leafu průběžně uvádět created/progress/test/done a evidence testů.
   Comments nesmazat; doplnit skutečný čas/řádky/tokeny jen pokud dostupné.
5. Po jednom leafu diff review a testy, neskočit automaticky k celému parentu.
   Necommitovat/pushovat bez konkrétního souhlasu; nespouštět Qwen/Continue.
6. U zdrojů docstringy veřejných kontraktů a komentáře invariantů; structured
   events musí identifikovat module/revision/stage a odlišit měřené/odhadované tokeny.

Základní offline příkaz z repo root:
C:\Python314\python.exe -m pytest test -q
s PYTHONPATH nastaveným na absolutní src a bez sběru vnořeného checkoutu.
Cílené příkazy jsou v leaf issues. Na konci milníku celá sada, compileall,
git diff --check a revize relevantních A18/A19 UML/process index.

## Akceptace parentu

- Společný dokumentový kontrakt, per-job výběr basic/advanced a migrace legacy.
- M1/M2 fungují bez M3; nepodporovaný modul/provider selže s důvodem bez fallbacku.
- Ruční HTML a PDF sazba zachované; HTML→out nepotřebuje model.
- Paměť větší než prompt, budgety, konflikty, cancel/resume a bezpečný storage.
- P17/P18 neoznačí mock za kvalitativní ani výkonový důkaz živého modelu.
- Dokumentace a GUI/CLI manuál rozlišují dodané a dosud nedostupné režimy.
- Pokud se rozsah redukuje na M2, M3 neoznačit done: explicitně odložit do comments.

## comments

2026-10-11: Vytvořen hierarchický plán pro Codex Luna 5.6. Osmnáct leaf issues,
testy v každém tasku, tři dodávatelné milníky. Pouze plán, žádná implementace.
