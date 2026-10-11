status: test
last change: 2026-10-11
dependency: none
group: architecture/translation-engine
type: documentation
estimate:
  time: 90–180 min návrhu a revize; samostatný implementační odhad je v parent issue P01–P18
  logical_lines: 305–515 řádků dokumentace a kontraktních příkladů; 0 produkčních změn
  tokens: 10k–18k orientační pracovní rozsah
  subtasks: A01, A02, A02b, A03a, A03b, A04, A05
description: Navrhnout pokročilý překladový modul s jednoduchým veřejným rozhraním pro vstupní a výstupní adaptéry a sjednotit stávající překladové kontrakty.

## Zadání a rozsah

Výsledkem tasku je implementovatelný návrh, nikoli implementace modulu.
Překladové jádro přijímá kanonický XHTML dokument s metadaty a vrací přeložený
XHTML dokument. Vstupní adaptér převádí soubor na tento dokument; výstupní
adaptér jej formátuje a zapisuje. Výběr souborových formátů a práce s frontou
zůstávají v orchestrátoru. AI služby se připojují přes providerový kontrakt.

Pokročilé funkce mají být skryté za malým rozhraním: dávkování podle limitů
modelu, kontext, stylové profily, validace textu a inline markup, retry, cache,
checkpointy, obnovení, zrušení požadavku, průběh a měření výkonu.
Rozlišit povinné schopnosti první verze a volitelné rozšiřující strategie.
Nevytvářet vlastní framework ani další paralelní překladový kontrakt.

## Ověřený výchozí stav

- translate_core/adapters.py: DocumentInputAdapter.read(Path) -> XhtmlDocument
  a DocumentOutputAdapter.write(XhtmlDocument, Path) -> Path.
- translate_core/pipeline.py: TranslationPipeline.translate(XhtmlDocument),
  samostatný TranslationBackend a MarkupTranslation.
- ai/contracts.py: AiBackend, SegmentRequest a SegmentResult.
- ai/translation.py: SegmentTranslationPipeline, validace, retry a cancel checks.
- job_runner.py: JobRunner.run používá SegmentTranslationPipeline;
  existenci této cesty nezaměňovat za důkaz, že ji používají všechny joby.
- translate.py a queue_worker.py obsahují produkční orchestrace; jejich skutečné
  volací cesty jsou nově zmapované v A19/A01; worker stále používá legacy tok.

Statický nález pro návrh: JobRunner ukládá nové překlady do checkpointu, ale
do dokumentu před výstupem aplikuje pouze dříve obnovené hodnoty. Použití
block.translated(text) navíc samo nesynchronizuje markup. Statická revize
potvrdila chybějící kontrolu prvního výstupu v testu JobRunner; reprodukce
a oprava jsou oddělené v P01, nikoli implementované v tomto návrhu.

Minimální kontext: uvedené zdroje, projektový AGENTS.md, doc/tools.md,
doc/modularization-analysis.md (A03, A06, A09, A13, A18, A19) a příslušné testy v test/.

## Navržená veřejná hranice k posouzení

~~~python
class TranslationEngine(Protocol):
    def translate(
        self,
        document: XhtmlDocument,
        options: TranslationOptions,
        *,
        context: TranslationContext | None = None,
    ) -> TranslationResult: ...
~~~

TranslationOptions: zdrojový a cílový jazyk, styl a překladová politika.
TranslationContext: volitelné rušení, progress a checkpoint/cache služby.
TranslationResult: výsledný dokument a stručné statistiky; metadata formátu
nesmějí zmizet. První přesné typy a hranici konfigurace provideru stanoví A19/A02.
Provider předat při sestavení engine; credentials a provider options řeší
existující providerová konfigurace. Adaptéry nepotřebují přístup k AI konfiguraci.

Použití: input.read(path) -> engine.translate(document, options)
-> output.write(result.document, target). XHTML lze načíst také přímo codecem.
Výstup z již přeloženého XHTML musí fungovat bez sestavení AI backendu.

## Plán přezkoumatelných podúloh

| ID | Výsledek a ověření | Čas | Logické řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| A01 | Mapa skutečných volacích cest a rozdílů kontraktů; tvrzení doložená symboly a testy | 10–20 min | 25–45 | 1k–2k | none |
| A02 | Jediný veřejný kontrakt, typy, invarianty a krátký příklad propojení adapterů; review všech vstupů a výsledků | 15–30 min | 45–80 | 2k–3k | A01 |
| A02b | Volba basic/advanced v jobu, registr dostupnosti, GUI/CLI a migrace starších jobů; scénáře smíšené fronty, nedostupnosti a resume | 10–20 min | 35–60 | 1k–2k | A02 |
| A03a | Sémantické dávky, kontext a paměť: schéma glosáře, vyhledávání, konflikty a invalidace; scénáře více významů a obnovy | 20–40 min | 70–120 | 2k–4k | A02 |
| A03b | Standardní/rozšířený režim, nástrojové smlouvy, validace, limity, rušení a výkonový experiment; kontrola terminálních stavů | 15–30 min | 60–100 | 2k–3k | A03a |
| A04 | Zpřesnění class/sequence diagramů a procesního indexu v A18 podle výsledných kontraktů; kontrola Mermaid | 10–20 min | 40–60 | 1k–2k | A02b, A03a, A03b |
| A05 | Migrace a testovací plán včetně paměti, limitů, provider capabilities a EN→CS benchmarku; pokrytí kritérií | 10–20 min | 30–50 | 1k–2k | A04 |

