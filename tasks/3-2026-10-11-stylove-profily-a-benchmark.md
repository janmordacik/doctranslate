status: created
last change: 2026-10-11
dependency: none
group: ai/translation/style-library
type: feature
description: Zavést verzovanou knihovnu jazykových stylů pro překlad a rozšířit benchmark o stylové profily, referenční překlady, výpis výsledků na obrazovku a strukturované logování.
Priority: 3 (medium)
Created: 2026-10-11

## Cíl

Umožnit, aby překladové jádro dostalo kromě zdrojového a cílového jazyka také
volitelný stylový profil. Pokud uživatel styl nezvolí, nesmí se aplikovat
žádný předdefinovaný styl: model má zachovat registr, tón, míru expresivity a
dobové zabarvení originálu. Profil nesmí být pouze ukázka textu: musí obsahovat
pravidla, omezení, politiku expresivity a metadata ukázky. Význam, úplnost,
struktura dokumentu, placeholdery a odborné termíny mají přednost před stylem.

Stejný kontrakt musí podporovat i převod v rámci jednoho jazyka. Například
neutrální češtinu lze explicitně převést do slangového nebo argotického profilu.
Jde o řízený stylový přepis, nikoli o automatickou změnu při běžném překladu.

Rozšířit benchmark tak, aby uživatel mohl spustit:

    translate.cmd --benchmark
    translate.cmd --benchmark translategemma:4b translategemma:12b
    translate.cmd --benchmark --style cs-modern-literary
    translate.cmd --inlang cs --outlang cs --style cs-slang-argot
    translate.cmd --inlang cs --outlang cs --target-variant cs-hantec
    translate.cmd --benchmark --style auto

Bez seznamu modelů se načtou modely z Ollama. Nechat benchmark projít všechny
modely neznamená posílat překladové požadavky embedding nebo vision modelům:
modely bez kompatibilního chat/generate rozhraní se zaznamenají jako SKIP
s důvodem a nezpůsobí selhání celého běhu.

## Počáteční profily

První verze musí obsahovat tyto profily:

| ID | Význam |
|---|---|
| cs-modern-standard | moderní spisovná čeština, pouze explicitně vyžádaný profil |
| cs-expert | odborná a terminologicky přesná čeština |
| cs-modern-literary | moderní literární čeština |
| cs-archaic | historizující/archaická čeština |
| cs-parodic-archaic-polacek | parodická archaizace inspirovaná Poláčkovým typem humoru, nikoli kopírování konkrétního textu |
| cs-colloquial | přirozená hovorová čeština |
| cs-slang-argot | slang a argot se zachováním sociálního a dobového registru |
| cs-dialect-plzen | záměrně stylizovaná až karikaturní plzeňská vrstva, například copa/kampa |
| cs-colloquial-prague | záměrně stylizovaná pražská hovorová vrstva, například krásnej/neuměj |
| cs-colloquial-ostrava | záměrně stylizovaná ostravská vrstva; expresivní prvky včetně pyčo |
| cs-hantec | záměrně stylizovaný až karikaturní brněnský hantec |

Profil cs-slang-argot je určen i pro literární texty, u nichž by neutrální
čeština zničila charakter postav. Vulgarity se nesmí přidávat, ale pokud jsou
významovou součástí originálu, výchozí politika je zachovat jejich intenzitu.

Dialektové profily jsou vždy explicitní. Nesmí se použít jako výchozí styl ani
se nesmí automaticky odhadovat pouze podle jednoho slova. Tyto profily mají
naopak záměrně sklouzávat ke srozumitelné karikatuře regionu: nářeční znaky,
slovní zásoba a expresivita mají být výrazné a rozpoznatelné. Profil musí
uvést region, intenzitu karikatury, transformační pravidla a vlastní slovník.
Vulgarita typu pyčo se řídí explicitní politikou profilu a nesmí se objevit v
jinem profilu bez důvodu ve vstupu.

