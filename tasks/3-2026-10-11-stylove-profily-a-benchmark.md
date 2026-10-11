status: progress
last change: 2026-10-11
dependency: none
group: ai/translation/style-library
type: feature
estimate:
  time: 5 h 20–9 h 20 čisté práce; živé benchmarky a ruční review zvlášť
  logical_lines: 1130–1990 včetně testů, katalogu a dokumentace
  tokens: 44k–78k pracovní orientace; kontext po B-krocích 3k–7k
  subtasks: B01–B08; B02.1–B02.3 a B03.1–B03.3 v doc/style-benchmark-implementation.md
description: Zavést verzovanou knihovnu jazykových stylů pro překlad a rozšířit benchmark o stylové profily, referenční překlady, výpis výsledků na obrazovku a strukturované logování.
Priority: 3 (medium)
Created: 2026-10-11
Implementation agent: Codex 5.6 Luna (určen uživatelem; nyní nespouštěn)

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
prokazatelně netextové modely se zaznamenají jako SKIP
s důvodem a nezpůsobí selhání celého běhu. Vision model s podporou textu není
automaticky SKIP; neznámá schopnost se ověří měřeným během.

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
karikatura se tvoří podle profilu, ne náhodným vymýšlením slov. V navazujícím rozšíření může po překladu
proběhnout lokální kontrola cílového jazyka a známek polské kontaminace. Kontrola
nesmí automaticky přepisovat text bez evidence; při podezření zapíše varování
do logu a označí výsledek pro kontrolu.

## Výchozí režim bez stylového profilu

Výchozí hodnota je target_variant=auto. Nejde o další stylový profil a nesmí se do
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

Pokud source_language a target_language mají stejnou hodnotu, přepis vyžaduje
explicitní target_variant odlišný od auto; auto zachová vstup bez AI přepisu. Profil může zavést své typické slovní
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
--outlang a --target-variant; --style bude alias pro ID profilu,
ale kanonické pole je target_variant. source_variant je
volitelná informace o vstupu a její automatická detekce nesmí měnit volbu
uživatele.

## Kontrakt profilu

Pro MVP je profil JSON v balíčku; loader musí po načtení vytvořit jeden
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
3. změří první požadavek, warm p50/p95, load_duration, celkový čas, prompt/eval tokeny a tokeny/s;
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
- Job uloží target_variant, přičemž výchozí hodnota je auto.
- worker předá target_variant do překladového jádra bez vlastní interpretace.
- benchmark používá auto, pokud styl není uveden.

Konzolový řádek obsahuje minimálně:

    MODEL | VARIANT | STATUS | FIRST_REQUEST | WARM_P50 | TOKENS/S

Log obsahuje celý výstup překladu, časy, parametry, dostupnost, důvody SKIP,
chyby a identifikaci fixture. Credentials a citlivé vstupní dokumenty se
nezapisují.

## Autoritativní implementační plán

[Plán B01–B08](../doc/style-benchmark-implementation.md) obsahuje aktuální
mapu symbolů, minimální kontext, kontrakty, povolené soubory, závislosti,
testy, odhady a cílové Mermaid class/sequence diagramy s procesním indexem.
Nahrazuje původní S01–S56 i rozporné tabulky pracnosti. Historické komentáře
zůstávají evidencí, nejsou aktuálním zadáním.

Pořadí: katalog → skutečně odeslané prompty → job/worker/cache → fixture →
měřicí runner → CLI/reporty → GUI → regrese/instalace/dokumentace. Každý
B-krok zahrnuje své testy; nevytvářet nefunkční mezistav bez ověření.

Kanonická hodnota je target_variant=auto, --style je alias. Providerový
profile_id je nezávislý. Podrobná rozhodnutí v plánu řeší také cs→cs auto,
text+vision modely, first-request versus cold start a obnovu cache.

Pro Codex 5.6 Luna plán obsahuje přesné API kontrakty, mapování payloadů,
šest menších kroků B02.1–B03.3 a pevný stats_callback benchmarku. Souhrnné
odhady zůstávají stejné; podkroky se k nim nepřičítají podruhé.

