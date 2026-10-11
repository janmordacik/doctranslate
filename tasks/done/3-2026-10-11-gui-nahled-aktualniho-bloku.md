status: done
last change: 2026-10-11
dependency: none
group: gui/worker/observability
type: feature
description: Zobrazit v GUI dávkový náhled aktuálního překládaného bloku
Priority: 3 (normal)
Created: 2026-10-11

## Cíl

Umožnit uživateli průběžně kontrolovat kvalitu překladu během dlouhého běhu.
Náhled se obnovuje pouze na bezpečných hranicích dokončených překladových
dávek; neimplementuje tokenové streamování a nezasahuje do AI transportu.

## Chování

- Před zahájením dávky worker zveřejní začátek zdrojového textu aktuálního
  bloku.
- Po dokončení a validaci dávky zveřejní začátek přeloženého textu posledního
  dokončeného bloku.
- GUI zobrazí náhled pod seznamem jobů v readonly textové oblasti vysoké
  přibližně 10 řádků se svislým scrollbar-em.
- Runtime snapshot může obsahovat až 100 řádků náhledu; delší text se zkrátí
  podle explicitního limitu znaků a řádků.
- Náhled se zobrazí spolu s identifikací jobu, stránky/bloku, fází a stavem
  source, translating, translated nebo error.
- Při Stop, chybě nebo ukončení workeru GUI zobrazí poslední dostupný stav a
  po odstranění worker-state.json náhled vyčistí.
- Náhled se nezapisuje do queue.json, překladové cache ani event logu a nikdy
  se nepoužije jako vstup pro další překlad.

## Kontrakt runtime stavu

Rozšířit worker-state.json volitelným polem:

~~~json
{
  "preview": {
    "job_id": "job-a1b2c3",
    "block_id": "p000241_b0003",
    "page": 241,
    "stage": "translated",
    "source_text": "Beginning of source block...",
    "translated_text": "Začátek přeloženého bloku...",
    "line_count": 10,
    "truncated": false
  }
}
~~~

Pole musí být zpětně kompatibilní: GUI bez preview pracuje stejně jako dosud
a worker toleruje starší GUI.

~~~mermaid
classDiagram
    class WorkerRuntimeState {
        +str job_id
        +str activity
        +float progress
        +PreviewSnapshot preview
    }

    class PreviewSnapshot {
        +str job_id
        +str block_id
        +int page
        +str stage
        +str source_text
        +str translated_text
        +int line_count
        +bool truncated
    }

    class QueueWorker {
        +publish_preview(snapshot)
        +write_state()
    }

    class QueueGui {
        +render_preview(snapshot)
        +clear_preview()
    }

    WorkerRuntimeState *-- PreviewSnapshot
    QueueWorker --> WorkerRuntimeState : atomicky zapisuje
    QueueGui --> WorkerRuntimeState : polluje
~~~

~~~mermaid
sequenceDiagram
    participant Worker
    participant Translate as překladové jádro
    participant State as worker-state.json
    participant GUI

    Worker->>Translate: připraví překladovou dávku
    Translate-->>Worker: zdrojový začátek aktuálního bloku
    Worker->>State: zapíše preview.stage=translating
    loop GUI polling
        GUI->>State: načte snapshot
        State-->>GUI: zdrojový náhled a metadata
    end
    Translate-->>Worker: validovaný překlad dávky
    Worker->>State: zapíše poslední dokončený blok a překlad
    GUI->>State: načte nový snapshot
    State-->>GUI: translated preview
    alt stop nebo chyba
        Worker->>State: zapíše stav stop/error
        GUI->>GUI: zobrazí poslední náhled a stav
    end
~~~

## Výkon a limity

- Aktualizovat pouze při zahájení dávky, po validovaném výsledku a při chybě;
  ne při každém tokenu ani v každém GUI pollu.
- Běžné průběžné aktualizace omezit na nejvýše jednu za 10 sekund; první
  náhled nového jobu a terminální stav translated/error/stopped zveřejnit ihned.
- Snapshot zůstává poslední stavový soubor; nevytvářet historické preview
  soubory ani JSONL události s celým textem.
- Omezit náhled na nejvýše 100 řádků a stanovený maximální počet znaků.
- Serializace a zápis náhledu nesmí prodloužit kritickou cestu AI požadavku.
- PDF sazba může zobrazovat obdobný náhled aktuální stránky, pokud to lze
  využít bez dalšího formátového kontraktu; překladový náhled je minimum.

## Testy

- Unit test oříznutí na 100 řádků/limit znaků a zachování Unicode.
- Unit test atomického zápisu a načtení preview ve worker-state.json.
- Worker test: preview se objeví před dávkou a změní na translated až po
  validním výsledku; neplatný výsledek nesmí přepsat poslední validní překlad.
- GUI test: chybějící nebo starý snapshot nevyvolá výjimku, scrollbar a
  readonly režim zůstanou funkční.
- Regrese stávající fronty a progress baru.

## Acceptance

- Uživatel vidí první překládané bloky během zpracování dlouhého jobu, aniž
  by čekal na dokončení celého dokumentu.
- Náhled se obnovuje pouze na hranici dávky a nemění uložený překlad.
- Po Stop nebo chybě zůstane vidět poslední dostupný náhled a srozumitelný stav.
- Výkon běžného překladu se měřením nezhorší významně; nezavádí se streaming.
- Aktualizovat doc/technical-overview.md a autoritativní Mermaid diagramy, pokud se
  změní runtime kontrakt.

## comments

2026-10-11: Task vytvořen na základě požadavku uživatele. Bez tokenového
streamování; náhled je dávkový, diagnostický a zapisuje se pouze do aktuálního
worker-state snapshotu.
2026-10-11: Implementováno v translate.py, queue_worker.py a queue_app.py.
Náhled se zveřejňuje na hranici dávky, omezuje se na 100 řádků/12000 znaků,
GUI jej zobrazuje v readonly textové oblasti se scrollbarem a stav se ukládá
pouze do worker-state.json. Cílené testy prošly 50/50 a úplná sada 115/115.
2026-10-11: Přidán throttling běžných preview update na 10 s; první preview,
nový job a terminální stavy se nezpožďují. Přidán regresní test.