## Omezená znalost dialektů v modelech

Na znalost českých dialektů nelze spoléhat pouze z parametrů modelu. Některé
modely, zejména Qwen, mohou zaměňovat češtinu s polštinou nebo vytvářet
neexistující nářeční tvary. Každý dialektový profil proto musí obsahovat:

- povinné a volitelné lexikální prvky;
- transformační pravidla s příklady před/po;
- krátké pozitivní a negativní ukázky;
- seznam zakázaných nebo podezřelých polských znaků a slov;
- intenzitu karikatury v rozsahu 0 až 3;
- kontrolní fixture pro českého rodilého mluvčího.

Prompt musí výslovně požadovat češtinu, nikoli polštinu, a zdůraznit, že
karikatura se tvoří podle profilu, ne náhodným vymýšlením slov. Po překladu
proběhne lokální kontrola cílového jazyka a známek polské kontaminace. Kontrola
nesmí automaticky přepisovat text bez evidence; při podezření zapíše varování
do logu a označí výsledek pro kontrolu.

## Výchozí režim bez stylového profilu

Výchozí hodnota je style_id=auto. Nejde o další stylový profil a nesmí se do
promptu vložit instrukce typu moderní spisovná čeština. Překladový prompt pouze
požádá model, aby zachoval styl autora, registr, tón, expresivitu, dobové
zabarvení, vulgarity a sociální charakter textu.

V režimu auto platí zejména:

- vulgární originál může mít vulgární český výsledek;
- technická nebo školní učebnice nesmí dostat nově vymyšlené vulgarity;
- slang a argot se nesmí bezdůvodně převést do neutrální spisovné češtiny;
- pokud se výraz v originálu nevyskytuje a není nutný pro přirozenou syntaxi,
  překlad ho nesmí sám doplnit;
- explicitní profil může styl změnit, ale nesmí změnit význam bez politiky
  fidelity=soften nebo jiné výslovné volby.

Toto pravidlo řeší zachování stylu bez samostatné klasifikace autora. Pozdější
automatická detekce stylu může pouze doporučit profil; nesmí přepsat volbu
uživatele.

## Přepis v rámci stejného jazyka

Pokud source_language a target_language mají stejnou hodnotu, je povinný
explicitní target_variant odlišný od auto. Profil může zavést své typické slovní
nebo nářeční prvky, ale nesmí přidat nový děj, fakta ani emoce. Pole
policy.transformation určuje, zda jde o stylistický přepis, regionální
karikaturu nebo pouze jemnou úpravu registru. Pole policy.lexical_expansion
určuje, zda smí profil doplnit stylové výrazy; jejich počet a intenzita musí
zůstat omezené a reprodukovatelné.

Příklad neutrální češtiny do argotu:

    --inlang cs --outlang cs --target-variant cs-slang-argot

Výchozí auto při source_language=target_language znamená zachovat textový
styl, tedy prakticky pouze překladovou/strukturální kontrolu bez stylového
přepisu.

## Jazyk a jazyková varianta

Dialekt není v datovém modelu další hodnota jazyka. Jazyk a varianta se vedou
odděleně:

    source_language: cs
    target_language: cs
    source_variant: auto
    target_variant: cs-hantec

target_language určuje jazykovou rodinu a základní gramatiku pro backend.
target_variant určuje region, sociolekt, období nebo registr cílového textu.
Do variant proto patří standardní, odborná, literární, archaická, hovorová,
slangová i regionální podoba češtiny. Tento model umožní také překlad
angličtiny do hantecu:

    source_language: en
    target_language: cs
    target_variant: cs-hantec

GUI má zobrazovat oddělené volby Cílový jazyk a Cílová varianta. CLI používá
--outlang a --target-variant; --style zůstane kompatibilní alias pro existující
profily, ale nové rozhraní má preferovat target-variant. source_variant je
volitelná informace o vstupu a její automatická detekce nesmí měnit volbu
uživatele.