Restart: zapsat poslední dokončený B-krok/podkrok, soubory a testy do comments.
Aktuálně nejsou B01–B08 implementované; tato revize upravuje pouze zadání.

## Acceptance

- Všech jedenáct počátečních profilů se načte, validuje a zobrazí v seznamu.
- Prompt obsahuje pravidla stylu odděleně od zdrojového textu.
- Význam, placeholdery, markup, čísla a struktura mají přednost před stylem.
- Vulgární slova se nepřidávají; jejich zachování nebo zmírnění řídí explicitní politika profilu.
- --benchmark bez seznamu objeví modely přes Ollama, nekompatibilní přeskočí a pokračuje.
- --benchmark s explicitním seznamem testuje pouze uvedené modely.
- GUI a CLI nabízejí stejný seznam stylů a shodně používají výchozí auto.
- Režim auto nevkládá předdefinovaný jazykový styl a zachová styl originálu.
- source_language=target_language provádí přepis pouze s explicitním target_variant;
  auto zachová vstup bez AI;
  neutrální češtinu lze převést do cs-slang-argot bez přidání nového obsahu.
- Překlady a metriky jsou viditelné na obrazovce i v logu.
- Report obsahuje first-request/warm časy, skutečné load_duration, tokeny/s,
  chyby, SKIP důvody a fixture; neověřený cold start se neslibuje.
- MVP uloží metadata referenčního překladu a strukturální kontroly; úplné
  dimenzionální kvalitativní hodnocení je navazující rozšíření.
- Offline testy pokryjí neplatný profil, neznámou politiku, chybějící pole,
  konflikt vulgarity a fidelity, prompt injection ve vstupu a nedostupný model.
- Dialektové profily používají explicitní slovník a transformační pravidla.
  MVP negarantuje automatickou detekci polské kontaminace; ta je navazující
  rozšíření s vlastními pozitivními/negativními fixture.
- Benchmark nevolá Ollamu během PDF-only fáze a automaticky nestahuje modely.

## Otevřené otázky

- Pro MVP rozhodnuto: JSON v balíčku, bez nové YAML dependency.
- Pro MVP rozhodnuto: strukturální kontroly a ruční rubrika; judge je rozšíření.
- Které tradiční ukázky a překlady mají ověřená práva pro trvalé uložení.
- Zda profil slang/argot zůstane jeden profil, nebo se později rozdělí podle období a regionu.

## comments

