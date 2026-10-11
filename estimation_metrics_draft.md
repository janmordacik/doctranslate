# Odhadové metriky – pracovní návrh

Stav: pracovní dokument, nikoli finální návod. Rozpracování a pilot odloženy
na žádost uživatele 2026-10-11; návrhy ani konstanty nejsou potvrzenou metodikou.

## Účel

Tento soubor je měřený základ pro další odhady tasků v projektu. Odhad a skutečnost se zapisují současně v těchto dimenzích:

- čas: odhadované minuty;
- rozsah: odhadované logické řádky a skutečný Git diff;
- pracovní kontext: orientační tokeny;
- ověřitelnost: počet souborů, testy a stav.

## Pracovní návrh kompromisu – revize 2026-10-11

Stav: pracovní podklad, nikoli finální návod ani schválená metodika.
Další rozpracování a pilot jsou na žádost uživatele odložené v
[tasku praktických odhadů](tasks/5-2026-10-11-prakticke-odhady-slozitosti-tasku.md).
Dosavadní výpočty a model simple-v1 jsou zachované pro porovnání; jejich
konstanty nejsou tímto návrhem potvrzené. Následující postup čeká na ověření.

### Zvolený směr

- Hierarchický rozpad podle výsledků práce (WBS) a odhad od nejnižších úloh
  směrem k celku (bottom-up).
- Odhad podle podobných dokončených úloh; lehká adaptace inspirovaná PROBE,
  nikoli tvrzení o úplném zavedení PSP/PROBE.
- Explicitní závislosti pro pořadí implementace a omezení na jednoho vývojáře.
- Žádné nevysvětlitelné body složitosti ani univerzální převod bodů na čas.
  Matematické vzorce nezaručují přesnost bez vhodných měření.

