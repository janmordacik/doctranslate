# Translate

Aktuální revize odolnosti, priorit a kódu: [revize 2026-10-10](review-2026-10-10.md). Jednotlivé plaintext issues jsou v [tasks](../tasks/); význam priorit a formát stavu jsou v revizi. Popis níže je stav implementace, nikoli záruka integračního ověření.

Struktura adresářů, formát tasků, dependency/group/type a pořadí jejich zpracování jsou závazně popsané v [pravidlech projektu a úloh](project-structure-and-tasks.md).

Nové zadání: [modularizace dokumentů a AI poskytovatelů](modularization-analysis.md) obsahuje cílové kontrakty, UML diagramy a 14 navazujících implementačních tasků. Jde o plán, nikoli již implementovanou podporu cloudů. Tato část níže popisuje dosavadní stav.

## Účel

translate.py je nástroj pro překlad dokumentů s důrazem na zachování rozložení. Překlad je postupně oddělován od práce s PDF:

- vstupní formát se převede na XHTML dokument s metadaty a bloky textu,
- překladové jádro pracuje nad tímto dokumentem a nezná PDF API,
- vstupní a výstupní formáty jsou adaptery/pluginy,
- výstupní renderer rozhoduje o sazbě, zarovnání a vložení zdrojů.

Aktuální produkční cesta je stále PDF → XHTML/HTML → PDF. Nový kontrakt v src/doctranslate/translate_core/ poskytuje stabilní hranici pro další formáty.

## Funkce a stav vývoje

| Oblast | Stav |
|---|---|
| PDF vstup přes PyMuPDF | existující a funkční |
| Překlad přes Ollama API | existující; závisí na dostupnosti endpointu a modelu |
| Cache po validovaných blocích | existující |
| Restart podle .plan.json | existující |
| XHTML/HTML s metadaty | implementováno jako core kontrakt a bridge z legacy extrakce |
| PDF sazba bez Ollamy | existující |
| Zarovnání běžných odstavců do obou okrajů | implementováno heuristikou |
| Zarovnání TOC/seznamů vlevo | implementováno heuristikou |
| Zachování řádků TOC z fragmentovaných PDF spanů | implementováno; regresní test pro strany 4–6 |
| PDF input/output adapter | rozhraní a první implementace existují; produkční tok dosud legacy, output vyžaduje renderer |
| Registr adapterů | implementován |
| Formátově nezávislá pipeline | kontrakt implementován; úplné převedení legacy sazby je další krok |
| Konfigurovatelný model a Ollama endpoint | implementováno přes -model, -ollama-url a prostředí |
| AI provider moduly, profily a cloud autentizace | připravená analýza a tasky; zatím neimplementováno |
| translate.cmd runner | implementováno |
| Strukturovaný run log a výjimky | implementováno pro překlad; fronta/GUI/worker mají vlastní JSONL event log |
| Dávková fronta v JSON | implementováno |
| Worker jako samostatný proces | implementováno, ale revize odhalila blokující importy/launcher a chybu Windows PID kontroly |
| Průběh aktuálního jobu | implementováno přes worker-state.json; GUI progress bar, stavový text a CLI status |
| GUI bez parametrů | implementováno |
| Konfigurovatelný workdir a jazyk GUI | implementováno; bez konfigurace aktuální adresář |
| Lokalizace GUI cs/en | implementováno; výchozí podle locale |
| Mazání jobu v GUI | implementováno; při mazání aktivního jobu Update vyžádá potvrzení, zapíše změnu a worker sám přeruší právě běžící AI požadavek |
| CLI add/start/pause/stop/status | implementováno |
| Jednorázový globální stop | implementováno; spolehlivost závisí na opravě worker liveness a hraničních přechodů |
| Živá změna nastavení během dávky | běžné změny se uplatní podle pollu; invalidace aktuálního jobu se během AI překladu zpracuje okamžitě |
| TranslateGemma 12B | implementována verzovaná Ollama prompt strategie; lokální benchmark proti qwen3.8:27b proběhl, TranslateGemma byla na tomto stroji rychlejší; úplné kvalitativní hodnocení zůstává omezené na krátký fixture |
| TranslateGemma 4B | strategie je implementována; model je dostupný v Ollamě a benchmark 4B/12B/Qwen byl dokončen |
| Srovnání TranslateGemma/Qwen 3.8 | dokončeno pro 4B, 12B a qwen3.8:27b v [reportu](../tmp/translategemma-smoke/comparison-2026-10-11.md); doporučení je podmíněné krátkým fixture |
| Náhled aktuálního překládaného bloku | implementováno a otestováno v [tasku 3-2026-10-11-gui-nahled-aktualniho-bloku.md](../tasks/3-2026-10-11-gui-nahled-aktualniho-bloku.md); dávkový snapshot bez streamování |
| Vizuální regresní test PDF | odloženo |
| GitHub push | odloženo; pracuje se lokálně |