## Kontrakt profilu

Profil může být YAML nebo JSON, ale loader musí po načtení vytvořit jeden
validovaný interní model. Minimální pole:

    id
    name
    language
    description
    version
    prompt.must
    prompt.should
    prompt.avoid
    prompt.forbidden
    policy.register
    policy.period
    policy.expressivity
    policy.vulgarity
    policy.fidelity
    policy.caricature_intensity
    policy.target_language_guard
    policy.transformation
    policy.lexical_expansion
    style_samples
    lexicon
    transformations
    references

Povolené hodnoty policy.vulgarity jsou minimálně avoid, preserve-if-present a
allow. Výchozí fidelity je preserve-meaning-and-intensity. Není přípustné,
aby profil s avoid automaticky odstranil významovou vulgaritu bez výslovného
nastavení soften.

Ukázky stylu a pravidla jsou důvěryhodná konfigurace aplikace. Text zdrojového
dokumentu se nesmí stát instrukcí pro změnu stylu nebo systému promptu.
Prompt composer proto vloží styl odděleně od překladu a zachová existující
ochranu placeholderů, markup a čísel.

## Referenční texty

Fixture pro benchmark může mít více referenčních překladů. Každý záznam musí
obsahovat source_text, reference_translation, style_id, source, translator,
license_or_rights, version a případné poznámky. Referenční překlad se nesmí
porovnávat pouze přesnou shodou řetězců: správné překlady mohou být formulovány
odlišně.

Hodnocení má oddělit:

- význam a úplnost;
- gramatiku a přirozenost;
- terminologii;
- stylový registr;
- zachování struktury, čísel a značek;
- nepřidávání obsahu nebo vulgarit.

Do repozitáře se smějí přidat jen texty s ověřeným oprávněním nebo vlastní
fixture. U cizích referenčních překladů evidovat metadata a cestu/hash podle
projektové retenční politiky, ne kopírovat neověřený plný text.

## Benchmark

Benchmark pro každý model a styl:

1. ověří dostupnost a kompatibilitu modelu;
2. provede stejný en → cs fixture;
3. změří cold start, warm p50/p95, celkový čas, prompt/eval tokeny a tokeny/s;
4. zkontroluje neprázdný výstup, placeholdery, markup, čísla a nežádoucí think výstup;
5. vypíše překlad průběžně na obrazovku;
6. zapíše JSONL event log a závěrečný JSON/Markdown report;
7. při chybě označí model jako failed a pokračuje další položkou.

Výchozí nastavení je temperature=0 a think=false, pokud provider/model
nevyžaduje jiný bezpečný režim. Modely se testují sekvenčně, aby se současně
nepřetěžovala VRAM. Benchmark nestahuje modely automaticky.

Při běhu bez explicitního stylu se použije auto a zachová se styl zdroje. Volba více
stylů musí být explicitní, například opakovaným spuštěním nebo volbou
--style all; první implementace nemusí násobit všechny kombinace automaticky.

GUI i CLI musí používat stejný seznam profilů a stejnou hodnotu auto:

- GUI Job obsahuje combobox Style s první položkou Auto – zachovat styl originálu.
- CLI přijímá --style auto nebo explicitní ID profilu.
- Job uloží style_id, přičemž výchozí hodnota je auto.
- worker předá style_id do překladového jádra bez vlastní interpretace.
- benchmark používá auto, pokud styl není uveden.

Konzolový řádek obsahuje minimálně:

    MODEL | STYLE | STATUS | COLD | WARM_P50 | TOKENS/S

Log obsahuje celý výstup překladu, časy, parametry, dostupnost, důvody SKIP,
chyby a identifikaci fixture. Credentials a citlivé vstupní dokumenty se
nezapisují.

## UML návrhu