2026-10-11: Task založen podle požadavku na knihovnu stylů, která kromě ukázek obsahuje i explicitní promptová pravidla. Počáteční sada zahrnuje moderní spisovnou, odbornou, moderní literární, archaickou, parodickou archaickou, hovorovou, slangovou/argotickou a čtyři regionální profily. Implementace nebyla zahájena.
2026-10-11: Upřesněno napojení do GUI/CLI. Výchozí režim je auto bez předdefinovaného stylu: zachovává styl autora včetně vulgarit, ale nepřidává vulgarity do neutrálního nebo odborného textu. Explicitní profily jsou volitelné.
2026-10-11: Upřesněno, že regionální profily mají být záměrně karikaturní. Doplněn požadavek na profilové slovníky, transformační pravidla a kontrolu češtiny proti polské kontaminaci, protože znalost modelu nemusí být spolehlivá.
2026-10-11: Jazyk a dialekt/registr jsou odděleny jako target_language a target_variant. Stejný mechanismus tak podporuje překlad do varianty i převod mezi variantami bez zvláštního jazyka.
2026-10-11: Zapsán implementační plán ve fázích 0–6. Task zůstává ve stavu created; implementace ani živý benchmark nebyly zahájeny. Po každé fázi se počítá s cílenou validací, na konci s offline sadou a volitelným Ollama smoke testem.
2026-10-11: Plán znovu zkontrolován po commitu cloudové autentizace. Pořadí zůstává: kontrakt a registry, prompt composer, fixture, benchmark/reporty, CLI/GUI a závěrečná validace. Implementace se zatím nespouští.
2026-10-11: Doplněn odhad pracnosti 19–33 hodin čistého času, vertikální řez 7–12 hodin a riziková rezerva 20–30 %. Čas živého benchmarku je uveden samostatně a není součástí odhadu implementace.
2026-10-11: Plán rozložen na 56 subtasků S01–S56 v doporučené délce 15–30 minut, se závislostmi a kontrolními body po každé fázi.
2026-10-11: Původní jednotný odhad 15–30 minut na každý subtask byl vyhodnocen jako nadhodnocený. Upraveno na 2–10 minut pro průzkum/dokumentaci, 10–25 minut pro malé změny a 15–30 minut pro integraci; čistý odhad celku je 6–12 hodin, elapsed odhad 8–16 hodin.
2026-10-11: Revize proti skutečnému kódu potvrdila znovupoužití PerformanceRecorderu, segmentového překladu, JobSpec a Ollama strategií. Automatické kvalitativní skóre a dialektový detektor zůstávají mimo MVP. Odhad první verze je 5–9 hodin čisté práce a 7–13 hodin elapsed času.
2026-10-11: Doplněn odhad velikosti změn pro každý subtask; celkem přibližně 775–1 630 logických řádků včetně testů, fixture a dokumentace.
2026-10-11: Implementátorem bude podle uživatele Codex 5.6 Luna. Doplněny pevné kontrakty, mapování provider payloadů, callback metrik a šest menších integračních kroků s odhady/testy. Agent nebyl spuštěn; jde pouze o zpřesnění předání, ne ověření jeho schopností.
2026-10-11: Revize proti skutečným worker/provider cestám: původní S01–S56 a rozporné odhady nahrazuje plán B01–B08 v doc/style-benchmark-implementation.md. Doplněny minimální kontext, odhady, cache/obnova, balení dat, jednotný prompt dispatch, modelové schopnosti a přesné metriky. Vyřešeny rozpory varianty/style_id a cs→cs auto; diagramy odkazují na jeden cílový návrh. Implementace ani modelové requesty při revizi neproběhly.
2026-10-11: B01 dokončen. Přidána neměnná knihovna StyleProfile/StyleLibrary načítaná přes importlib.resources, validace katalogu/politik, implicitní varianta auto, jedenáct českých profilů v JSON včetně slovníků a ochranných pravidel pro dialekty, exporty balíčku a testy. Cílené testy B01 + provider profiles: 15 passed. Další krok: B02.1 kontrakt prompt composeru.
2026-10-11: B02.1 dokončen. Přidán compose_policy a translate_prompt, PromptBuilder přijímá katalog a připojuje stylové instrukce před hranici s nedůvěryhodnými daty. Auto nepřidává stylovou ukázku a explicitní profil kontroluje cílový jazyk. Cílené testy promptů, katalogu, pipeline a provider profiles: 23 passed. B02 jako celek zůstává otevřený; další krok B02.2 napojení skutečných provider requestů.
2026-10-11: B02.2 dokončen. HttpAiBackend podporuje volitelný target_variant bez rozbití starého translate API, translate_segments předává variantu z atributů a Ollama/TranslateGemma/OpenAI/Gemini/Claude vkládají společnou politiku do skutečných payloadů. Testy provider payloadů a offline AI sad: 28 passed + 4 subtests. B02.3 legacy JSON batch bridge zůstává otevřený, protože současný translate.py skládá globální prompt mimo nový job/variant kontrakt.
2026-10-11: B04 dokončen v základním rozsahu. Přidán loader BenchmarkFixture a dva vlastní, verzované fixture vstupy: en→cs s rostoucí gramatickou/lexikální obtížností a cs→cs přepis. Obsahuje reference, hash, provenance a placeholder/číselné tokeny; reference není součástí promptu. Cílené testy: 31 passed + 4 subtests.
2026-10-11: B05 dokončen v MVP rozsahu. Přidány BenchmarkSample, BenchmarkResult a BenchmarkRunner s first/warm opakováním, wall time, textem, chybami, skip stavem a cancel. Tokenová/provider metadata zůstávají null, dokud je konkrétní backend neposkytne; benchmark je proto neoznačuje jako změřená. Cílená sada: 34 passed + 4 subtests.
2026-10-11: B06 dokončen v základním lokálním rozsahu. Přidán --benchmark [MODEL ...], discovery přes Ollama endpoint bez stahování modelů, konzolový výpis překladů/časů a JSON report s fixture/reference/sample daty. Cílené testy: 36 passed + 4 subtests. Plné pytest -q je blokováno cizím paralelním balíkem a ACL cache; správný příkaz python -m pytest test -q prošel jako 151 passed + 4 subtests. B02.3 legacy batch bridge, B03 job/cache, B07 GUI a B08 dokumentace/UML zůstávají otevřené.
2026-10-11: B03 průběžně: JobSpec, JobRunner.identity, queue normalizace a make_job nyní nesou target_variant s kompatibilním defaultem auto; variantu worker předává v SegmentRequest.attributes a změna varianty invaliduje checkpoint identity. Cílené job/queue testy: 47 passed. Profilový hash/revize, HTML metadata, obnova legacy cache a GUI výběr zůstávají otevřené.
2026-10-11: B03/B07 pokračování: JobSpec počítá při absenci explicitní revize fingerprint katalogu, queue normalizuje target_variant a dopočítává style_revision, HTML/XHTML metadata nesou target_variant/style_revision/prompt_revision, explicitní varianta je součástí cache identity a historické auto cache zůstává čitelné. Worker přenáší target_variant do legacy translate běhu. GUI má v Job skupině lokalizovaný výběr stylu Auto + katalog profilů, zachovává jej při výběru/kopii a ukládá při OK. Doplněn CLI alias --style/--target-variant a benchmark varianty. Celá offline sada: 153 passed, 4 subtests passed; compileall src/doctranslate prošel.
2026-10-11: B02.3 dokončen: HttpAiBackend a konkrétní provideři mají precomposed prompt kontrakt, ProviderBatchClient jej používá pro již sestavený strukturovaný JSON prompt a test ověřuje, že se prompt neposílá přes další překladový wrapper. Celá offline sada po změně: 154 passed, 4 subtests passed. B03/B07 zůstávají průběžné kvůli PDF-only/discovery validaci, cílovému jazyku v queue GUI a ručnímu GUI smoke. B08 nebyl zahájen.
2026-10-11: B08 dokumentace průběžně: aktualizovány doc/translate.md, doc/user-manual.md a doc/modularization-analysis.md o katalog stylů, CLI benchmark, aktuální stav a Mermaid class/sequence diagramy. Zbývá instalační/wheel kontrola, případně render Mermaid a ruční GUI/live Ollama smoke.
2026-10-11: B03 dokončen: queue normalizuje explicitní profil proti cílovému jazyku a vždy přepočítá aktuální fingerprint; worker nastavuje variantu před configure, takže explicitní cs→cs převod funguje, auto zůstává bez AI přepisu. PDF-only discovery a HTML metadata jsou pokryté offline testy.
2026-10-11: B07 dokončen implementačně: GUI Job detail má zdrojový/cílový jazyk, filtr stylů podle cílového jazyka, jazykově závislé názvy výstupu a kompatibilitu Copy/Cancel/OK. Celá offline sada po změně: 154 passed, 4 subtests passed.
2026-10-11: B08 dokončen dokumentačně a textovou kontrolou Mermaid bloků. Wheel check nelze dokončit v aktuálním C:/Python314, protože chybí setuptools.build_meta; projektový pyproject nebyl měněn a omezení je zapsáno v doc/tools.md. Zbývá pouze uživatelský live Ollama benchmark, GUI smoke, vizuální kontrola PDF a případná instalace setuptools pro opakování wheel checku.
2026-10-11: Upřesněna ochrana stejného jazyka: GUI nepovolí uložit auto při source=target a vyžádá explicitní profil; CLI/worker stejnou kombinaci odmítnou před AI voláním. Explicitní cs→cs stylový převod zůstává podporovaný.
2026-10-11: Po instalaci setuptools odhalil wheel check chybu v package-data zápisu; klíč doctranslate.ai.data byl opraven v pyproject.toml. Wheel doctranslate-0.1.0-py3-none-any.whl byl úspěšně sestaven a obsahuje styles.json i benchmark.json. Před spuštěním byly ověřeny Python, setuptools, pytest, PyMuPDF, keyring a Ollama; offline regrese: 156 passed, 4 subtests passed.