## Architektura překladového jádra

~~~mermaid
classDiagram
    class XhtmlDocument {
        +SourceMetadata metadata
        +Sequence~XhtmlBlock~ blocks
        +str html
        +with_blocks(blocks) XhtmlDocument
    }

    class SourceMetadata {
        +str source_path
        +str media_type
        +str source_language
        +str target_language
        +int page_count
        +int layout_revision
    }

    class XhtmlBlock {
        +str block_id
        +int page_number
        +int order
        +str text
        +str markup
        +bbox
        +translated(text) XhtmlBlock
    }

    class DocumentInputAdapter {
        <<protocol>>
        +read(source) XhtmlDocument
    }

    class DocumentOutputAdapter {
        <<protocol>>
        +write(document, target) Path
    }

    class TranslationBackend {
        <<protocol>>
        +translate(texts, source_language, target_language) Sequence
    }

    class TranslationPipeline {
        +TranslationBackend backend
        +translate(document) XhtmlDocument
    }

    class PdfInputAdapter {
        +read(source) XhtmlDocument
    }

    class PdfOutputAdapter {
        +write(document, target) Path
    }

    class AdapterRegistry {
        +register(media_type, adapter)
        +get(media_type) adapter
    }

    XhtmlDocument *-- SourceMetadata
    XhtmlDocument *-- XhtmlBlock
    TranslationPipeline --> TranslationBackend
    TranslationPipeline --> XhtmlDocument
    DocumentInputAdapter <|.. PdfInputAdapter
    DocumentOutputAdapter <|.. PdfOutputAdapter
    AdapterRegistry --> DocumentInputAdapter
    AdapterRegistry --> DocumentOutputAdapter
~~~

Jádro src/doctranslate/translate_core/ neimportuje PyMuPDF. PDF závislost je v src/doctranslate/translate_core/pdf_adapter.py a ve stávající legacy orchestraci. Výstupní PDF adapter přijímá renderer přes dependency injection, takže lze přidat HTML, EPUB nebo DOCX bez změny překladového jádra.

## Architektura fronty

Frontend (GUI nebo CLI) pracuje s JSON frontou. Worker je druhý proces, který frontu načte, provádí joby a po každé dokončené Ollama dávce znovu načte řídicí data. Trvalé IPC není použito.

~~~mermaid
classDiagram
    class QueueStore {
        +Path path
        +load() QueueSnapshot
        +transaction(mutator) QueueSnapshot
        +set_jobs(jobs) QueueSnapshot
        +update_job(id, changes) QueueSnapshot
        +request_stop() QueueSnapshot
        +consume_stop() QueueSnapshot
    }

    class FileLock {
        +Path path
        +acquire()
        +release()
    }

    class QueueFrontend {
        <<GUI or CLI>>
        +add()
        +start()
        +pause(job)
        +stop()
        +status()
        +send()
    }

    class QueueWorker {
        +choose_job()
        +run_job(job)
        +after_batch()
        +write_state()
    }

    class QueueJson {
        +int schema
        +int revision
        +ControlItem control
        +JobItem[] jobs
    }

    QueueFrontend --> QueueStore
    QueueWorker --> QueueStore
    QueueStore --> FileLock
    QueueStore --> QueueJson
    QueueWorker --> FileLock : worker.lock singleton
~~~

### Soubory