PROBE používá předběžný návrh a historickou velikost podobných částí; doporučuje
malý počet kategorií, aby odhad nevynucoval předčasně podrobný návrh.
[SEI: PROBE](https://www.sei.cmu.edu/documents/2108/2006_004_001_14693.pdf).
WBS, činnosti, závislosti a délky činností jsou podkladem harmonogramu a CPM.
[PMI: WBS a kritická cesta](https://www.pmi.org/learning/library/moving-work-breakdown-structure-critical-path-6978).
Pro kapacitní omezení je třeba také plánování zdrojů; samotná technická
nezávislost dvou úloh neumožní jednomu vývojáři pracovat na obou současně.
[PMI: resource leveling](https://www.pmi.org/learning/library/scheduling-resource-leveling-project-progression-8006).

### Minimální postup a zápis

1. Popsat konkrétní výsledek, hranici změny a ověření dokončení.
2. Rozdělit na samostatně pochopitelné a testovatelné části podle chování,
   nikoli mechanicky na denní nebo stejně velké úlohy. Řádkové orientace
   přibližně 40 pro interaktivní krok a 200–400 pro review zůstávají vodítkem.
3. Uvést interval času a řádků, profil implementátora a podobné hotové úlohy.
   Pokud srovnatelná historie chybí, odhad označit jako předběžný.
4. Zapsat hlavní konkrétní nejistotu; nevymýšlet další entity, počty ani UML
   jen kvůli odhadu. Nejasné zadání dopracovat. Technickou neznámou může řešit
   krátký průzkumný subtask s jasným výsledkem, poté odhad zpřesnit.
5. Zaznamenat skutečný výsledek, zachovat původní odhad a vysvětlit odchylky.
   Kalibrovat zvlášť pro člověka, Codex a další agenty podle srovnatelných úloh.

| Subtask | Výsledek a ověření | Závislosti | Čas / profil | Řádky | Reference / nejistota |
|---|---|---|---|---|---|
| Sxx | Jedna ověřitelná změna | ID předpokladů nebo none | Interval a implementátor | Interval podle kategorií | Podobný dokončený task nebo předběžný odhad; konkrétní riziko |

Čas znamená nezbytné načtení kontextu, implementaci, testy, review a potřebnou
dokumentaci; externí čekání a přerušení uvádět zvlášť. Rozsah rozlišovat na
produkční kód, testy a dokumentaci. Logické řádky pro review nezaměňovat s
Git insertions + deletions; porovnávat stejné jednotky. Tokeny uvádět jen jako
orientační doplněk s podkladem nebo označením neměřeno.

### Hierarchie, závislosti a harmonogram

Návrh rozlišuje parent (nadřazený celek ve WBS) a dependency (skutečné
implementační předpoklady, může jich být několik). Dosavadní označení parent
issue v projektové dokumentaci nesmí vést k záměně těchto významů.
Jde o návrh zpřesnění formátu; existující tasky ani schéma se nyní nemigrují.

Nadřazený celek agreguje odhady listových úloh; jeho vlastní práci evidovat
samostatně, nikoli započítat dvakrát. Pro implementaci vybírat neodložené
úlohy se splněnými závislostmi; dále podle priority, odblokování další práce
a stabilního pořadí. Graf musí být acyklický.
Gantt je volitelné zobrazení větších celků a termínů. Výpočet kritické cesty
a termínů musí respektovat jediného pracovníka i případné externí čekání.
Pro běžnou práci může stačit seznam připravených a blokovaných úloh.

### Režie a budoucí ověření

Příprava odhadu má orientačně zabrat přibližně do 5 % celkového času přípravy
implementačního zadání, včetně odhadu. Jde o měkký, upravitelný cíl, nikoli
tvrdé akceptační maximum ani podíl času implementace.
Pokud cíl nereflektuje realitu nebo přínos odhadu, upravit jej na základě
pilotních měření a zdůvodnit. U drobných úloh nevynucovat nákladné měření.

Po obnovení porovnat praktický postup s dosavadním simple-v1 na nejméně pěti
běžných zadáních. Hodnotit srozumitelnost, režii, chybu času/řádků a užitečnost
intervalů; nic dalšího nepřidávat bez doloženého přínosu. Historické časové
proxy z filesystemu a commitů jsou pouze počáteční podklad, nikoli přesné
měření aktivní práce. Nyní nebyl proveden pilot ani změna aplikace.

## Zdroj a omezení měření

Porovnání bylo vytvořeno 11. 10. 2026 6:01:03 až 11. 10. 2026 6:31:13 z tasků P01–P18.

- Odhad je převzat z bloku estimate v odpovídajícím tasku.
- Skutečný rozsah je součet insertions + deletions z commitu, nikoli počet unikátních výsledných řádků.
- Čas tasku v detailní tabulce je proxy od nejstaršího nového souboru do commitu. Celý průchod je od prvního nového souboru po poslední commit; samotné intervaly mezi commity ani časy souborů nezaručují úplné měření práce.
- Tokeny skutečné implementace Git neměří. Uvádí se jen plánovaný rozsah.
- Commit může zahrnovat task, testy, dokumentaci i změnu samotného tasku. Proto je Git diff záměrně označen jako diff lines, nikoli jako čisté logical lines.

## Použité heuristiky



### Heuristiky původního odhadu

Původní odhady nevznikaly z historického měření. Byly ručně odvozeny z textu tasku a z pochopení aktuálního kódu. Níže je jejich rekonstruovaný rozhodovací postup; nejde o přesný záznam jednotlivých interních kroků ani o statisticky kalibrovaný model.

| Signál v popisu tasku | Jak byl interpretován | Dopad na odhad času | Dopad na odhad řádků |
|---|---|---:|---:|
| Změna jedné funkce nebo jednoho validačního pravidla | malý lokální zásah | nízký | nízký |
| Nové veřejné rozhraní nebo kontrakt | nutnost navrhnout API a upravit volající | střední až vysoký | střední |
| Změna přes více vrstev (CLI, GUI, worker, model) | integrační task | vysoký | vysoký |
| Nový provider, adaptér nebo backend | nový integrační bod s konfigurací a chybovými stavy | vysoký | vysoký |
| Změna fronty, workeru, pause/stop/restart nebo recovery | stavový a konkurenční problém | vysoký | střední až vysoký |
| Požadavek na zachování starého chování | kompatibilita a regresní riziko | zvýšení rezervy | zvýšení rezervy |
| Požadavek na testy, smoke test nebo benchmark | další implementace a ověření | zvýšení rezervy | zvýšení |
| Požadavek na dokumentaci, diagramy nebo migraci dat | práce mimo produkční kód | zvýšení rezervy | zvýšení |
| Nejasná závislost na externím nástroji (Ollama, PDF, cloud API) | riziko diagnostiky a opakovaných pokusů | zvýšení rezervy | obvykle malé zvýšení |
| Čistě mechanická změna nebo přejmenování | nízké logické riziko | nízký | podle počtu míst |

Z těchto signálů se použila následující praktická heuristika:

1. Nejprve se odhadla základní velikost podle počtu dotčených vrstev a nových rozhodnutí.
2. Za každou další integrační hranici se zvýšila časová rezerva, protože bylo nutné projít kontrakty, chyby a testy.
3. Za explicitní požadavek na testy nebo dokumentaci se přidal samostatný rozsah, nikoli jen časová rezerva.
4. U nejasných nebo stavových tasků se použil širší interval, protože nebylo jisté, kolik existujícího kódu bude nutné změnit.
5. Odhad řádků představoval logické řádky produkčního kódu, testů a dokumentace. Nešlo o odhad výsledného Git diffu.
6. Odhad času byl odhad práce na pochopení, implementaci, testech a review; nebyl to odhad čistého času psaní kódu.
7. Tasky se měly dělit podle chování a samostatné reviewovatelnosti, nikoli mechanicky podle počtu řádků.

Typický odhadovací vzorec byl tedy přibližně:

čas = základ podle složitosti + integrace + testy + dokumentace + riziková rezerva

řádky = produkční změna + testy + dokumentace + nutná konfigurace

Tyto vzorce jsou rekonstrukce původní heuristiky. Kandidátní postup, profily implementátorů a kalibrace jsou uvedené níže v části „Odhadování 1.0 – dosavadní kandidátní model simple-v1“. Podrobný seznam parametrů zůstává návrhem pro případné další verze.

### Co původní heuristika neobsahovala

- Neměla explicitní sazbu řádků za minutu.
- Nerozlišovala systematicky produkční kód, testy, dokumentaci a metadata.
- Nepracovala s pravděpodobností rizik ani s evidencí retry a čekání na externí nástroje.
- Neměla základní odhad odvozený z typu tasku a historicky podobných tasků.
- Neověřovala, zda je rozsah tasku skutečně vhodný pro jeden samostatně reviewovatelný krok.

### Heuristiky skutečných hodnot



- Skutečný čas byl odvozen jako rozdíl mezi nejstarším filesystemovým birthtime nově přidaného souboru v commitu a časem implementačního commitu.

- Předpokladem je nepřerušený dávkový běh P02–P17; proto tento čas zachycuje průběžný wall-clock rozsah, ale může obsahovat čekání a review.

- Tasky P01 a P18 byly vyřazeny, protože jejich implementační commity neobsahovaly žádný nově přidaný soubor.

- Skutečné řádky jsou Git numstat: vložení plus smazání. Zahrnují produkční kód, testy, dokumentaci i změny tasků.

- Skutečné řádky proto nejsou totéž co počet výsledných logických řádků.



### Regresní heuristiky



- Všechny koeficienty byly fitovány proporcionální regresí přes počátek ve tvaru cíl = k × vstup.

- K1 odvozuje odhadovaný čas ze skutečného času.

- K2 odvozuje odhadované řádky ze skutečných řádků.

- K3 odvozuje odhadované řádky z odhadovaného času.

- K4 odvozuje skutečné řádky ze skutečného času.

- Procentní odchylka je (cílová hodnota − predikce) / predikce × 100.

- Regrese nebyla společně omezená; jednotlivé koeficienty proto nejsou přesně algebraicky konzistentní.



### Co je třeba nahradit měřením



- Start a konec tasku měřit explicitním monotónním časovačem nebo běhovým logem.

- Oddělit aktivní implementaci, testy, review, čekání na externí nástroj a opakované pokusy.

- Řádky evidovat odděleně pro produkční kód, testy, dokumentaci a metadata tasků.

- Ukládat typ tasku, počet subtasků, počet souborů, nové soubory, retry a výsledek validace.

- K1–K4 používat pouze jako retrospektivní popis této dávky, dokud nebude k dispozici větší homogenní soubor měření.

## Souhrn

Souhrnné odhady, detailní tabulka a kalibrace zahrnují pouze P02–P17. P01 a P18 byly vyřazeny, protože jejich implementační commit nemá žádný nově přidaný soubor.

| Metrika | Odhad P02–P17 | Skutečnost / pozorování |
|---|---:|---:|
| Čas | 835–1440 min | commit span 26 min 50 s; čistý pracovní čas není z Git doložitelný |
| Logické řádky | 3140–5200 | 5994 vložení, 69 smazání, 6063 diff řádků |
| Pracovní tokeny | 43–76 k | Git neposkytuje měření |
| Commity | 16 | 16 zahrnutých commitů |
| Zasažené soubory v commitech | — | 66 položek numstat |
| Střed odhadu času | 1 137,5 min | nelze zaměňovat s 26 min 50 s commit spanem |

Poměr skutečného diffu k průměru odhadovaného rozsahu je přibližně 1,45×. Pozorovaný commit throughput 226 diff řádků/min je pouze vlastnost této konkrétní dávky a nesmí se používat jako obecná rychlost implementace.

## Regresní koeficienty pro odhady

Všechny vztahy používají jediný zápis: cíl = k × vstup. Koeficienty jsou proporcionální fit přes počátek z P02–P17.

| ID | Typ | Jednotný vztah | k | Jednotka | Interpretace |
|---|---|---|---:|---|---|
| K1 | korekce času | odhadovaný čas = k × skutečný čas | 58.463201 | min/min | 1 min skutečného času dává 58.46 min odhadovaného času |
| K2 | korekce řádků | odhadované řádky = k × skutečné řádky | 0.557896 | řádek/řádek | 100 skutečných řádků dává 55.79 odhadovaných řádků; skutečnost je přibližně 1.79× odhadu |
| K3 | rychlost odhadu | odhadované řádky = k × odhadovaný čas | 3.641800 | řádek/min | 1 odhadovaná minuta dává 3.64 odhadovaných řádků |
| K4 | skutečná rychlost | skutečné řádky = k × skutečný čas | 355.258766 | řádek/min | 1 skutečná minuta dává 355.26 skutečných řádků |

K1 a K2 jsou korekční faktory. K3 a K4 jsou rychlosti v řádcích za minutu. K4 je kalibrace této nepřerušené dávky; skutečné řádky jsou Git diff včetně testů a dokumentace.

### Diagnostické metriky fitu přes počátek

| ID | R² | RMSE | MAE |
|---|---:|---:|---:|
| K1 | 0.762687 | 34.950178 | 31.303445 |
| K2 | 0.800898 | 116.885117 | 95.005718 |
| K3 | 0.994869 | 18.763500 | 16.343344 |
| K4 | 0.820983 | 177.788597 | 144.737591 |

### Kauzalita a interpretace

Regrese ukazuje asociaci v tomto vzorku, nikoli kauzalitu. Nepřerušený běh zvyšuje vypovídací hodnotu časového proxy údaje: P02–P17 pokrývají přibližně 27,62 min od prvního nového souboru do posledního commitu. Odhadovaný čas a odhadované řádky jsou stále dvě heuristiky odvozené ze stejného popisu složitosti tasku; bez experimentu s kontrolovanou změnou jedné veličiny nelze tvrdit, že jedna způsobuje druhou.

### Konzistence rychlosti a časové korekce

Samotný K1 rychlost neurčuje. Protože K2 převádí odhadované řádky na skutečné řádky, očekávaná kombinace je K1 / K2. Přímé porovnání rychlostí je K4 / K3.

| Výpočet | Hodnota |
|---|---:|
| K4 / K3 | 97.5503 |
| K1 / K2 | 104.7922 |
| rozdíl | -6.9107 % |

Rozdíl vzniká tím, že všechny koeficienty jsou samostatné proporcionální regrese, nikoli jeden společně omezený model. K3 a K4 navíc používají odlišné veličiny a K4 zahrnuje Git diff testů a dokumentace. Řádově proto výsledky souhlasí: odhadovaná rychlost je přibližně 3.64 řádku/min, skutečný diff přibližně 355.26 řádku/min a poměr rychlostí je přibližně 98×.

### Závěr

K3 není přímá rychlost modelu, ale podíl odhadovaných řádků a odhadovaného času. Podhodnocení počtu řádků proto K3 uměle snižuje. Po započtení K1 a K2 vychází K1 / K2 = 104.79×, zatímco přímé porovnání rychlostí K4 / K3 = 97.55×. Rozdíl je přibližně 6.9 %, takže nadhodnocený čas a podhodnocený počet řádků společně vysvětlují téměř celý rozdíl.

## Odchylky proporcionálních modelů

Odchylka je skutečnost minus predikce. K1 a K2 predikují odhad z reality. K3 převádí odhadovaný čas na odhadované řádky. K4 převádí skutečný čas na skutečné řádky.

| Číslo řádku | Task | Odhad čas | Skutečný čas | K1 predikce | K1 odchylka | Odhad řádky | Skutečné řádky | K2 predikce | K2 odchylka | K3 predikce | K3 odchylka | K4 predikce | K4 odchylka |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | P02 | 55.00 | 0.78 | 45.69 | 9.31 | 210.00 | 504 | 281.18 | -71.18 | 200.30 | 9.70 | 277.62 | 226.38 |
| 2 | P03 | 80.00 | 0.56 | 33.02 | 46.98 | 260.00 | 314 | 175.18 | 84.82 | 291.34 | -31.34 | 200.67 | 113.33 |
| 3 | P04 | 60.00 | 0.71 | 41.64 | 18.36 | 240.00 | 421 | 234.87 | 5.13 | 218.51 | 21.49 | 253.06 | 167.94 |
| 4 | P05 | 80.00 | 0.92 | 53.51 | 26.49 | 270.00 | 344 | 191.92 | 78.08 | 291.34 | -21.34 | 325.19 | 18.81 |
| 5 | P06 | 55.00 | 0.39 | 22.70 | 32.30 | 210.00 | 126 | 70.29 | 139.71 | 200.30 | 9.70 | 137.96 | -11.96 |
| 6 | P07 | 70.00 | 1.91 | 111.68 | -41.68 | 270.00 | 229 | 127.76 | 142.24 | 254.93 | 15.07 | 678.66 | -449.66 |
| 7 | P08 | 70.00 | 1.00 | 58.44 | 11.56 | 270.00 | 163 | 90.94 | 179.06 | 254.93 | 15.07 | 355.09 | -192.09 |
| 8 | P09 | 55.00 | 0.61 | 35.57 | 19.43 | 240.00 | 331 | 184.66 | 55.34 | 200.30 | 39.70 | 216.12 | 114.88 |
| 9 | P10 | 75.00 | 0.43 | 25.15 | 49.85 | 270.00 | 374 | 208.65 | 61.35 | 273.14 | -3.14 | 152.86 | 221.14 |
| 10 | P11 | 75.00 | 0.68 | 39.91 | 35.09 | 290.00 | 316 | 176.30 | 113.70 | 273.14 | 16.86 | 242.49 | 73.51 |
| 11 | P12 | 75.00 | 0.59 | 34.40 | 40.60 | 260.00 | 254 | 141.71 | 118.29 | 273.14 | -13.14 | 209.03 | 44.97 |
| 12 | P13 | 87.50 | 1.00 | 58.70 | 28.80 | 310.00 | 411 | 229.30 | 80.70 | 318.66 | -8.66 | 356.68 | 54.32 |
| 13 | P14 | 70.00 | 2.27 | 132.67 | -62.67 | 240.00 | 944 | 526.65 | -286.65 | 254.93 | -14.93 | 806.18 | 137.82 |
| 14 | P15 | 75.00 | 0.45 | 26.26 | 48.74 | 270.00 | 352 | 196.38 | 73.62 | 273.14 | -3.14 | 159.59 | 192.41 |
| 15 | P16 | 75.00 | 1.01 | 59.31 | 15.69 | 290.00 | 535 | 298.47 | -8.47 | 273.14 | 16.86 | 360.41 | 174.59 |
| 16 | P17 | 80.00 | 1.60 | 93.30 | -13.30 | 270.00 | 445 | 248.26 | 21.74 | 291.34 | -21.34 | 566.97 | -121.97 |

## Procentní odchylky od regresí

Procentní odchylka je (cílová hodnota − regresní predikce) / regresní predikce × 100. Kladná hodnota znamená, že cíl je vyšší než predikce; záporná hodnota znamená, že je nižší.

| Číslo řádku | Task | K1 % | K2 % | K3 % | K4 % |
|---:|---|---:|---:|---:|---:|
| 1 | P02 | 20.4 | -25.3 | 4.8 | 81.5 |
| 2 | P03 | 142.3 | 48.4 | -10.8 | 56.5 |
| 3 | P04 | 44.1 | 2.2 | 9.8 | 66.4 |
| 4 | P05 | 49.5 | 40.7 | -7.3 | 5.8 |
| 5 | P06 | 142.3 | 198.7 | 4.8 | -8.7 |
| 6 | P07 | -37.3 | 111.3 | 5.9 | -66.3 |
| 7 | P08 | 19.8 | 196.9 | 5.9 | -54.1 |
| 8 | P09 | 54.6 | 30.0 | 19.8 | 53.2 |
| 9 | P10 | 198.2 | 29.4 | -1.1 | 144.7 |
| 10 | P11 | 87.9 | 64.5 | 6.2 | 30.3 |
| 11 | P12 | 118.0 | 83.5 | -4.8 | 21.5 |
| 12 | P13 | 49.1 | 35.2 | -2.7 | 15.2 |
| 13 | P14 | -47.2 | -54.4 | -5.9 | 17.1 |
| 14 | P15 | 185.6 | 37.5 | -1.1 | 120.6 |
| 15 | P16 | 26.5 | -2.8 | 6.2 | 48.4 |
| 16 | P17 | -14.3 | 8.8 | -7.3 | -21.5 |

Nejvyšší absolutní odchylky: K1 P10 +198.2 %, K2 P06 +198.7 %, K3 P09 +19.8 %, K4 P10 +144.7 %.

## Detailní tabulka

Tabulka obsahuje pouze P02–P17. Čas je v minutách. Skutečný čas je odhad od nejstaršího filesystemového birthtime mezi nově přidanými soubory (Git status A) do implementačního commitu. Filesystemový birthtime je lokální časový proxy údaj. V této nepřerušené dávce je použitelný pro odhad průběžného času tasku, ale není uložený v Gitu a nemusí být přenositelný mezi checkouty.

| Číslo řádku | Task | Název | Odhad čas min | Odhad čas max | Odhad řádky min | Odhad řádky max | Skutečný čas min | Skutečné řádky |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | P02 | engine-kontrakt-a-registr | 40 | 70 | 160 | 260 | 0.78 | 504 |
| 2 | P03 | basic-engine | 60 | 100 | 200 | 320 | 0.56 | 314 |
| 3 | P04 | engine-checkpoint | 45 | 75 | 180 | 300 | 0.71 | 421 |
| 4 | P05 | legacy-xhtml-bridge | 60 | 100 | 200 | 340 | 0.92 | 344 |
| 5 | P06 | job-volba-modulu | 40 | 70 | 160 | 260 | 0.39 | 126 |
| 6 | P07 | worker-engine-dispatch | 50 | 90 | 200 | 340 | 1.91 | 229 |
| 7 | P08 | gui-cli-volba-modulu | 50 | 90 | 200 | 340 | 1.00 | 163 |
| 8 | P09 | semantic-batch-planner | 40 | 70 | 180 | 300 | 0.61 | 331 |
| 9 | P10 | json-glossary-store | 55 | 95 | 200 | 340 | 0.43 | 374 |
| 10 | P11 | bounded-memory-context | 55 | 95 | 220 | 360 | 0.68 | 316 |
| 11 | P12 | contextual-provider-port | 55 | 95 | 200 | 320 | 0.59 | 254 |
| 12 | P13 | advanced-standard-engine | 65 | 110 | 240 | 380 | 1.00 | 411 |
| 13 | P14 | managed-memory-tools | 50 | 90 | 180 | 300 | 2.27 | 944 |
| 14 | P15 | agent-backend-port | 55 | 95 | 200 | 340 | 0.45 | 352 |
| 15 | P16 | bounded-agent-session | 55 | 95 | 220 | 360 | 1.01 | 535 |
| 16 | P17 | standard-acceptance-benchmark | 60 | 100 | 200 | 340 | 1.60 | 445 |

### Komentáře k řádkům

1. [1] P02 — commit d34556c6; nejstarší nový soubor: src/doctranslate/translation/contracts.py; src/doctranslate/translation/__init__.py; birthtime 2026-10-11 04:02:31 015 UTC<br>src/doctranslate/translation/contracts.py; birthtime 2026-10-11 04:02:25 113 UTC<br>src/doctranslate/translation/registry.py; birthtime 2026-10-11 04:02:31 012 UTC<br>test/test_translation_registry.py; birthtime 2026-10-11 04:02:37 424 UTC; feat: add translation engine contracts and registry
2. [2] P03 — commit 7f34f124; nejstarší nový soubor: src/doctranslate/translation/basic.py; src/doctranslate/translation/basic.py; birthtime 2026-10-11 04:03:37 109 UTC<br>test/test_basic_translation_engine.py; birthtime 2026-10-11 04:03:50 069 UTC; feat: add basic translation engine
3. [3] P04 — commit 9a3e7b1b; nejstarší nový soubor: src/doctranslate/translation/checkpoint.py; src/doctranslate/translation/checkpoint.py; birthtime 2026-10-11 04:04:35 261 UTC<br>test/test_translation_checkpoint.py; birthtime 2026-10-11 04:04:47 541 UTC; feat: add versioned translation checkpoints
4. [4] P05 — commit 264d879d; nejstarší nový soubor: src/doctranslate/integration/translation_bridge.py; src/doctranslate/integration/__init__.py; birthtime 2026-10-11 04:05:44 084 UTC<br>src/doctranslate/integration/translation_bridge.py; birthtime 2026-10-11 04:05:44 079 UTC<br>test/test_translation_bridge.py; birthtime 2026-10-11 04:05:53 348 UTC; feat: add legacy translation bridge
5. [5] P06 — commit add7d853; nejstarší nový soubor: test/test_translation_job_selection.py; test/test_translation_job_selection.py; birthtime 2026-10-11 04:07:39 700 UTC; feat: persist translation engine selection per job
6. [6] P07 — commit 51237432; nejstarší nový soubor: test/test_translation_worker.py; test/test_translation_worker.py; birthtime 2026-10-11 04:09:26 381 UTC; feat: dispatch translation engines from worker
7. [7] P08 — commit d195ecbe; nejstarší nový soubor: test/test_translation_selection_ui.py; test/test_translation_selection_ui.py; birthtime 2026-10-11 04:13:33 028 UTC; feat: expose translation module selection
8. [8] P09 — commit a2bd5534; nejstarší nový soubor: src/doctranslate/translation/planning.py; src/doctranslate/translation/planning.py; birthtime 2026-10-11 04:15:11 500 UTC<br>test/test_translation_planning.py; birthtime 2026-10-11 04:15:24 896 UTC; feat: add semantic translation batch planner
9. [9] P10 — commit 5f131f4b; nejstarší nový soubor: src/doctranslate/translation/memory.py; src/doctranslate/translation/memory.py; birthtime 2026-10-11 04:16:18 184 UTC<br>test/test_translation_memory.py; birthtime 2026-10-11 04:16:26 810 UTC; feat: add revisioned JSON glossary store
10. [10] P11 — commit 28cfca14; nejstarší nový soubor: src/doctranslate/translation/retrieval.py; src/doctranslate/translation/context.py; birthtime 2026-10-11 04:17:09 048 UTC<br>src/doctranslate/translation/retrieval.py; birthtime 2026-10-11 04:17:09 046 UTC<br>test/test_translation_context.py; birthtime 2026-10-11 04:17:16 406 UTC; feat: add bounded translation context retrieval
11. [11] P12 — commit be873759; nejstarší nový soubor: src/doctranslate/ai/context_backend.py; src/doctranslate/ai/context_backend.py; birthtime 2026-10-11 04:18:16 697 UTC<br>test/test_contextual_backend.py; birthtime 2026-10-11 04:18:35 323 UTC; feat: add contextual Ollama provider port
12. [12] P13 — commit d5c02784; nejstarší nový soubor: src/doctranslate/translation/advanced.py; src/doctranslate/translation/advanced.py; birthtime 2026-10-11 04:19:39 760 UTC<br>test/test_advanced_translation_engine.py; birthtime 2026-10-11 04:20:01 032 UTC; feat: add standard advanced translation engine
13. [13] P14 — commit d24e1a87; nejstarší nový soubor: src/doctranslate/translation/tools.py; src/doctranslate/translation/tools.py; birthtime 2026-10-11 04:22:23 843 UTC<br>test/test_translation_tools.py; birthtime 2026-10-11 04:23:14 519 UTC; feat: add managed translation memory tools
14. [14] P15 — commit a8ec5a5a; nejstarší nový soubor: test/test_agent_backend.py; test/test_agent_backend.py; birthtime 2026-10-11 04:25:32 047 UTC; feat: add validated agent backend turns
15. [15] P16 — commit d356777a; nejstarší nový soubor: src/doctranslate/translation/session.py; src/doctranslate/translation/session.py; birthtime 2026-10-11 04:26:31 130 UTC<br>test/test_translation_session.py; birthtime 2026-10-11 04:26:52 635 UTC; feat: add bounded translation agent session
16. [16] P17 — commit d4056832; nejstarší nový soubor: test/test_translation_engine_integration.py; test/test_translation_engine_integration.py; birthtime 2026-10-11 04:28:26 244 UTC; test: add translation engine acceptance benchmark

## Co se z toho učíme

1. Původní časové odhady byly systematicky příliš vysoké pro izolované implementační tasky provedené v jednom rychlém průchodu. Nelze je ale bez dalšího ztotožnit s čistým časem práce, protože mezi commity nejsou zachyceny všechny činnosti.
2. Řádkové odhady byly užitečnější než časové, ale jejich porovnání s Git diffem je zatíženo testy, dokumentací, task metadata a přidáváním nových souborů.
3. Největší odchylky rozsahu vznikly u P02, P04, P13, P14 a P16. U těchto tasků je vhodné příště rozlišit rozhraní, implementaci, testy a dokumentaci; jeden souhrnný řádkový odhad je málo informativní.
4. P01 a P06 byly menší než odhad. U mechanických napojení a malých oprav nepoužívat automaticky hodinové minimum 40–60 minut.
5. P14 ukazuje, že nástroje s validací schémat a testy mohou být výrazně větší než základní doménový kód, i když se chování zdá jednoduché.

## Odhadování 1.0 – dosavadní kandidátní model simple-v1

Dosavadní návrh k 2026-10-11 je zachován jako kandidát pro porovnání s kompromisním postupem výše. Není finálním návodem. Numerické váhy ani vhodnost modelu pro běžné zadávání dosud nejsou ověřené; další práce je odložená.

Analýza má přirozeně popsat požadované chování, kontrakty, návaznosti a ověření. Nevytvářet další entity, properties, zprávy nebo diagramy jen pro odhad. Z běžné analýzy se převezmou dva údaje:

| Parametr | Význam | Jak jej získat |
|---|---|---|
| N | Počet požadovaných samostatně ověřitelných změn chování nebo datového kontraktu | výsledky výslovně popsané v zadání/analýze, například registrovat, vypsat a vytvořit = 3 |
| B | Počet dotčených integračních hranic se změnou kontraktu nebo toku | konkrétní návaznosti komponent, například GUI → fronta a worker → provider = 2 |

Počítat změnu jednou, i když ji popisuje více odstavců či diagramů. Pole jednoho měněného datového kontraktu se nezapočítávají jako samostatná N. Nevytvářet nové rozdělení jen pro zvýšení/snížení počtu. B je počet skutečně měněných návazností, ne počet souborů, volání nebo všech existujících komponent.

Složitost (například souběh, crash recovery, neznámý protokol nebo rozsáhlé mapování) uvést stručně do předpokladů a důvodů nejistoty. První verze ji nepřevádí na další číselné skóre. Pokud takové tasky budou soustavně vybočovat, data rozhodnou o samostatné kategorii či přidání jedné metriky.

Tyto dva parametry byly vybrány pro snadné získání z analýzy. Historická data jejich statistickou významnost zatím nedokazují, protože N/B nebyly zaznamenané.

### Vzorce a výchozí konstanty 1.0

    W = wN × N + wB × B
    L = k × W
    T_work = a + L / v + g × B
    T_elapsed = T_work + T_wait

L jsou fyzické přidané + odstraněné řádky kódu, testů a potřebné dokumentace dohromady. Mechanické přesuny a generovaná data vykazovat zvlášť. Logické řádky pro velikost review jsou samostatný odhad. T_wait zahrnuje pouze čekání nad obvyklé krátké testy/review, které už obsahuje profil.

Výchozí návrhové váhy: wN = 60 řádků na změnu, wB = 40 řádků na měněnou hranici. Zahrnují obvyklou implementaci, testy a stručnou dokumentaci. Nejsou fitované z historických dat. k je korekce rozsahu podle profilu, a jednorázová režie tasku, v rychlost, g dodatečné integrační ověření nad běžnou validaci.

| Profil | k | a min | v ř./min | g min/hranici | Stav konstant |
|---|---:|---:|---:|---:|---|
| codex-history-initial | 1 | 0 | 220 | 0.25 | pouze v vychází z historického průchodu; ostatní návrhové |
| human-python-initial | 1 | 5 | 8 | 5 | všechny návrhové pro zkušeného vývojáře ve známém projektu |
| new-agent-pilot | nezjištěno | nezjištěno | nezjištěno | nezjištěno | změřit na pilotních taskách, například pro Qwen |

Codex v ≈ 220 vychází z 6063 diff řádků / 27.62 min celého průchodu P02–P17. Součet jejich kratších filesystemových proxy časů je jen 14.91 min a nevystihuje celý průchod. Přesný historický model/backend není doložen; profil je startovní prior, nikoli univerzální rychlost všech verzí Codexu.

Člověk má vlastní počáteční profil; jeho čas se neodvozuje násobením času agenta. Nový agent přebírá inventář N/B, nikoli automaticky rychlost Codexu. Fingerprint a revize profilu zahrnují implementátora/model, nástroje, prostředí, konvence a rozsah validace.

### Tabulka v tasku a krátký příklad

| Parametr | Počet | Zdroj v zadání/analýze |
|---|---:|---|
| N | 3 | registrovat / vypsat / vytvořit |
| B | 1 | nově měněné napojení volajícího na registr |

W = 60 × 3 + 40 × 1 = 220. Při k = 1: L = 220 řádků; Codex T_work = 220/220 + 0.25 = 1.25 min; člověk T_work = 5 + 220/8 + 5 = 37.5 min. Jde o ilustraci výpočtu s výchozími konstantami.

Stačí odkázat na existující analýzu, uvést N/B s jejich zdrojem, profil/revizi, řádky a čas, předpoklady a ověření. Nevyžaduje se tabulka všech kandidátních metrik. Tokeny uvést podle dostupných dat, jinak unavailable s důvodem; nejsou dalším vstupem tohoto modelu.

Pro známou mikroopravu několika konkrétních řádků lze použít method=known-diff s přímým odhadem změny a jejího testu; univerzální váha 60 řádků by byla zavádějící. Čistá dokumentace a mechanické změny nemají být násilně převedeny na změny chování N.

### Postup použití a nejasné zadání

1. Přečíst běžnou analýzu a acceptance. Z ní vyčíst N/B; pokud to jde, nepřidávat další analytickou práci.
2. Pokud nelze určit požadované výsledky, hranice změny nebo jejich ověření, dopracovat právě tuto mezeru. Nejasnost zadání nezakrývat odhadovacími kategoriemi ani velkou rezervou.
3. Zapsat odhad před implementací: method=simple-v1, scope/analysis reference, N/B, profil, L a T_work/T_wait. Dělit task podle chování, nikoli pro dosažení určitého N.
4. Dokud chybějí vlastní validační chyby, uvést plánovací pásmo L = 0.5–2.0 × střed a interval v: Codex 110–330, člověk 4–12 ř./min. Jsou to výchozí rezervy, nikoli statistické intervaly. Pokud je užší/širší pásmo zdůvodněné konkrétním zadáním, důvod zapsat.
5. Časový interval spočítat stejným vzorcem z krajních L/v; nesčítat znovu tutéž rezervu za složitost. Neznámé dlouhé čekání uvést zvlášť.
6. Po akceptaci doplnit skutečný scope-filtered diff, čas práce/ověření, extra wait, retries a změny scope. Zachovat původní odhad.

Chybějící kalibrace implementátora je samostatná nejistota profilu. Pokud je zadání jasné, může pilot použít výslovně označený předběžný profil; nezjištěné konstanty se nedosazují jako nuly.

### Kalibrace jednoduchého modelu

1. Na prvních 5–10 reálných taskách zaznamenat N/B z původní analýzy před implementací, skutečné L a celý T_work. Měřit od nutného načtení kontextu do dokončení testů/review; přerušení a extra wait oddělit. Scope change a neúspěchy uchovat.
2. Nejprve fixovat wN/wB a fitovat jedinou korekci: k = sum(W_i × L_i) / sum(W_i²). Při nulovém jmenovateli nelze fit provést. Nedosazovat staré 1/K2; starý odhad a nový W jsou odlišné prediktory.
3. Pro první časový profil fitovat v = sum(L_i) / sum(T_work_i) a v této agregované variantě použít a=g=0, aby se režie nezapočítala podruhé. Alternativně ponechat zdůvodněné a/g a fitovat na zbytkovém čase; tuto volbu uvést.
4. Až bude dost nezávislých dat s různým N/B, lze fitovat přímo L = pN × N + pB × B nezápornou regresí. Pak nastavit k=1; nefittovat zároveň pN/pB a další globální k bez fixace měřítka. Pokud N a B rostou vždy spolu, ponechat jejich poměr a kalibrovat pouze k.
5. Později lze obdobně fitovat T_work = a + beta × L + g × B, v = 1/beta. Orientačně 10 měření na volný koeficient, s nezápornými koeficienty. Zpočátku nejsou pro všechny parametry současně data.
6. Ověřit na pozdějších taskách nebo vynechané celé dávce. Čas předpovídat s odhadnutými řádky, nikoli pouze se skutečnými. Evidovat absolutní chybu v řádcích/minutách, medián procentní chyby a pokrytí pásma; u nulových či velmi krátkých časů používat absolutní chybu.
7. Koeficienty vydat s revizí, fingerprintem, zdrojovými tasky a výsledkem validace. Pro nový model/agenta opakovat pilot; pro člověka používat jeho vlastní měření. Srovnávat jen akceptovanou kvalitu a obdobný rozsah testování.
8. Další metriku z kandidátního seznamu přidat pouze při opakované nevysvětlené chybě a doloženém zlepšení na validačních taskách. Informace musí už existovat v běžné analýze; náklady na její získání musí být přiměřené.

Dosavadní historie umožňuje převzít přibližnou rychlost a diagnostiku starých odhadů. Váhy N/B a jejich pořadí významnosti z ní zatím určit nelze bez nezávislé anotace původních zadání. Podrobný návrh níže není povinnou součástí běžného tasku.

## Podrobný návrh parametrů – kandidáti pro další verze

Stav: zachovaný podrobný návrh kandidátních metrik, 2026-10-11. Není povinnou součástí tasků; simple-v1 i kompromisní postup výše jsou pracovní návrhy k budoucímu porovnání. Následující vzorce, profily a tabulky popisují možnost podrobnějšího rozboru, pokud jej pozdější měření odůvodní. Historické tabulky výše zůstávají auditním podkladem. Výchozí váhy strukturálních parametrů jsou navržené; historická data umožňují kalibrovat jen souhrnný rozsah a rychlost. Neobsahují původně zaznamenané počty entit, polí a pravidel.

Cíl: ze stejného zadání, stejného inventáře změn a stejné verze profilu získat stejný výsledek. Každé číslo musí mít dohledatelný seznam položek. Odhad se zapisuje před implementací, následná změna scope jako další revize.

### Podklady pro případný podrobný rozbor

Analýza nebo architektonický návrh dotčené části musí před odhadem obsahovat parametry rozsahu v některé dohledatelné formě: strukturovaný text, tabulku, seznam kontraktů/polí/pravidel, datové schéma nebo diagram. UML není nutnou vstupní podmínkou odhadu každého tasku. Požadavek na UML pro centrální high-level architekturu aplikace tím není změněn.

Minimální podklady podle relevance: dotčené komponenty a jejich odpovědnosti, nové/měněné kontrakty a pole, operace a datový tok, pravidla a chybové stavy, algoritmy a limity, acceptance scénáře, reuse a závislosti. U malé lokální opravy stačí popsat konkrétní symbol, změnu pravidla a ověření. Nevytvářet další diagram jen kvůli počítání parametrů.

Postup před implementací:

1. Z požadavku určit cílové chování a hranice změny; dopracovat analýzu dotčené části.
2. Vypsat položky relevantních metrik s ID a zdrojem. Nerelevantní metriky označit ověřenou nulou, nejisté počty intervalem a jeho důvodem.
3. Ověřit, že acceptance a kontrakty umožňují sestavit inventář a spočítat odhad. Stejná informace z analýzy a diagramu se nezapočítá dvakrát.
4. Nelze-li zdůvodnit rozsah, označit estimate.readiness = needs-analysis, zapsat konkrétní mezery a dopracovat zadání. Nejasnost nezakrývat hodinovým minimem ani velkou procentní rezervou. Případný samostatný discovery task musí mít vlastní jasný výsledek a acceptance.
5. Jakmile jsou podklady dostatečné, uložit jejich revizi, tabulku parametrů a odhad. Teprve potom zahájit závislou implementaci; na nezávislých jasně popsaných částech lze pokračovat.

Nejistota výsledné pracnosti zůstává běžná i u jasného zadání. Chybějící kalibrace nového agenta se eviduje jako estimate.readiness = needs-calibration; neznamená sama o sobě nejasný scope. Inventář může být hotový a odhad používat výslovně označený předběžný profil. estimate.readiness není stav issue a nemění slovník created/progress/test/done.

### 1. Co se odhaduje

- L_code, L_test, L_doc: fyzické přidané a odstraněné řádky v příslušné kategorii. L_total je jejich součet. Toto je jednotka, kterou lze přímo měřit Git numstat.
- Logické/substantivní řádky se vedou zvlášť pro review a dělení tasků. Neporovnávat je přímo s fyzickým Git diffem.
- T_work: práce implementátora včetně porozumění, implementace, review a obvyklé lokální validace.
- T_wait: čekání navíc, například dlouhý benchmark, instalace nebo externí služba. Obvyklé krátké testy jsou již součástí rychlosti profilu.
- T_elapsed = T_work + T_wait pro jeden sériově pracující subjekt bez překryvu. Čekání na uživatele a přerušení evidovat samostatně, nepoužívat ke kalibraci.
- S_code/S_test/S_doc: kalibrační násobitele rozsahu podle implementátora a jeho konvencí. Rozsah lidské a agentní implementace nemusí být stejný.

Velikost vstupního dokumentu, zprávy v bajtech a asymptotická složitost algoritmu ovlivňují runtime aplikace. Samy neurčují počet implementačních řádků. Implementační rozsah zvyšuje konkrétní požadavek na streaming, dělení, index, retry nebo ochranu limitu.

### 2. Inventář změn a pravidla počítání

Počítat pouze novou nebo měněnou část tasku, nikoli celý návrh. Autoritativním zdrojem je dopracovaná analýza/návrh a acceptance; diagram je jednou z možných forem jejich zápisu. Každá položka má ID a odkaz na její definici. Stejná položka opakovaná v textu, tabulce nebo diagramu se započte jednou.

| ID | Parametr | Jednotka a jednoznačné pravidlo | Výchozí váha |
|---|---|---|---:|
| E_n | Nové entity | nová třída, datový typ nebo veřejné rozhraní s vlastní odpovědností; ne reference na existující službu | 8 |
| E_m | Měněné entity | existující typ se změněným veřejným kontraktem; entitu započtenou do E_n zde neopakovat | 4 |
| P | Properties / pole | nové nebo významově měněné pole v jedinečné definici schématu; ne počet jeho použití | 2 |
| O_n | Nové operace | nový veřejný vstup, handler nebo samostatná transformační operace s vlastní acceptance | 12 |
| O_m | Měněné operace | změna chování existující operace; nejde o počet všech mechanicky upravených volajících | 4 |
| M | Zprávové kontrakty | nové nebo měněné jedinečné request/response/event schéma; stejná zpráva v loop se nepočítá opakovaně | 8 |
| N | Vnořená struktura | jedinečná úroveň list/map/union s vlastním mapováním; primitivní pole již patří do P | 4 |
| R_s | Jednoduchá pravidla | jedna lokální podmínka, default nebo přímá validace jednoho údaje | 4 |
| R_m | Kombinovaná pravidla | pravidlo spojuje více údajů nebo provádí lokální stavový přechod | 10 |
| R_c | Provázaná pravidla | invariant přes persistenci/souběh, idempotenci, crash recovery nebo více komponent | 24 |
| A_s | Jednoduché algoritmy | přímá transformace nebo průchod jednou kolekcí bez interakce pravidel | 8 |
| A_m | Střední algoritmy | řazení/ranking, segmentace nebo několik závislých fází s definovanými hranicemi | 24 |
| A_c | Složité algoritmy | nový stavový plánovač, reconciliation nebo optimalizace s provázanými rozhodnutími | 60 |
| X | Konverzní mapování | jedinečná dvojice rozdílných datových schémat, například legacy → canonical; opačný směr je další mapování | 12 |
| Q | Testovací scénáře | samostatná pozitivní/negativní/hraniční acceptance s vlastním očekávaným výsledkem | 12 |
| H | Nová testovací infrastruktura | nový fake/fixture/transport s vlastní logikou; několik hodnot stejného fixture není více H | 20 |
| D | Dokumentační jednotky | jeden nový/měněný diagram, sekce manuálu nebo tasková evidence; docstringy patří do kódu | 10 |
| F_c / F_t / F_d | Soubory změny | obsahově měněné soubory kódu/testů/dokumentace; pouhý přesun vynechat, F je jejich součet | 3 |

Váhy jsou počáteční řádky na jednotku, nikoli výsledky regrese. Zahrnují obvyklé formátování Pythonu a stručné komentáře. Mechanicky generované nebo přesunuté řádky G vykazovat zvlášť a nepoužívat je jako měřítko produktivity.

Pravidlo rozkladu: O počítá kostru a vstup operace, A její řídicí algoritmus, R jednotlivá rozhodnutí. Stejné rozhodnutí nemůže být zároveň samostatné R a další A. Sdílený validator se počítá jednou, různé podmínky jeho použití jako konkrétní R. M počítá obálku/protokol; pole zprávy se počítají v P pouze v její jedinečné definici. Q počítá scénář jednou i při více parametrických hodnotách; významově odlišný očekávaný výsledek je další scénář.

### 3. Velikost a složitost zpráv

Pro každý M vést: počet polí, vnoření, počet variant, maximální bajty/tokeny, směr, transport a zdroj limitu. Například request má 8 polí, 2 vnořené struktury a limit 64 KiB: P += 8, N += 2, M += 1. Kontrola limitu přidá R a negativní Q. Pouhé zvětšení limitu na 128 KiB bez změny algoritmu nepřidá nové entity ani další M.

Pro každý algoritmus uvést ID, vstupy/výstupy, grade s/m/c, počet souvisejících R, očekávaný rozsah dat a časovou/paměťovou složitost. O(n log n) není automaticky složitější implementace než O(n); grade hodnotí počet závislých rozhodnutí a požadované invarianty.

Doplňkové časové parametry:

| ID | Parametr | Pravidlo |
|---|---|---|
| B | Integrační hranice | jedinečná měněná hranice komponent, procesu nebo externího API vyžadující samostatné ověření; ne každá šipka či opakované volání |
| Z | Obtížná rozhodnutí | Z = R_c + A_c; dodatečný čas na návrh/review nad náklady na zápis řádků |
| U | Neověřené předpoklady | konkrétní neznámý kontrakt, dostupnost nástroje nebo nepopsaná migrace; každý má otázku a ověřovací krok |

U není náhrada za neurčité zadání. Pokud nelze určit cílové chování, task se označí jako neodhadnutelný do vyjasnění a samostatně se odhadne discovery. B a Z nemají další vliv na řádky, které už popisují strukturální parametry.

### 4. Vzorce rozsahu

Použít váhy z tabulky a uložit jejich verzi:

    W_code = 8E_n + 4E_m + 2P + 12O_n + 4O_m + 8M + 4N
             + 4R_s + 10R_m + 24R_c + 8A_s + 24A_m + 60A_c + 12X + 3F_c
    W_test = 12Q + 20H + 3F_t
    W_doc  = 10D + 3F_d
    L_code = S_code × W_code
    L_test = S_test × W_test
    L_doc  = S_doc × W_doc
    L_total = L_code + L_test + L_doc

Výchozí S_code = S_test = S_doc = 1. Toto je návrhový prior. Až budou k dispozici rozdělená měření, násobitele upravit podle implementátora. Pro přesuny, generovaná data a čistě mechanickou změnu uvést G a zvláštní časový odhad podle konkrétní operace; G nepřidávat do L_total.

Známou malou opravu je možné místo velkého inventáře odhadnout podle konkrétního diffu a testu. Označit method=known-diff; nevymýšlet entity, aby se zaplnila tabulka.

### 5. Vzorce času a profily implementátorů

    T_work = a + L_total / v + bB + cZ + dU
    T_elapsed = T_work + T_wait

a je jednorázová režie tasku v minutách, v změněné fyzické řádky za minutu, b/c/d minuty na příslušnou jednotku. v zahrnuje běžné review a krátkou validaci; externí čekání navíc patří do T_wait. Nerovná se rychlosti psaní na klávesnici ani rychlosti generování tokenů.

| Profil v1 | S_code/test/doc | a min | v ř./min | b min/B | c min/Z | d min/U |
|---|---:|---:|---:|---:|---:|---:|
| codex-history-2026-10-11 | 1/1/1 | 0 | 220 | 0.25 | 0.5 | 1 |
| human-python-initial | 1/1/1 | 5 | 8 | 5 | 3 | 15 |
| new-agent-pilot | 1/1/1 | nezjištěno | nezjištěno | nezjištěno | nezjištěno | nezjištěno |

Codex: pouze v = přibližně 220 je podloženo celým historickým průchodem. a = 0 je volba agregovaného modelu; ostatní konstanty jsou výchozí návrhy k pozdější kalibraci. Přesná identita původního modelu/backendu není v této tabulce doložena; profil nelze vydávat za univerzální rychlost všech verzí ChatGPT Codex ani Luny. Použít jej jako startovní prior pro srovnatelný připravený sériový průchod, a následně přeměřit aktuální model.

Člověk: všechny konstanty jsou počáteční plánovací předpoklady pro zkušeného Python vývojáře ve známém projektu. Výchozí pásmo v je 4–12 ř./min; zahrnuje kód, testy a dokumentaci. Nejsou odvozené z výkonu Codexu. a se účtuje za samostatně zahajovaný task, ne opakovaně za každý krátký krok během téhož tasku.

Nový agent, například Qwen: nejprve pilotní kalibrace. Hodnoty nezjištěno nejsou nuly. Pro předběžný plán lze výslovně použít cizí profil s označením borrowed=true, avšak ne tvrdit, že jde o jeho změřený výkon.

Profile fingerprint obsahuje implementátora, model/verzi/digest pokud je dostupný, nastavení reasoning, backend a nástroje, stroj, jazyk/konvence, rozsah testování, datum a verzi vah. Výrazná změna kterékoliv relevantní části vytvoří novou revizi profilu. U člověka uvést zkušenost/projektovou znalost; údaje o GPU nebo backendu nejsou potřeba.

U jednoho parentu se sčítají leafy. Sdílené schéma/fixture dostane jediného vlastníka, ostatní tasky počítají pouze napojení. Je-li plán sériový, časy se sčítají; pro skutečnou paralelní práci použít dependency/critical path a oddělit effort od elapsed.

### 6. Co skutečně umožňuje historická kalibrace

P02–P17: 16 pozorování, 6063 diff řádků, součet středů původních řádkových odhadů 4170. Pro výpočty níže byly použity zobrazené hodnoty detailní tabulky, proto se drobně liší od fitů z původních nezaokrouhlených časů.

| Výpočet | Hodnota | Použití |
|---|---:|---|
| souhrnný L_actual / L_old | 1.453957 | popis starého podhodnocení rozsahu |
| dopředný fit L_actual = k × L_old | 1.435568 | nouzová korekce starého odhadu stejného typu |
| převrácený dřívější K2 | 1.792448 | převrácení opačné regrese, není dopředný fit |
| součet proxy časů tasků | 14.91 min | neúplný čas od prvního přidaného souboru |
| celý průchod od prvního nového souboru po poslední commit | 27.62 min | agregovaný end-to-end proxy |
| 6063 / 27.62 | 219.514844 ř./min | startovní v ≈ 220 pro codex-history |
| diagnostický fit T_proxy = a + b × L_actual | a = 0.302687; b = 0.0016604 | popis neúplných proxy časů, nepoužívat pro celý task |
| leave-one-out MAE tohoto časového fitu | 0.415489 min | chyba mimo vždy jeden vynechaný task, stále jen vůči proxy času |

Inverze K4 = 355.26 ř./min také není správný dopředný fit pro T z L. Parametr v proto nově odvozujeme z celého průchodu, nikoli překlápěním jednotlivých regresí.

Dopředná korekce starých řádkových odhadů má medián absolutní procentní chyby přibližně 20.53 % na tréninkových datech. Poměr skutečnost/predikce má empirické P10 ≈ 0.51 a P90 ≈ 1.48; jde o diagnostiku starého odhadu, ne interval nové parametrické metody. P14 má navíc rozšířený scope: původně šest nástrojů, později i accept/reject a další CAS/evidence. Takový task nelze použít pro přesnou kalibraci původního scope bez oddělení rozšíření.

Pro nový W není z historie zatím kalibrované S. Násobitel 1.435568 se NESMÍ automaticky aplikovat na W: W a starý intuitivní L_old jsou různé prediktory. Nejprve je třeba anotovat původní frozen zadání a spočítat W bez znalosti výsledného diffu. Nelze zpětně dopočítat počty parametrů tak, aby odpovídaly požadovanému výsledku.

### 7. Volitelná tabulka při zvoleném podrobném rozboru

Použít jednu společnou tabulku pro všechny profily. Každý parametr má počty min/střed/max a dohledatelné ID položek. P = 0 znamená ověřeně žádná změna pole; ? znamená neznámý počet. Neznámý údaj nedosazovat jako nulu.

| Parametr | Min | Střed | Max | Položky / zdroj zadání |
|---|---:|---:|---:|---|
| E_n / E_m |  |  |  | typy z analýzy/kontraktů nebo classDiagram |
| P |  |  |  | pole každého dotčeného typu |
| O_n / O_m |  |  |  | veřejné operace/handlery |
| M / N |  |  |  | inventory jedinečných zpráv a vnoření |
| R_s / R_m / R_c |  |  |  | pravidla R01… s grade |
| A_s / A_m / A_c |  |  |  | algoritmy A01… s grade a runtime limity |
| X |  |  |  | konkrétní mapování schémat |
| Q / H |  |  |  | acceptance scénáře a nové fakes |
| D / F_c / F_t / F_d |  |  |  | dokumentační jednotky a soubory podle kategorií |
| B / Z / U |  |  |  | hranice, obtížná rozhodnutí, otevřené předpoklady |

Při výpočtu jsou zápisy s lomítkem samostatné počty, například E_n=2; E_m=1, nikoli jeden jejich součet. Task uvede také velikost zpráv a její jednotku, vlastnictví sdílených částí, dependencies, validation command a výsledek každého subtasku.

Výstup odhadu:

    estimate.method: parametric-v1
    estimate.weights_revision: v1
    estimate.scope_revision: <revize zadání>
    estimate.analysis_reference: <podklady a revize, UML není nutné>
    estimate.readiness: <ready / needs-analysis / needs-calibration>
    estimate.profile: <fingerprint + revize>
    estimate.rows_code/test/doc: <min, střed, max>
    estimate.rows_total_diff: <min, střed, max>
    estimate.logical_lines: <samostatný odhad pro review>
    estimate.time_work_min: <min, střed, max>
    estimate.time_wait_min: <min, střed, max + zdroj>
    estimate.time_elapsed_min: <min, střed, max>
    estimate.tokens: <měřený/odhadnutý kontext, nebo unavailable + důvod>
    estimate.assumptions: <konkrétní předpoklady a U>

Tokeny nejsou převodem řádků na čas. Pokud je nutný tokenový budget, spočítat známý vstup tokenizerem konkrétního modelu; výstup odhadnout z historických output_tokens/L daného profilu. Bez takových dat uvést unavailable nebo výslovně navržený prior, ne naměřené číslo.

### 8. Interval a důvěra

Nejprve spočítat W_min/W_mid/W_max z inventáře. Zde může skutečně chybět například 0–2 varianty zprávy; zapisuje se příčina, nikoli jen procento navíc.

Dokud nový model nemá vlastní rezidua, použít explicitní pracovní rezervu L_min = 0.7 × S × W_min, L_max = 1.5 × S × W_max a L_mid = S × W_mid. U neúplného zadání použít 0.5–2.0 a označit low confidence. Jde o výchozí plánovací pásma, nikoli statistické intervaly spolehlivosti. Nepočítat již stejnou rezervu podruhé v počtech.

Pro codex-history počáteční pásmo v = 110–330 ř./min; pro human-python-initial 4–12. Pak:

    T_min = a + L_min / v_max + bB_min + cZ_min + dU_min + T_wait_min
    T_mid = a + L_mid / v_mid + bB_mid + cZ_mid + dU_mid + T_wait_mid
    T_max = a + L_max / v_min + bB_max + cZ_max + dU_max + T_wait_max

Pokud čas externí operace neznáme, uvést tuto část jako unknown, odhad work stále zůstává použitelný. Po kalibraci pásma nahradit empirickými chybami předpovědi na odložených taskách. Zaokrouhlovat až konečný výstup, nikoli jednotlivé příspěvky; u agentů zachovat desetinné minuty.

### 9. Úplný ilustrační příklad

Jde o nové vzorové zadání malého registru, nikoli o zpětně kalibrovaný P02. Inventory: tři nové typy Options/Descriptor/Result s celkem osmi poli; operace register/list/create; dvě zprávové obálky request/result a jedna vnořená mapa; tři jednoduchá pravidla (povinné ID, default, limit), jedno kombinované pravidlo dostupnosti a jeden jednoduchý dispatch algoritmus. Šest scénářů: úspěch, duplicate, unknown, unavailable, invalid options a hraniční limit. Jeden nový fake, dvě dokumentační jednotky, tři soubory (F_c=1, F_t=1, F_d=1), jedna ověřovaná hranice, žádné R_c/A_c ani neznámý předpoklad.

| E_n | E_m | P | O_n | O_m | M | N | R_s | R_m | R_c | A_s | A_m | A_c | X | Q | H | D | F | B | Z | U |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0 | 8 | 3 | 0 | 2 | 1 | 3 | 1 | 0 | 1 | 0 | 0 | 0 | 6 | 1 | 2 | 3 | 1 | 0 | 0 |

W_code = 129, W_test = 95, W_doc = 23; L_mid = 247 při S=1. Stejné zadání dává při pracovních rezervách L_min = 172.9 a L_max = 370.5.

| Profil | T_min min | T_mid min | T_max min | Podklad |
|---|---:|---:|---:|---|
| codex-history | 0.77 | 1.37 | 3.62 | 247/220 + 0.25, v pásmu 110–330 |
| human-python-initial | 24.41 | 40.88 | 102.63 | 5 + 247/8 + 5, v pásmu 4–12 |

T_wait = 0 znamená žádné další čekání nad obvyklé krátké ověření. Tabulka není závazek aktuálního modelu; ukazuje opakovatelný výpočet. Přidání jednoho samostatného jednoduchého pravidla a jeho nového scénáře zvýší W o 4 + 12 = 16 řádků. Nový crash-recovery invariant s testem zvýší W o 24 + 12 a zároveň Z o 1.

### 10. Kalibrace nového profilu včetně Qwen

1. Před pilotem uložit fingerprint a verzi vah. Vybrat několik reálných samostatně reviewovatelných tasků různých velikostí, ne uměle generované řádky. Pro nový agentní backend nejprve ověřit jeho funkčnost dle platných orchestrace pravidel; tento dokument nic nespouští.
2. U každého tasku předem uzavřít inventář, scope, Q a kvalitu akceptace. Uchovat původní odhad. Po implementaci nevynechávat obtížné nebo neúspěšné tasky.
3. Měřit start před načítáním nutného kontextu; konec po testech a review. Agent: log/monotónní časovač orchestrátoru. Člověk: aktivní pracovní úseky plus samostatné čekání. Zapisovat zvlášť retries, tool failures, test time, externí wait a přerušení.
4. Sejmout diff proti předem zaznamenanému výchozímu stavu a filtrovat scope. Numstat rozdělit na code/test/doc/G, nezahrnovat cizí souběžné změny. Chybějící měření označit unknown. Scope change uvést samostatně a původní scope neporovnávat s rozšířeným diffem.
5. První 3–5 pilotů slouží pro přibližný profil: odhadnout jeden společný S a jednu rychlost v; ostatní koeficienty fixovat a označit prior. Nedělat regresi všech vah na tak malém vzorku.
6. Pro rozsah použít dopředný nezáporný fit přes počátek: S = sum(W_i × L_i) / sum(W_i²). Pokud jsou dostatečná code/test/doc měření, stejně fitovat S_code/S_test/S_doc zvlášť. Fit neprovádět při nulovém jmenovateli.
7. Pro agregovaný počáteční čas použít v = sum(L_i) / sum(T_work_i) na stejných taskách bez extra wait. Při tomto agregovaném fitu použít a=b=c=d=0; další režii do něj nepřidávat podruhé. Pokud potřebujeme nenulové b/c/d, odečítat před fitováním jejich zdůvodněné příspěvky a zaznamenat tuto volbu.
8. Až bude dost měření, fitovat dopředný T_work = a + beta × L + bB + cZ + dU s nezápornými koeficienty; v = 1/beta. Začít pouze a/beta. Další sloupec přidat, když má nezávislou variabilitu a zlepšuje validační chybu. Orientačně nejméně 10 měření na volný koeficient; kolineární parametry ponechat fixované nebo sloučit.
9. Samostatné váhy E/P/O/M/R/A fitovat až na větším anotovaném souboru, s nezáporným regularizovaným modelem a normalizovanou stupnicí. Neodhadovat současně všechny váhy a globální S bez fixace měřítka. Když dvě metriky vždy rostou spolu, data jejich účinek nerozliší.
10. Ověřit na pozdějších taskách nebo leave-one-batch-out; běžné train/test rozdělení uvnitř stejné dávky může sdílet infrastrukturu. U malé dávky používat leave-one-out jen jako diagnostiku a uvést přesně, co bylo vynecháno. Časový model ověřit také s PŘEDPOVĚZENÝM L, nikoli pouze se skutečnými řádky.
11. Zapsat MAE v minutách/řádcích, medián podepsané odchylky, medián absolutní procentní chyby a pokrytí plánovacích pásem. U nuly nebo velmi krátkého času použít absolutní chybu, procenta jsou nestabilní. Koeficient přijmout pouze se stejnou akceptovanou kvalitou výstupu.
12. Profil vydat v nové revizi se seznamem tasků, měřeními, datem, vahami a validačním výsledkem. Po změně modelu, nástrojů, testovacího scope nebo výrazném driftu vytvořit novou kalibraci; nevydávat lidské ani Codex hodnoty za parametry Qwen.

Praktická fáze pro současná data: zachovat historical profil, na 5–10 nových taskách zapsat inventář podle této tabulky, potom ověřit S a v; po dalších nezávislých taskách rozšiřovat model. Pro retrospektivní anotaci P02–P17 číst pouze původní specifikaci/diagramy před implementací, evidovat nejisté počty a oddělit změny scope.

### 11. Evidence kalibrace a používání

Záznam každého dokončeného tasku:

    task_id, scope_revision, weights_revision, profile_fingerprint
    inventory + zdroje položek
    predicted_code/test/doc/time_min_mid_max
    actual_code/test/doc/generated_lines
    work_start, work_end, active_work, normal_validation, extra_wait, interruptions
    retries, tool_failures, scope_changes, acceptance_result
    baseline_commit, completion_commit nebo scope-filtered diff
    time_measurement_method, missing_values, quality_review

Nesmí se opravovat starý odhad tak, aby souhlasil s výsledkem. Uchovat původní i novou revizi. Schéma lze zatím vést jako tabulku v tasku; databáze ani nový runtime modul nejsou nutné.

Odhady tasků se nadále dělí podle samostatně pochopitelného chování. Orientačně 40 logických řádků pro interaktivní krok a 200–400 pro samostatně reviewovatelný task. Počet fyzických diff řádků tento limit přímo nenahrazuje. Čas odvodit z příslušného profilu, nikoli z univerzálního převodu na lidské hodiny.

Tento návrh upravuje odhadový dokument. Nezavádí nové globální instrukce, nespouští agenta a nemění historická zadání ani jejich původní odhady.