~~~mermaid
classDiagram
    class StyleProfile {
        +str id
        +str language
        +str version
        +StylePromptRules prompt
        +StylePolicy policy
        +StyleSample[] samples
        +validate()
    }

    class StylePromptRules {
        +str[] must
        +str[] should
        +str[] avoid
        +str[] forbidden
    }

    class StylePolicy {
        +str register
        +str period
        +str expressivity
        +str vulgarity
        +str fidelity
    }

    class StyleLibrary {
        +load(id) StyleProfile
        +list() StyleProfile[]
        +validate_all()
    }

    class PromptComposer {
        +compose(text, source, target, target_variant) Prompt
    }

    class BenchmarkRunner {
        +discover_models() ModelInfo[]
        +run(models, target_variant) BenchmarkReport
    }

    class BenchmarkFixture {
        +str source_text
        +str reference_translation
        +str target_variant
        +ReferenceMetadata metadata
    }

    class BenchmarkReport {
        +BenchmarkResult[] results
        +write_json()
        +write_markdown()
    }

    StyleProfile *-- StylePromptRules
    StyleProfile *-- StylePolicy
    StyleLibrary o-- StyleProfile
    PromptComposer --> StyleProfile
    BenchmarkRunner --> StyleLibrary
    BenchmarkRunner --> BenchmarkFixture
    BenchmarkRunner --> BenchmarkReport
~~~

~~~mermaid
sequenceDiagram
    actor User
    participant CLI as translate CLI
    participant Ollama
    participant Styles as StyleLibrary
    participant Runner as BenchmarkRunner
    participant Backend as TranslationBackend
    participant Log

    User->>CLI: --benchmark [models] [--style id]
    CLI->>Styles: načte a validuje styl
    alt seznam modelů není zadán
        CLI->>Ollama: /api/tags
        Ollama-->>CLI: dostupné modely
    end
    loop každý model
        CLI->>Runner: spusť fixture
        Runner->>Ollama: ověří kompatibilitu
        alt model není překladový/chat
            Runner->>Log: SKIP + důvod
        else model je použitelný
            Runner->>Backend: přelož se stylem
            Backend->>Ollama: prompt + fixture
            Ollama-->>Backend: překlad
            Backend-->>Runner: text + timing
            Runner->>Log: překlad + metriky + validace
            Runner-->>CLI: průběžný výsledek
        end
    end
    CLI->>Log: závěrečný JSON/Markdown report
~~~

## Pořadí implementace

1. Definovat interní model StyleProfile, enumy politik a validaci.
2. Přidat StyleLibrary s vestavěnými profily a verzováním.
3. Přidat PromptComposer bez zásahu do HTML/PDF adapterů.
4. Přidat fixture registry a metadata referenčních překladů.
5. Implementovat BenchmarkRunner s autodetekcí Ollama modelů a filtrem kompatibility.
6. Přidat konzolový výstup, JSONL log a Markdown/JSON report.
7. Doplnit offline testy loaderu, promptu, politik, filtrování a validace.
8. Doplnit jeden živý smoke test s lokální Ollamou.
9. Aktualizovat doc/translate.md a architekturu pouze podle skutečně změněných kontraktů.

## Implementační plán

### Fáze 0 – průzkum a kontrakty

- Zmapovat současné CLI argumenty, datový model jobu, prompt builder, Ollama
  backend, GUI comboboxy a benchmark/reporting kód.
- Ověřit existující kontrakty pro target_language, target_variant, metadata
  jobu a provider options; zachovat zpětnou kompatibilitu starších jobů.
- Rozhodnout formát vestavěné knihovny profilů podle skutečných závislostí.
  Preferovaný je verzovaný JSON/YAML registry načtený do jednoho validovaného
  interního modelu; při zbytečné závislosti použít JSON.
- Výstupem je návrh kontraktu a seznam dotčených souborů.

### Fáze 1 – model profilu a knihovna

- Implementovat StyleProfile, promptová pravidla, politiku fidelity/vulgarity,
  ukázky, lexikon, transformační pravidla a validaci.