| Soubor | Účel |
|---|---|
| workdir/queue.json | trvalá fronta a stav jobů |
| workdir/queue.lock | krátký zámek zápisu fronty |
| workdir/queue.bak | poslední předchozí snapshot jako záloha |
| workdir/worker.lock | zámek jediné instance workeru |
| workdir/worker-state.json | heartbeat, PID, stav, aktivní job a průběh aktuální fáze |
| workdir/queue.events.log | strukturované JSONL události fronty, GUI, CLI a workeru |
| workdir/worker.log | surový stdout/stderr procesu workeru pro diagnostiku spuštění |
| *.tmp | krátkodobý soubor při atomické výměně |

Po ukončení workeru proběhne konzervativní retenční úklid v adresáři fronty a
v adresářích odkazovaných joby. Výchozí politika nemaže vstupní PDF, výstupní
PDF ani HTML; po 30 dnech odstraňuje pouze starší reprodukovatelné sidecary
(plány, cache, logy a diagnostiku) a ponechává nejnovější dvě sady. Během
živého workeru se úklid přes zámek přeskočí. Ruční náhled nebo spuštění je
`translate.cmd cleanup --dry-run` a `translate.cmd cleanup`; stáří lze změnit
parametrem `--older-than-days N`. Současně se hlídá limit 50 MiB na jeden
sidecar a 250 MiB souhrnně v jednom pracovním adresáři. Překročení se zapíše
do reportu; při úklidu se odstraní nejstarší nechráněné sidecary, nikdy se
nezkracuje aktivní překladová cache.

Zámek se vytváří atomicky přes O_CREAT | O_EXCL. Zápis probíhá do dočasného souboru s fsync a následným os.replace. Obnova podle PID je zamýšlená, ale revize odhalila nebezpečnou PID kontrolu na Windows a závody stale recovery. Do opravy nelze tuto část považovat za spolehlivou; viz [revize](review-2026-10-10.md). Runtime soubory jsou ignorované Gitem. Cesty k worker.lock a worker-state.json se odvozují od konkrétního souboru fronty.

### Schéma fronty

~~~json
{
  "schema": 1,
  "revision": 7,
  "updated_at": "2026-10-10T12:00:00+00:00",
  "items": [
    {
      "kind": "control",
      "id": "worker-control",
      "command": null,
      "request_id": null,
      "updated_at": null
    },
    {
      "kind": "job",
      "id": "job-a1b2c3",
      "input": "book.pdf",
      "output": "book-cs-layout.pdf",
      "inlang": "en",
      "outlang": "cs",
      "model": "translategemma:12b",
      "phase": "both",
      "state": "prepared",
      "progress": 0.0,
      "error": null
    }
  ]
}
~~~

Kontrolní řádek není běžný job. Příkaz stop je jednorázový: worker ho spotřebuje a odstraní po obsluze, aby další start automaticky nepřerušil novou dávku. Pokud worker právě překládá, sleduje příkaz stop také uvnitř AI požadavku. Při Update jiného jobu pokračuje; pokud Update změní právě překládaný job na jiný stav nebo ho smaže, worker tuto invalidaci zjistí podle `current_job_id` a okamžitě zruší AI požadavek. Ollama klient při zrušení uzavře aktivní HTTP socket, uloží job jako `in_progress` (pokud stále existuje) a worker skončí. Další Start pokračuje z posledního checkpointu. Při sazbě PDF zůstává stop kooperativní na bezpečné hranici. U providerů bez podpory zrušení síťového požadavku se přerušení projeví po návratu aktuálního volání.

### Stavy jobu a plánování

| Stav | Význam | Automatické zpracování |
|---|---|---|
| prepared | připravený job | ano, podle pořadí v seznamu |
| in_progress | nedokončený job s checkpointem | ano, vždy před prepared |
| paused | uživatelem pozastavený job | ne; uživatel ho vrátí na prepared |
| failed | poslední běh skončil výjimkou | ne; uživatel ho musí ručně vrátit na prepared |
| done | dokončený job | ne |

Neexistují číselné priority. Pořadí prepared jobů je pořadí v JSON seznamu; GUI ho mění šipkami. Po globálním stopu zůstává aktuální job in_progress a pokračuje z checkpointu po dalším start. Stop nebo vypnutí počítače proto nemusí resetovat práci.