Odhady jsou čistá práce včetně review; řádky jsou dokumentace, ne odhad
budoucí implementace. Podúlohy dělit podle rozhodnutí a chování.
Implementační tasky po návrhu odhadnout zvlášť a zachovat sémantickou atomicitu.

## Zadání dlouhých dokumentů a paměti

Autoritativní požadavky, cílová struktura a procesy jsou v
[analýze A18](../doc/modularization-analysis.md#a18-pokročilý-překlad-dlouhých-textů--zadání-a-cílový-návrh).

- Převážně unikátní knihy/odborné texty řádově 1000 stran, prioritně EN→CS.
  Jedna GPU 6–32 GB VRAM, model cca 27B a nejvýše 128k modelového kontextu;
  skutečnou dosažitelnost určit podle modelu, kvantizace a KV cache.
- Malý veřejný kontrakt nad XHTML; žádná znalost PDF, GUI nebo fronty v engine.
  Provider a externí paměť jsou vyměnitelné interní služby.
- Volba modulu je per-job: basic (současný algoritmus) a advanced (návrh),
  přes stejný kontrakt a registr. Oddělit ji od provideru/modelu a od režimů
  uvnitř advanced. GUI kombo a CLI --translator, konkrétní ID uložit do JSON.
  Starší job bez ID znamená basic; kopie jobu volbu zachová. Nedostupný modul
  nesmí způsobit tichý fallback ani znemožnit basic překlad ostatních jobů.
- Standardní tok: sémantické dávky, omezené okolí, relevantní sub-glosář,
  deterministická validace a cílené opravy. Nepotřebuje tool calling.
- Rozšířený tok: model smí vyhledávat kontext, navrhovat termíny a žádat revizi;
  program spravuje nástroje a konečné rozpočty. Žádný neomezený konsenzus.
- Paměť může být větší než kontext. První varianta JSON + RAM index,
  přesné/aliasové a lexikální hledání; omezené výsledky i tokeny.
  Vektorová DB, GraphRAG a agentní framework nejsou podmínkou.
- Definovat lookup_terms, search_memory, get_occurrences, get_source,
  propose_term a request_revision; důkazy ze zdroje, význam/scope,
  konflikty, idempotenci, atomický zápis a revize ověřuje program.
- Modelové návrhy a potvrzená rozhodnutí se rozlišují. Konflikt nesmí tiše
  změnit glosář; změna termínu musí mít dohledatelné dotčené segmenty.
- Okolí je pouze kontext, překládají se označené segmenty se stabilními IDs.
  Shrnutí je volitelné a nespolehlivé pomocné vodítko, nikoli náhrada originálu.
- Deduplikace/fuzzy reuse celých odstavců není hlavní výkonová strategie:
  uživatel neočekává takto redundantní dokumenty. Cache je hlavně pro obnovu.
- Vyhodnotit režii proti baseline na unikátních vzorcích; měřit AI/tool volání,
  tokeny, přípravu, generování, opravy, I/O a kvalitu včetně času na opravy.
  Číselné scénáře v A18 jsou hypotézy, nikoli naměřené závazky.

## UML a procesní pokrytí návrhu

Diagramy udržovat pouze v autoritativní analýze A18/A19, neduplikovat v issue.

| Návrhový výstup | Odkaz |
|---|---|
| Struktura, komponenty a závislosti | [Class diagram](../doc/modularization-analysis.md#cílová-struktura-enginu) |
| Překlad, render-only, rušení, chyba a obnova | [T01](../doc/modularization-analysis.md#t01-preklad-a-obnova) |
| Dotazy, zápis a konflikty paměti | [T02](../doc/modularization-analysis.md#t02-prace-s-pameti) |
| Omezené AI/nástrojové kroky a revize | [T03](../doc/modularization-analysis.md#t03-agentni-relace) |
| Volba modulu v jobu a ověření dostupnosti | [T04](../doc/modularization-analysis.md#t04-volba-prekladoveho-modulu) |
| Kontrakty, provider porty a legacy migrační hranice v0.1 | [A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu) |
| Zachování legacy I/O při migraci | [T05](../doc/modularization-analysis.md#t05-produkci-zachovavajici-migrace) |
| Memory/checkpoint crash recovery | [T06](../doc/modularization-analysis.md#t06-memory-checkpoint-recovery) |

A01–A05 mají první návrhový výstup v A19 a čekají na review (test).
Implementační rozpad P01–P18 je v
[parent issue](3-2026-10-11-prekladove-moduly-implementace.md).
Ověření runtime/prompt kvality je součást budoucích implementačních acceptance,
nikoli hotový výsledek tohoto návrhu.

## Stav prvního návrhu a review

| Výstup | Stav / evidence |
|---|---|
| A01 volací mapa | statická revize worker/translate/JobRunner/provider, A19/A01 |
| A02 a A02b veřejný kontrakt a volba | návrh v0.1 s typy, registry, options a chybami |
| A03a kontext/paměť | planner, JSON+RAM, snapshots a checkpoint revision politika |
| A03b režimy/budgety | standard vs extended, volitelné backend porty, konečné limity |
| A04 UML | class a sequence T01–T06; textová kontrola, rendering neproveden |
| A05 migrace/testy/odhady | tři milníky a 18 leaf issues pro Lunu |

Před zahájením implementace review v0.1. Nález prvního výstupu, bridge mapping
a kompatibilita modelu mají konkrétní testovací brány; nedoplňovat náhradu
naslepo. Produkční zdroje ani AI/GPU běhy nebyly při přípravě návrhu měněny.

## Akceptační kritéria návrhu

- Jedno srozumitelné veřejné rozhraní překladového jádra; příklady in -> XHTML
  -> translated XHTML -> out a přímého html -> out.
- Definovat translator_id/options, registr a facade současného algoritmu;
  smíšená fronta používá uloženou volbu každého jobu bez globálního přepínání.
  Ověřit GUI/CLI paritu, legacy default basic, kopii a nedostupnost modulu.
- Engine neimportuje PDF/Tk/queue a nevybírá souborové formáty ani výstupní cesty.
- Invarianty: stabilní IDs a pořadí, soulad text/markup, zachování layout metadat
  a resources, přesná evidence jazyka/stylu a atomický checkpoint validovaných dat.
- Chyby, retry limity a cancellation mají definovaný výsledek i obnovu;
  pause jobu a stop workeru zůstávají odpovědností fronty.
- Cache identity zahrnuje obsah, jazyky, provider/model, prompt/style revision
  a segmentační politiku. Změna těchto hodnot nesmí znovupoužít neplatné výsledky.
  Totéž platí pro ID/revizi modulu a jeho účinné options; změna modulu
  aktivního jobu není hot-swap a nesmí smíchat nekompatibilní checkpointy.
- Metriky oddělují přípravu, AI čekání, validaci a I/O; existující preview limit
  10 s zůstává v návrhu zohledněn.
- Návrh stanoví migrační mapu stávajících kontraktů a odstranění duplicity;
  implementační plán má fake backend testy, inline markup, cancel/resume a render-only.
- Standardní cesta funguje bez tool calling; nástroje mají limity, validované
  zápisy a definované řešení konfliktů i vyčerpání rozpočtu.
- Testy pokrývají paměť větší než prompt, významové kolize, změny glosáře,
  obnovu a odmítnutí nepodporovaných režimů bez blokování standardní cesty.
- Výkonový plán nepředpokládá opakované odstavce; odděluje kvalitu, režii
  kontextu/nástrojů a skutečnou rychlost proti baseline.
- Autoritativní návrh zpřesnit v doc/modularization-analysis.md A18;
  technický přehled odkazuje na návrh a odlišuje jej od implementace.
- Mermaid vykreslení ověřit, pokud je dostupný renderer; jinak uvést textovou kontrolu.

## Vazba na další úlohy

Související: 4-2026-10-11-modularni-cleneni-zdroju.md.
Návrh není blokovaný přesuny souborů. Před implementací částí M04/M05 tohoto
refaktoringu zohlednit výsledný kontrakt; PDF sazba patří do výstupního adaptéru.
Styly zůstávají odložené v jejich vlastním tasku; existující podporu použít jako vstup.

## comments

2026-10-11: Založeno na požadavek uživatele. Priorita 3: vyjasnění veřejného
API a sjednocení kontraktů před dalším rozšiřováním. Náčrt je cílový návrh,
nikoli implementovaný stav. Tento krok pouze eviduje zadání; A01–A05 čekají.

2026-10-11: Doplněno zadání z diskuse: řízený engine, externí JSON paměť,
standardní a omezený agentní režim, relevantní kontext a cílené opravy.
Redundance odstavců není cílový předpoklad; přínos kvality a režii ověřit.
Diagramy sjednoceny v A18; odhady a rozpad rozšířeny o A03a/A03b.
Pouze dokumentační zápis: status created, analýza ani implementace nejsou hotové.

2026-10-11: Doplněn požadavek na jednoduchý výběr překladového modulu,
přednostně při zadání jobu. Basic zachová současný algoritmus; advanced je
navrhovaný modul, oba za stejným rozhraním. Přidán A02b a aktualizovány odhady.
Zapsána oddělená volba provider/model, dostupnost, migrace a checkpoint identity;
UML registru a proces T04 jsou v A18. Pouze návrh, bez implementace.

2026-10-11: Vypracován první ucelený návrh v0.1 do A19: ověřená mapa
legacy workeru, společná facade, registry, provider porty, checkpoint/memory
recovery a procesy T05/T06. Připraven parent P01–P18 a samostatné leaf issues
pro Lunu s časem/řádky/tokeny, dependency a minimálním kontextem.
Status test znamená review návrhu, nikoli runtime test hotové implementace.