- Implementovat StyleLibrary.list/load/validate_all s deterministickou
  registrací a srozumitelnými chybami.
- Přidat všech jedenáct počátečních profilů. Dialektové profily musí být
  explicitně karikaturní a obsahovat lexikon, pravidla a negativní příklady
  proti polské kontaminaci.
- Zachovat auto jako zvláštní výchozí režim bez předdefinovaného stylu.

### Fáze 2 – prompt a překladové jádro

- Rozšířit překladový kontrakt o style_id/target_variant bez zásahu do
  PDF/XHTML adapterů.
- Implementovat PromptComposer, který oddělí důvěryhodná pravidla profilu od
  zdrojového textu a zachová placeholdery, markup, čísla a strukturu.
- Zajistit, že auto zachová registr originálu a explicitní profil mění styl
  pouze v mezích své politiky.
- Pro převod ve stejném jazyce vyžadovat explicitní variantu odlišnou od auto.

### Fáze 3 – fixture a hodnocení

- Zavést vlastní, právně bezpečné fixture s metadaty a případně více
  referenčními překlady.
- Oddělit hodnocení významu, úplnosti, gramatiky, terminologie, registru,
  struktury a nepřidaného obsahu; nezačínat přesnou shodou jako jedinou
  metrikou.
- Přidat dialektové pozitivní/negativní fixture a varování při podezření na
  polské tvary bez automatického přepisování výstupu.

### Fáze 4 – benchmark a reporty

- Implementovat autodetekci modelů přes Ollama, kompatibilitní filtr a stav
  SKIP s důvodem pro embedding/vision/nepoužitelné modely.
- Podporovat explicitní seznam modelů i režim všech modelů z ollama list.
- Měřit cold start, warm p50/p95, celkový čas, tokeny, tokeny/s a parametry;
  modely spouštět sekvenčně.
- Přidat konzolový řádek MODEL | STYLE | STATUS | COLD | WARM_P50 | TOKENS/S,
  průběžný výpis překladu, JSONL event log a JSON/Markdown report.
- Credentials a obsah vstupních dokumentů do logu neukládat; benchmark nesmí
  automaticky stahovat modely.

### Fáze 5 – CLI/GUI napojení

- CLI: --style, --target-variant, --benchmark, volitelný seznam modelů,
  --inlang a --outlang; zachovat kompatibilní aliasy.
- GUI: stabilní položka Auto – zachovat styl originálu, oddělené cílový jazyk
  a varianta a zobrazení konfigurace v detailu jobu.
- Worker pouze předává hodnoty do jádra; interpretace stylu patří knihovně a
  prompt composeru.

### Fáze 6 – validace a dokumentace

- Po každé fázi spustit cílené testy a po dokončení celou offline sadu.
- Přidat živý smoke test s lokální Ollamou jako volitelný test mimo offline CI.
- Aktualizovat doc/translate.md, uživatelský manuál a high-level UML:
  classDiagram pro komponenty a sequenceDiagram pro překlad, benchmark, SKIP,
  chybu a režim auto.
- Teprve po splnění acceptance kritérií změnit stav tasku na test; po
  nezávislé kontrole a commitu přesunout task do tasks/done.

### Akceptační kontrolní body

1. Registry a všech jedenáct profilů se načtou bez Ollamy.
2. Prompt testy prokáží izolaci profilu od vstupu a zachování
   placeholderů/markupu/čísel.
3. CLI a GUI používají shodný seznam profilů a shodné chování auto.
4. Benchmark zvládne explicitní seznam i autodetekci, kompatibilitní filtr,
   SKIP, metriky a report bez pádu na jednom chybném modelu.
5. Offline testy pokryjí neplatná data, konfliktní politiky, stejný jazyk bez
   varianty, dialektovou kontrolu a prompt injection.
6. Živý smoke test ověří alespoň jeden dostupný model a neblokuje offline
   validaci při nedostupné Ollamě.