Mazání `in_progress` jobu je záměrně chráněno proti souběhu se živým workerem. GUI při Update zobrazí potvrzení a po něm změnu zapíše; worker průběžně zjistí, že jeho job zmizel, okamžitě přeruší AI požadavek a skončí. Samotná frontová vrstva bez explicitního `allow_active_delete` mazání stále odmítá; tím zůstává bezpečná i pro jiné klienty. Update jiného jobu nebo změna polí, která aktuální job neruší, překlad nepřerušuje.

~~~mermaid
sequenceDiagram
    actor User
    participant Frontend as GUI / CLI
    participant Queue as queue.json
    participant Worker as queue_worker.py
    participant Ollama as Ollama
    participant Translate as doctranslate.translate

    User->>Frontend: add / edit / pause
    Frontend->>Frontend: GUI drží neodeslané editace lokálně
    User->>Frontend: Update nebo CLI add
    Frontend->>Queue: uloží změny
    Frontend->>Worker: spustí proces, pokud neběží
    Worker->>Queue: acquire worker.lock
    loop každý job
        Worker->>Queue: vybere in_progress, jinak první prepared
        Worker->>Translate: spustí job s checkpointem
        loop Ollama dávky
            Translate->>Ollama: přeloží dávku
            Ollama-->>Translate: překlady
            Translate->>Worker: after_batch()
            Worker->>Queue: zkontroluje stop/pause/invalidaci jobu
            Worker->>Queue: průběžně sleduje current_job_id
            alt Aktuální job smazán nebo není in_progress
                Worker->>Translate: cancel_event
                Translate->>Ollama: uzavře aktivní HTTP požadavek
                Worker->>Queue: zachová checkpoint nebo job odstraní
            else Jiný job nebo neprovozní změna
                Worker->>Translate: pokračuje
            end
        end
        Worker->>Queue: zapíše done, failed nebo in_progress
    end
    User->>Frontend: stop
    Frontend->>Queue: command=stop
    Worker->>Queue: spotřebuje command=stop
~~~

## Konfigurace pracovního adresáře a jazyka

Konfigurace je volitelný soubor `translate.config.json` v aktuálním pracovním adresáři; cestu lze nastavit přes `TRANSLATE_CONFIG_FILE`. Chybějící soubor použije výchozí nastavení, poškozený se neignoruje.

~~~json
{
  "schema": 1,
  "workdir": "C:\\data\\doctranslate",
  "language": "cs"
}
~~~

Pokud konfigurace neexistuje, GUI při spuštění použije aktuální pracovní adresář a jazyk odvodí z lokálního nastavení systému; konfiguraci nevytváří automaticky. Volbou adresáře a jazyka v GUI se hodnoty uloží. Podporované jazyky GUI jsou `cs` a `en`; volba se projeví ihned.

Fronta, zámky, heartbeat workeru, checkpointy a výchozí překladové artefakty se odvozují od nastaveného `workdir`. Cesty zadané explicitně v jobu zůstávají absolutní. Změna workdir je povolena pouze po zastavení workeru, aby nemohly současně běžet dvě různé pracovní fronty.

## Ovládání

### Průběh aktuálního jobu

Průběh je diagnostický runtime údaj v `worker-state.json`; nezapisuje se při
každé změně do `queue.json`, takže neprodlužuje kritickou cestu zápisu fronty.
Worker aktualizuje hodnoty po dokončeném HTML checkpointu nebo po dokončené
straně při sazbě PDF. Heartbeat je dál obnovuje během dlouhého AI požadavku.
GUI je čte při pravidelném pollu a zobrazuje je ve stavové liště progress barem;
CLI je uvádí v `status`.

Aktuální implementovaný kontrakt:

~~~json
{
  "job_id": "job-a1b2c3",
  "activity": "translating",
  "phase": "html",
  "progress": 0.42,
  "completed": 210,
  "total": 493,
  "unit": "pages",
  "current_page": 211
}
~~~

`progress` je číslo v intervalu `0..1`, `completed` a `total` jsou celočíselné
hodnoty stejné jednotky. Pro překlad HTML i sazbu PDF je jednotkou stránka.
Během přípravy, kdy celkový počet ještě není znám, GUI ponechá bar
na nule a zobrazí pouze aktuální činnost. Po ukončení workeru se runtime soubor
odstraní; trvalý stav jobu zůstává ve frontě.

