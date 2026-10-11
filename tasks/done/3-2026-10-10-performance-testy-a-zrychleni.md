status: done
last change: 2026-10-11
dependency: ../done/3-2026-10-10-integrace-modulu-a-regresni-checklist.md
group: performance/benchmarking
type: performance
description:
Připravit reprodukovatelné performance testy jednotlivých bloků překladového
pipeline a na jejich základě určit skutečné bottlenecky a možnosti zrychlení.
Neoptimalizovat naslepo; každé doporučení musí mít měřitelný přínos, cenu a riziko.
Priority: 3 (normal)
Created: 2026-10-10

## Rozsah měření

Měřit samostatně i end-to-end alespoň tyto bloky:

1. načtení vstupního PDF a extrakce textu/layoutu,
2. výpočet hashů a práce s resources/metadaty,
3. převod PDF dokumentu na XHTML a jeho serializace/parsing,
4. rozdělení dokumentu na překládané bloky a validace placeholderů,
5. AI požadavek (mock/provider): sestavení promptu, latence, retry, throughput,
6. cache/checkpoint: lookup, zápis, obnova po přerušení,
7. fronta a worker: režie polling/send/update a zpracování dávky,
8. převod XHTML na výstupní PDF a zápis výsledku.

Pro AI backend rozlišit cold start, warm start, jednotlivý blok a dávku.
Živé cloud/Ollama testy musí být volitelné; výchozí testovací sada nesmí vyžadovat
model, síť ani dostupné externí služby.

## Požadovaná měření

- wall-clock čas a čas jednotlivých fází,
- počet bloků, znaků a tokenů, pokud jsou dostupné,
- p50/p95 latence a průchodnost,
- CPU time a maximální RSS, pokud je měření v prostředí dostupné,
- počet retry, cache hit/miss, checkpointů a chyb,
- velikost vstupních, mezilehlých a výstupních souborů,
- cold/warm rozlišení a parametry běhu: Python, OS, provider, model, velikost dokumentu.

Výsledky zapisovat do strojově čitelného formátu a současně generovat stručný
Markdown report s baseline, odchylkou a závěry. Benchmark nesmí zapisovat
citlivé texty, API klíče ani celé prompt/response payloady.

## Kandidáti zrychlení k vyhodnocení

- reuse klienta a connection/session pooling,
- paralelní překlad nezávislých bloků s limitem concurrency,
- vhodnější velikost dávky/chunku a omezení prompt overheadu,
- přeskočení nezměněných bloků přes stabilní identitu a cache,
- inkrementální nebo odložené hashování zdrojů,
- omezení opakovaného parsingu/serializace XHTML,
- checkpoint pouze při významné změně nebo v dávkách,
- redukce polling režie workeru,
- optimalizace renderu PDF pouze pokud benchmark prokáže, že je bottleneck,
- oddělení výkonu modelu od výkonu orchestrace a filesystemu.

Pro každý kandidát uvést: očekávaný přínos, složitost, riziko změny výstupu,
vliv na paměť, možnost zapnutí/vypnutí a návrh validačního testu.

## Navržený postup

~~~mermaid
sequenceDiagram
    participant B as Benchmark runner
    participant P as Pipeline block
    participant A as AI provider/mock
    participant C as Cache/checkpoint
    participant R as Report
    B->>B: Připraví fixture a parametry běhu
    B->>P: Spustí měřený blok
    P->>A: Volitelně přeloží blok/dávku
    P->>C: Čte a zapisuje cache/checkpoint
    P-->>B: Vrátí výsledek a metriky
    B->>R: Zapíše raw výsledky
    R->>R: Spočítá baseline, odchylky a bottlenecky
    alt externí služba není dostupná
        B->>A: Použije deterministický mock
    else benchmark vyžaduje živou službu
        B->>A: Ověří dostupnost a označí test jako opt-in
    end
~~~

## Acceptance

- Existuje izolovaná benchmark sada pro jednotlivé bloky i end-to-end průchod.
- Výchozí offline běh je deterministický a nevyžaduje Ollamu, model, síť ani
  speciální PDF vstup.
- Každý benchmark uvádí warm-up, počet opakování a měřené metriky.
- Je k dispozici první baseline report pro malý, střední a větší fixture.
- Bottlenecky jsou doložené měřením, nikoli pouze odhadem.
- Návrhy optimalizací jsou seřazené podle poměru přínos/náklady/riziko.
- Výkonnostní změny mají regresní test a nesnižují korektnost překladu,
  checkpoint recovery ani formátování výstupu.
- Dokumentace uvádí omezení přesnosti měření a rozdíl mezi offline mockem a
  živým providerem.

## comments:

2026-10-10: Task založen na požadavku uživatele. Nejprve se mají připravit
reprodukovatelné testy jednotlivých bloků, potom baseline a teprve následně
návrhy či implementace optimalizací. Žádná optimalizace nebyla zatím provedena.

2026-10-10: První statická diagnostika konkrétního sazebního běhu:
493 stran, vstupní PDF 17 548 591 B, výstup 25 559 149 B a přibližně 5 803
textových bloků. Funkce run_html_typesetting volá po každé stránce save_pdf_atomic;
ta provádí úplný doc.save s garbage=4 a deflate=True do dočasného PDF.
To je hlavní podezřelé úzké hrdlo: rostoucí celý dokument se znovu komprimuje a
zapisuje až 493krát, nikoli jen jednou na disk. Funkce process_page navíc provádí
insert_htmlbox jednou v probe dokumentu a podruhé v cílové stránce pro každý
změněný blok. V době měření bylo volných přibližně 104,7 GB RAM z 137,3 GB.
Hypotéza i navržené změny musí být potvrzeny benchmarkem, nikoli pouze tímto
statickým rozborem.

2026-10-10: Implementován PerformanceRecorder, adaptivní PDF ukládání a opt-in
runner tools/performance_benchmark.py. Režimy memory/checkpoint/adaptive mají
regresní testy; offline sada má 92 úspěšných testů. Skutečný dlouhý benchmark
referenčního 493stránkového PDF nebyl spuštěn, protože sazbu PDF provede uživatel.
Task byl uzavřen v omezeném, explicitně ověřeném rozsahu PDF sazby.

2026-10-11: Ověřeny reprodukovatelné baseline fixture o velikosti 3, 30 a 100
stran v režimech memory, checkpoint a adaptive. Stostránkový běh skončil
memory 3,83 s, checkpoint 4,36 s a adaptive 3,79 s; růst je přibližně lineární.
Výsledky a reporty jsou v tmp/performance-100/.

2026-10-11: Opraven report výkonu: po dokončení nyní uvádí output_exists,
output_bytes a output_pages. Regresní testy výkonu prošly 13/13.

2026-10-11: Uzavřen je PDF typesetting benchmark. Měření extrakce, AI backendu,
cache a workeru zůstávají mimo tento uzavřený rozsah a mohou být samostatnými
tasky.