### Rizika a rozhodovací body

- Nejasný formát registry vyřešit ve fázi 0 podle skutečných závislostí.
- Automatické kvalitativní skóre může být nespolehlivé; první verze má
  poskytovat transparentní dimenze a referenční data, nikoli jedinou známku.
- Benchmark všech modelů může trvat dlouho; běh musí být přerušitelný a
  průběžně zapisovat výsledky.
- Dialektové profily jsou stylizace, nikoli lingvistická autorita; dokumentace
  musí tuto hranici uvádět.

## Acceptance

- Všech jedenáct počátečních profilů se načte, validuje a zobrazí v seznamu.
- Prompt obsahuje pravidla stylu odděleně od zdrojového textu.
- Význam, placeholdery, markup, čísla a struktura mají přednost před stylem.
- Vulgární slova se nepřidávají; jejich zachování nebo zmírnění řídí explicitní politika profilu.
- --benchmark bez seznamu objeví modely přes Ollama, nekompatibilní přeskočí a pokračuje.
- --benchmark s explicitním seznamem testuje pouze uvedené modely.
- GUI a CLI nabízejí stejný seznam stylů a shodně používají výchozí auto.
- Režim auto nevkládá předdefinovaný jazykový styl a zachová styl originálu.
- source_language=target_language funguje pouze s explicitním target_variant;
  neutrální češtinu lze převést do cs-slang-argot bez přidání nového obsahu.
- Překlady a metriky jsou viditelné na obrazovce i v logu.
- Report obsahuje cold/warm časy, tokeny/s, chyby, SKIP důvody a identifikaci fixture.
- Referenční překlad se vyhodnocuje po dimenzích, ne pouze přesnou shodou.
- Offline testy pokryjí neplatný profil, neznámou politiku, chybějící pole,
  konflikt vulgarity a fidelity, prompt injection ve vstupu a nedostupný model.
- Dialektové profily používají explicitní slovník, transformační pravidla a
  pozitivní/negativní fixture; test ověří cílovou češtinu a varování při
  polské kontaminaci.
- Benchmark nevolá Ollamu během PDF-only fáze a automaticky nestahuje modely.

## Otevřené otázky

- Zda první verze přijme pouze YAML/JSON soubory, nebo i registry v Pythonu.
- Zda se reference budou hodnotit ručně, pomocí odděleného judge modelu, nebo kombinací.
- Které tradiční ukázky a překlady mají ověřená práva pro trvalé uložení.
- Zda profil slang/argot zůstane jeden profil, nebo se později rozdělí podle období a regionu.

## comments

2026-10-11: Task založen podle požadavku na knihovnu stylů, která kromě ukázek obsahuje i explicitní promptová pravidla. Počáteční sada zahrnuje moderní spisovnou, odbornou, moderní literární, archaickou, parodickou archaickou, hovorovou, slangovou/argotickou a čtyři regionální profily. Implementace nebyla zahájena.
2026-10-11: Upřesněno napojení do GUI/CLI. Výchozí režim je auto bez předdefinovaného stylu: zachovává styl autora včetně vulgarit, ale nepřidává vulgarity do neutrálního nebo odborného textu. Explicitní profily jsou volitelné.
2026-10-11: Upřesněno, že regionální profily mají být záměrně karikaturní. Doplněn požadavek na profilové slovníky, transformační pravidla a kontrolu češtiny proti polské kontaminaci, protože znalost modelu nemusí být spolehlivá.
2026-10-11: Jazyk a dialekt/registr jsou odděleny jako target_language a target_variant. Stejný mechanismus tak podporuje překlad do varianty i převod mezi variantami bez zvláštního jazyka.
2026-10-11: Zapsán implementační plán ve fázích 0–6. Task zůstává ve stavu created; implementace ani živý benchmark nebyly zahájeny. Po každé fázi se počítá s cílenou validací, na konci s offline sadou a volitelným Ollama smoke testem.