Volitelné pole preview ve stejném runtime snapshotu obsahuje poslední dávkový
náhled aktuálního bloku. Worker jej zapisuje před AI požadavkem jako
translating a po validovaném výsledku jako translated; při chybě může obsahovat
error. Náhled je omezen na 100 řádků a 12000 znaků, GUI jej zobrazuje readonly
se scrollbarem a nezapisuje se do fronty, cache ani event logu. Nejde o tokenové
streamování; aktualizace probíhá pouze na hranici dávky. Detailní UML kontrakt
je v [tasku náhledu](../tasks/3-2026-10-11-gui-nahled-aktualniho-bloku.md).
Běžné zápisy preview jsou navíc throttlované na nejvýše jeden zápis za 10 s.
První preview nového jobu a terminální stav translated/error/stopped se zapíší
ihned, aby se nezhoršila odezva ani diagnostika.

~~~mermaid
classDiagram
    class WorkerRuntimeState {
        +str job_id
        +str activity
        +str phase
        +float progress
        +int completed
        +int total
        +str unit
        +int current_page
    }

    class QueueWorker {
        +report_progress(completed, total, unit, current_page)
        +write_state()
    }

    class TranslationCore {
        <<callback boundary>>
        +report_progress(completed, total, unit, current_page)
    }

    class QueueGui {
        +render()
        +progress_bar
    }

    QueueWorker --> WorkerRuntimeState : atomicky zapisuje
    TranslationCore --> QueueWorker : progress callback
    QueueGui --> WorkerRuntimeState : polluje
~~~

~~~mermaid
sequenceDiagram
    participant Worker
    participant Translate as překladové jádro
    participant State as worker-state.json
    participant GUI
    participant CLI

    Worker->>Translate: spustí fázi s progress callbackem
    Translate->>Translate: dokončí checkpoint HTML nebo stránku PDF
    Translate->>Worker: completed / total / unit
    Worker->>State: atomicky zapíše snapshot
    loop pravidelný poll
        GUI->>State: načte snapshot
        State-->>GUI: progress, aktivita, fáze
        GUI->>GUI: aktualizuje progress bar a stavový text
    end
    CLI->>State: načte snapshot při status
    State-->>CLI: progress a aktivita
    alt dlouhý AI požadavek
        Worker->>State: heartbeat bez změny průběhu
    end
~~~

Tento kontrakt odděluje překladové jádro od fronty: jádro pouze volá volitelný
callback a při samostatném použití nemusí znát GUI, CLI ani JSON frontu.

Bez parametrů se otevře GUI:

~~~bat
translate.cmd
~~~

GUI se spouští přes `pythonw` na pozadí; launcher se po předání požadavku ukončí a jeho konzolové okno se zavře. CLI a překladové příkazy používají běžný `python`, aby zůstal dostupný průběh a diagnostika.

GUI zobrazuje první speciální řádek s globálním příkazem STOP WORKER, pod ním joby v pořadí fronty a sloupec stavu. Sekce ovládání jsou uspořádané svisle; stav workeru, revize a neodeslané změny jsou ve stavové liště pod seznamem jobů. Ovládací prvky jsou rozdělené podle účelu:

