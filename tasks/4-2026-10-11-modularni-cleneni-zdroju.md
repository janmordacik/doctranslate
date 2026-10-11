status: created
last change: 2026-10-11
dependency: none
group: architecture/source-layout
type: refactor
estimate:
  time: 3–6 hodin čisté práce; offline regrese průběžně
  logical_lines: 400–800 včetně testů a dokumentace
  tokens: 20k–40k pracovní orientace; zadávat po subtascích
  subtasks: M01–M08 níže, každý samostatně reviewovatelný
description: Rozdělit velké zdrojové moduly do podadresářů podle odpovědností bez změny veřejného spuštění a chování.
Priority: 4 (low)
Created: 2026-10-11

## Cíl

Postupně rozdělit zdrojový kód podle modulů a odpovědností. Zachovat:

- python -m doctranslate;
- translate.cmd;
- veřejné CLI parametry;
- queue JSON kompatibilitu;
- existující PDF/XHTML a provider kontrakty;
- možnost práce bez Ollamy ve fázi PDF-only.

Neprovádět mechanické dělení podle počtu souborů. Každý přesun musí mít
jasnou odpovědnost, testovatelnou hranici a minimální importní cyklus.

## Cílová struktura

~~~text
src/doctranslate/
├── ai/
├── benchmark/
├── cli/
├── config/
├── documents/
│   ├── input/
│   ├── output/
│   └── xhtml/
├── queue/
│   ├── store.py
│   ├── worker.py
│   └── controller.py
├── translation/
│   ├── pipeline.py
│   ├── batching.py
│   └── cache.py
├── gui/
└── observability/
~~~

Stávající formats/ a translate_core/ nejprve pouze zmapovat. Jejich sloučení
neprovádět ve stejném kroku jako dělení queue nebo translation runtime.

## Pořadí subtasků

| ID | Výsledek | Odhad času | Odhad řádků | Závislost |
|---|---|---:|---:|---|
| M01 | inventář symbolů, importních hranic a cyklů | 10–20 min | 30–60 | none |
| M02 | queue model/store/controller rozdělené do queue/ | 30–60 min | 120–220 | M01 |
| M03 | worker oddělený od GUI a queue persistence | 25–50 min | 80–160 | M02 |
| M04 | translation runtime rozdělený na pipeline/batch/cache | 45–90 min | 180–350 | M01 |
| M05 | PDF typesetting a document boundary oddělené od překladu | 30–60 min | 100–200 | M04 |
| M06 | benchmark/config/CLI přesunuty bez změny launcheru | 20–40 min | 70–140 | M04 |
| M07 | importní kompatibilita, package exports a regresní testy | 30–60 min | 100–200 | M02–M06 |
| M08 | UML, modulová dokumentace a závěrečná kontrola | 20–40 min | 40–100 | M07 |

Subtasky se mají dělit podle chování a hranic modulů, ne pouze podle počtu
řádků. Po každém subtasku provést cílené testy a diff review.

## Akceptační kritéria

- žádný nový importní cyklus mezi queue, translation, documents a ai;
- python -m doctranslate --help funguje;
- translate.cmd a GUI fungují stejně jako před refaktoringem;
- offline testy projdou explicitním příkazem C:\Python314\python.exe -m pytest test -q;
- compileall a git diff --check projdou;
- PDF-only fáze neimportuje ani nespouští AI backend;
- struktura a procesní změny jsou popsány Mermaid class/sequence diagramy;
- veřejné API se mění pouze po explicitním zdokumentování;
- nevzniknou kompatibilní kopie zdrojových souborů ve starých cestách.

## Navržené hranice

~~~mermaid
classDiagram
    class CLI {
        +main()
    }
    class Queue {
        +QueueStore
        +WorkerController
        +Worker
    }
    class Translation {
        +TranslationPipeline
        +BatchTranslator
        +TranslationCache
    }
    class Documents {
        +InputAdapter
        +XhtmlDocument
        +OutputAdapter
    }
    class AI {
        +Provider
        +StyleLibrary
    }
    class Observability {
        +JsonEventLogger
        +PerformanceRecorder
    }
    CLI --> Queue
    Queue --> Translation
    Translation --> Documents
    Translation --> AI
    Queue --> Observability
    Translation --> Observability
~~~

~~~mermaid
sequenceDiagram
    actor User
    participant CLI_GUI
    participant Queue
    participant Worker
    participant Translation
    participant Documents
    participant AI
    CLI_GUI->>Queue: publish job or start worker
    Worker->>Queue: read next job
    Worker->>Translation: run job
    Translation->>Documents: read input into XHTML
    alt translation phase
        Translation->>AI: translate text blocks
        AI-->>Translation: translated blocks
    else PDF-only phase
        Note over Translation,AI: AI is not called
    end
    Translation->>Documents: write HTML/PDF output
    Translation-->>Worker: progress or error
    Worker->>Queue: persist state
~~~

## comments

2026-10-11: Task založen na požadavku začít dělit zdrojáky do podadresářů podle modulů. Doporučeno postupné dělení queue, translation runtime, document boundary a benchmark/CLI. Implementace nebyla zahájena.

2026-10-11: Před M04/M05 zohlednit návrh v 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md. Jde o související architektonické rozhodnutí; mapování a queue refaktoring může pokračovat nezávisle. PDF sazbu cílově ponechat ve výstupním document adaptéru.

2026-10-11: První návrh překladových modulů v0.1 je v doc/modularization-analysis.md
A19, implementační parent 3-2026-10-11-prekladove-moduly-implementace.md.
Translation package obsahuje pouze formátově nezávislé engine/memory/planning
služby. PDF typesetting odstraněn z plánované translation struktury; patří
do document output adaptéru. Nevytvářet dva konkurenční refaktoringy týchž
symbolů; M04/M05 musí koordinovat P03/P05/P07. Queue přesuny nejsou jejich blokátor.
