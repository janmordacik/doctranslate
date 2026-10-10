# 01 — Cílová architektura

## Vrstvy

~~~mermaid
classDiagram
    class Frontend {
        <<GUI or CLI>>
        +load()
        +edit()
        +update()
        +start()
        +stop()
        +status()
    }
    class QueueStore {
        <<JSON Repository>>
        +load()
        +transaction()
        +write_atomic()
    }
    class Worker {
        +acquire_singleton()
        +select_job()
        +run_batch()
        +persist_state()
    }
    class TranslationCore {
        +read_xhtml()
        +translate_blocks()
        +write_xhtml()
    }
    class FormatAdapter {
        <<plugin>>
        +read()
        +write()
    }
    Frontend --> QueueStore
    Worker --> QueueStore
    Worker --> TranslationCore
    TranslationCore --> FormatAdapter
~~~

Frontend a worker jsou samostatné procesy. Frontend při Update zapíše frontu a
podle potřeby worker nastartuje. Start worker pouze spustí nebo obnoví. Worker
si ověří singleton zámkem; druhá instance se korektně ukončí.

## Životní cyklus

~~~mermaid
sequenceDiagram
    actor User
    participant UI as GUI/CLI
    participant Q as queue.json
    participant W as worker
    participant T as translation core
    User->>UI: přidá nebo upraví job
    UI->>Q: Update atomickým zápisem
    UI->>W: start, pokud neběží
    W->>Q: načte frontu a zamkne worker
    loop po jobech
        W->>Q: vybere in_progress, jinak první prepared
        W->>T: zpracuje dávku
        T-->>W: checkpoint
        W->>Q: načte stop/pause po dávce
    end
    User->>UI: Stop
    UI->>Q: jednorázový příkaz stop
    W->>Q: spotřebuje stop po dokončení dávky
~~~

## Zámky a soubory

- queue.json: trvalé zadání a runtime stav jobů.
- queue.json.lock: krátký zámek transakce, nikdy nedržet během Ollamy.
- worker.lock: singleton workeru.
- worker-state.json: heartbeat, aktivní job a poslední známý stav.
- queue.json.bak: poslední platná záloha, pokud je to bezpečně možné.

Zápis musí být temp-file + flush/fsync + atomické nahrazení. Stale lock nesmí
být převzat pouze podle stáří bez bezpečného ověření vlastníka.