- Worker: `Start` spustí nebo obnoví worker, `Update` zapíše změny a worker nastartuje, `Stop` zastaví worker; během překladu se pokusí okamžitě zrušit AI požadavek.
- Job: Add otevře přímo ve skupině Job lokální formulář nového jobu. Detail vybraného jobu je jinak readonly. Pause, Prepare, Delete, Up a Down pracují pouze s potvrzenými údaji fronty.
- Job detail: obsahuje vstupní PDF, výstupní PDF, XHTML/HTML, fázi, provider, profil a model. V režimu Add jsou pole editovatelná a zobrazí se OK a Cancel. OK pouze přidá validovaný job do lokálního draftu GUI; Cancel změny zahodí.
- Automatické názvy: po výběru vstupního PDF GUI doplní prázdné HTML a PDF pole normalizovanými názvy. Ručně změněné hodnoty nepřepisuje. Vstupní cesty může uživatel zadat s libovolnými platnými znaky; pouze automatické návrhy se normalizují.
- Fáze a HTML: interní hodnoty jobu zůstávají `both/html/pdf`, ale GUI je zobrazuje formátově neutrálně jako `in -> html -> out`, `in -> html` a `html -> out`. Tím není ovládání svázané s konkrétním vstupním nebo výstupním formátem. Pole pro přeložené HTML lze při fázi `html -> out` vybrat tlačítkem; pokud cesta není zadána, worker hledá kompletní HTML podle SHA-256 vstupního souboru a jazykových metadat ve složce vstupu/výstupu.
- Výběr modelu: combobox v sekci Job načítá lokálně dostupné modely z Ollama `/api/tags` mimo Tk vlákno a rozlišuje available/empty/offline/invalid; při nedostupné Ollamě ponechá výchozí nebo již uložený model.
- Capability provideru: Ollama používá pouze výběr modelu; profil a konfigurace se u ní nezobrazují. OpenAI, Gemini a Claude mohou mít uložený profil a provider-specific konfiguraci; Gemini navíc podporuje browser login.
- Obecné: volba jazyka a `Refresh`, který znovu načte frontu.
- Pracovní adresář: `Browse` vybere adresář a `Save` ho uloží do konfigurace.
- Volba jazyka `cs` nebo `en` mění všechny popisky GUI ihned a uloží nastavení.

Workdir se zobrazuje pouze ve skupině Pracovní adresář. Neodeslané změny zahrnují i otevřený formulář Add a jsou označeny ve stavovém řádku, který zobrazuje stav workeru, revizi fronty a aktuální aktivitu/fázi. Worker obnovuje heartbeat i během dlouhého volání AI, takže GUI rozliší běžící práci od ukončeného procesu. OK potvrzuje formulář do lokálního draftu; Update jobs je jediný okamžik zápisu potvrzeného draftu workeru. Start pouze spouští worker. Při zavření nebo refreshi se GUI zeptá, zda zahodit otevřený formulář nebo neodeslané změny.

~~~mermaid
classDiagram
    class QueueGui {
        +begin Add
        +commit_job_form()
        +cancel_job_form()
        +send()
    }

    class JobFormSession {
        +bool editing
        +input
        +output
        +html
        +phase
        +validate()
        +commit()
        +cancel()
    }

    class QueueDraft {
        +JobItem[] jobs
        +bool dirty
    }

    QueueGui --> JobFormSession : edits
    JobFormSession --> QueueDraft : OK appends
    QueueGui --> QueueDraft : Update jobs publishes
~~~

~~~mermaid
sequenceDiagram
    actor User
    participant GUI as Queue GUI
    participant Form as Job form
    participant Draft as local queue draft
    participant Queue as queue.json
    participant Worker

    User->>GUI: Add
    GUI->>Form: clear fields and enable editing
    User->>GUI: select input PDF
    GUI->>Form: fill empty normalized HTML/PDF suggestions
    User->>GUI: edit paths, phase or provider settings
    alt OK
        GUI->>Form: validate all fields
        Form-->>GUI: valid job
        GUI->>Draft: append job; mark unsent
    else Cancel
        GUI->>Form: discard fields
        GUI->>GUI: restore selected job details
    end
    User->>GUI: Update jobs
    GUI->>Queue: atomically publish draft
    GUI->>Worker: start if needed
~~~

CLI:

~~~bat
translate.cmd add "book.pdf" --outfile "book-cs-layout.pdf" --model "translategemma:12b"
translate.cmd start
translate.cmd pause job-a1b2c3
translate.cmd stop
translate.cmd status
translate.cmd status --json
~~~

`add` uloží job a automaticky spustí worker. `start` pouze spustí nebo obnoví worker; výběr práce řídí fronta. `pause` je zápis stavu; worker ho během překladu rozpozná průběžně a při sazbě ho uplatní na bezpečné hranici. `stop` se týká workeru jako celku a během AI překladu se pokusí zrušit aktuální požadavek.

## Překladový běh, logování a výjimky

~~~mermaid
sequenceDiagram
    actor User
    participant Runner as translate.cmd
    participant Legacy as doctranslate.translate
    participant Cache as plan/cache
    participant Log as run.log

    User->>Runner: command + options
    Runner->>Legacy: translate.cmd
    Legacy->>Log: configured, phase, model
    Legacy->>Cache: načte nebo uloží checkpoint
    Legacy->>Log: batch timing a cache decision
    Legacy->>Log: completion
    alt výjimka
        Legacy->>Log: exception + traceback
        Legacy->>User: exit code a cesta k run-error.json
    end
~~~

Log je implicitně vedle výstupu jako *.run.log. Parametr -trace přidává podrobné JSONL události včetně fází, dávky, bloků, trvání, cache a výjimek. Stejný stabilní event kontrakt používá fronta, GUI, CLI a worker v workdir/queue.events.log; každý záznam má time_utc, event a kontextová pole. worker.log zůstává surovým záznamem stdout/stderr pro chyby spuštění subprocessu. Logování je best-effort a nesmí skrýt původní chybu při plném nebo readonly disku. Chyby uvnitř překladových/sazebních fází se ukládají také do *.run-error.json. Chyby před main(), například nenalezené HTML, se zapíšou do diagnostiky i do fallback run logu, pokud je známý výstup; viz bootstrap issue.

## Aktuální stav a restart

### Modularizované AI a formátové hranice

Implementované moduly v src/doctranslate nyní poskytují:

- kanonický XHTML codec s metadaty, resources a atomickým uložením;
- oddělené input/output format registry a PDF resource/hash validaci;
- obecný textový a segmentový AI kontrakt;
- Ollama, OpenAI API, Gemini API a Claude API backendy s jednotným chybovým kontraktem;
- verzované AI profily, API-key/env/keyring hranici a Gemini loopback OAuth;
- restartovatelný JobRunner s cache identity a checkpointy;
- provider/profile/model volby v CLI, workeru a GUI.

Produkční PDF překlad zůstává zpětně kompatibilní přes legacy bridge; cílové adaptéry jsou veřejná hranice pro další migraci sazebních heuristik. Offline stav a limity ověření jsou v modularization-analysis.md.

### Pravidla názvů souborů

- Vstupní cesty a uživatelem explicitně zadané výstupní cesty se používají beze změny; program musí zvládnout i mezery, diakritiku a další platné znaky systému.
- Název vytvořený z přeloženého názvu dokumentu se před uložením normalizuje. Automaticky vytvořené soubory (výchozí výstup, HTML, plán, cache, logy a diagnostické soubory) odstraní diakritiku, ponechají mezery a spojovníky a odstraní ostatní nejednoznačné znaky.
- Příklad češtiny: Lucio Russo – Zapomenutá revoluce.pdf se uloží jako Lucio Russo - Zapomenuta revoluce.pdf.
- Příklad němčiny: Lucio Russo – Die vergessene Revolution.pdf se uloží jako Lucio Russo - Die vergessene Revolution.pdf.
- Existující starší sidecary s původním názvem zůstávají kvůli obnově práce čitelné; nové soubory používají normalizovaný název.

### Výkon PDF sazby

Původní sazba zapisovala celý rostoucí PDF dokument po každé stránce a při každém zápisu prováděla kompresi a garbage collection. Pro 493stránkový dokument to znamenalo stovky úplných přepisů výstupu.

Aktuální režim adaptive:

- při dostatečné rezervě RAM drží pracovní PDF v paměti a provede jeden optimalizovaný zápis na konci;
- při nízké rezervě přejde na rychlé checkpointy po PDF_CHECKPOINT_PAGES stranách;
- checkpointy se zapisují bez nákladné optimalizace; finální zápis používá garbage=4 a deflate=True;
- při přerušení zůstává v JSON plánu poslední skutečně uložený checkpoint.

Režim lze vynutit přes --pdf-save-mode memory|checkpoint|adaptive a interval přes --pdf-checkpoint-pages N. Pro měření použijte připravený runner:

    python tools/performance_benchmark.py --infile source.pdf --htmlfile translated.html --outfile benchmark-memory.pdf --mode memory

Pro srovnání checkpointů použijte jiný výstupní soubor a --mode checkpoint --checkpoint-pages 1 nebo vyšší interval. Runner vyžaduje kompletní HTML, Ollamu ani síť nepoužívá a vytvoří .performance.json a .performance.md.

Statická diagnostika referenčního běhu zjistila 493 stran, přibližně 5 803 textových bloků a přibližně 104,7 GB volné RAM. Vizuální sazba referenčního dokumentu ani dlouhý benchmark nebyly v této revizi spuštěny.

### Výkon PDF sazby

Původní sazba zapisovala celý rostoucí PDF dokument po každé stránce a při každém zápisu prováděla kompresi a garbage collection. Pro 493stránkový dokument to znamenalo stovky úplných přepisů výstupu.

Aktuální režim adaptive:

- při dostatečné rezervě RAM drží pracovní PDF v paměti a provede jeden optimalizovaný zápis na konci;
- při nízké rezervě přejde na rychlé checkpointy po PDF_CHECKPOINT_PAGES stranách;
- checkpointy se zapisují bez nákladné optimalizace; finální zápis používá garbage=4 a deflate=True;
- při přerušení zůstává v JSON plánu poslední skutečně uložený checkpoint.

Režim lze vynutit přes --pdf-save-mode memory|checkpoint|adaptive a interval přes --pdf-checkpoint-pages N. Pro měření použijte připravený runner:

    python tools/performance_benchmark.py --infile source.pdf --htmlfile translated.html --outfile benchmark-memory.pdf --mode memory

Pro srovnání checkpointů použijte jiný výstupní soubor a --mode checkpoint --checkpoint-pages 1 nebo vyšší interval. Runner vyžaduje kompletní HTML, Ollamu ani síť nepoužívá a vytvoří .performance.json a .performance.md.

Statická diagnostika referenčního běhu zjistila 493 stran, přibližně 5 803 textových bloků a přibližně 104,7 GB volné RAM. Vizuální sazba referenčního dokumentu ani dlouhý benchmark nebyly v této revizi spuštěny.

- Pracovní kopie: C:/Users/mordacik/Documents/Codex/doctranslate.
- Zdrojový balíček: src/doctranslate/; jediný uživatelský launcher je translate.cmd.
- Projektová dokumentace je v doc/; trvalá testovací data jsou v test/mock/; tmp/ obsahuje pouze lokální pracovní artefakty. Runtime fronta a výchozí výstupy jsou v nastaveném workdir.
- Klasifikace JSON artefaktů a návrh úklidu jsou v doc/cleanup-candidates.md.
- Lokální Git má historii; při revizi HEAD 70d9fd9 (2026-10-10, AI doc translation). V rámci revize nebyl proveden commit ani push; vzdálený stav se neověřoval.
- Přidány src/doctranslate/, queue frontend/worker, testy, runner a dokumentace.
- Starší Qwen delegace selhávaly na Continue serveru. Revize znovu potvrdila read calibration exit1 bez tool callů; nontriviální kódové úpravy nyní zůstávají odložené podle supervisor policy.
- Revize 2026-10-10: offline suite nyní prochází 51 testy včetně subprocess regresí pro worker, souběžnou obnovu stale locku, storage fault injection, bootstrap bez PDF engine, Ollama discovery a JSONL observability. Ollama, modely a vizuální PDF kontrola zůstávají neověřené; podrobná evidence a meze testování jsou v `review-2026-10-10.md`.

### Doporučené další kroky

1. Vyřešit P1 bezpečné ověření PID na Windows a P2 start/importy workeru.
2. Dokončeno: lock, konflikty fronty, životní cyklus workeru, zápisové chyby a bootstrap jsou pokryté offline regresemi.
3. Dokončeno: jednotné CLI chyby, dependency preflight a offline fake-backend test jsou implementované.
4. Ujasnit víceuzlový text/markup kontrakt; teprve potom postupně připojovat pluginy a immutable JobContext.
5. Vizuální PDF regresi a delší ručně hodnocený benchmark TranslateGemma provést samostatně; aktuální sazbu PDF spouští uživatel.
6. Commit/push pouze po výslovném rozhodnutí.

## Provozní poznámky nástrojů

Kuchařku ověřených postupů a workaroundů vede [doc/tools.md](tools.md). Projektový [AGENTS.md](../AGENTS.md) vyžaduje načtení tohoto souboru na začátku každé práce.
