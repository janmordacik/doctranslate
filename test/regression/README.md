Krátké testy PDF překladače

Sada je integrována v test/regression/ a testuje zdrojový modul v src/doctranslate/. Používá
pouze standardní Python a PyMuPDF, které už překladač potřebuje.

Nejdříve spusťte bez modelu:

    python test/regression/translate_regression.py --script src/doctranslate/translate.py

Provede 16 kontrol proti místnímu simulovanému API. Skutečná Ollama ani GPU se
nepoužívá. Zde ověřený běh trval přibližně 3 sekundy; čas na vašem PC se může lišit.
PASS znamená úspěch kontroly, FAIL konkrétní problém. Návratový kód je 0 při úspěchu,
1 při chybě a 130 při přerušení Ctrl+C. Běžné pracovní JSONy knihy se nepoužívají.

Kontroly zahrnují:
- dostupný původní font, serifovou náhradu neznámého fontu A, české znaky a vadný font;
- zmenšení delšího textu, kurzivu, tvrdé zlomy obsahu, obrázky a vektorovou grafiku;
- 182 bloků se dvěma poškozenými výsledky: uložit 180 a znovu poslat pouze dva;
- neúplný JSON, ochranu doslovných úseků, omezená opakování, timeout a uvolnění modelu;
- přerušení, obnovení z cache/JSONu, HTML před opakováním a směrování CLI/GUI;
- HTML s obrázkem a metadaty, ruční opravu a sazbu PDF bez modelu i bez cache;
- osm poškozených HTML, která nesmí změnit existující PDF ani checkpoint;
- přerušení a obnovení sazby bez AI, odlišné opravy opakovaného textu a staré plány.

Každý běh zapisuje do nové podsložky v adresáři tmp/doctranslate-test-results.
Hlavní report je report.json, podrobnosti jednotlivých kontrol jsou v test.log.
Kontrolní výstup sazbové zkoušky je layout/translated.html a layout/translated.pdf. Třetí stránka, která obsahuje
jen čísla a symboly, musí zůstat beze změny. Statistiky AI v těchto test.log jsou
simulované; nejde o měření rychlosti skutečného modelu.

Potom lze zapnout krátký test skutečného modelu:

    python test/regression/translate_regression.py --script src/doctranslate/translate.py --live

Nejprve projdou offline kontroly. Poté se použije MODEL a adresa Ollamy z vašeho
src/doctranslate/translate.py. Server musí běžet a model musí být dostupný. Ověření se řídí těmito limity:
- jediný překladový požadavek, bez automatického opakování nebo dělení;
- čtyři krátké bloky na jedné stránce, včetně dvou řádků a tečkovaného vodítka;
- kontext nejvýše 8192 tokenů, výstup nejvýše 512 tokenů, think=false;
- timeout překladového požadavku 120 sekund, potom zrušení požadavku a pokus o uvolnění;
- bez postupného testování velkých kontextových oken.

Načtení modelu je součástí překladového požadavku. Ověření dostupnosti a úklid mohou
přidat další čas. Model se uvolňuje i při chybě a Ctrl+C; případné selhání uvolnění
se vypíše. Běžná konfigurace překladače se nepřepisuje.

Výstupy živého testu: live/live-en.pdf, live/live-cs.pdf a live/budget.json.
Při chybě zůstává diagnostika live/live-cs.ollama-error.json. Test kontroluje strukturu
a vznik PDF; správnost a přirozenost českého překladu posuďte v PDF nebo ve výpisu.

V test/mock jsou připravené sample-en.pdf a sample-cs-reference.pdf pro rychlé
vizuální srovnání a sample-cs-reference.html jako ukázka čitelného HTML s obrázkem.
Česká reference vznikla z pevně zadaného překladu, bez modelu.
Každý běh si navíc vytvoří vlastní vzorek, aby nezávisel na souborech v test/mock.

Dvoufázový postup v translate.cmd

Výchozí režim both nejprve dokončí překlad do HTML, uvolní model a teprve potom
vytvoří PDF. Pro ruční kontrolu překladu spusťte samotnou první fázi:

    translate.cmd -infile "book.pdf" -outfile "kniha.pdf" -inlang en -outlang cs -phase html

Vznikne kniha.html vedle budoucího PDF. Cestu HTML lze nastavit pomocí -htmlfile.
Otevřete HTML v prohlížeči pro čtení. Pro opravy použijte textový editor v UTF-8.
Měňte text uvnitř <span data-span="...">. Zachovejte značky data-block/data-span,
atributy data-bbox/data-status, <br> i JSON metadata v hlavičce. Metadata popisují
původní stránky, rámečky, fonty, velikosti, barvy a strukturální zlomy. PDF fáze
ověří jejich soulad s původním souborem a pro sazbu znovu načte původní geometrii.
HTML obsahuje obrázky přímo v sobě; nepotřebuje složku s obrázky. CSS zajišťuje
jen čitelnost a velikost obrázků, bez souřadnic, tabulek a napodobení sazby knihy.
Vektorové kresby se v HTML nekopírují; v PDF zůstávají zachované.

Po kontrole překladu spusťte druhou fázi:

    translate.cmd -phase pdf -htmlfile "kniha.html"

Ollama neběží. Původní PDF je stále nutné: jeho cestu a jazyky skript přečte
z HTML. Po přesunu knihy lze cestu opravit parametrem -infile; -outfile vybere
jméno PDF. SHA256 musí odpovídat původní knize. Úpravy či pořadí obrázků v HTML
nemění obrázky v PDF: PDF je přebírá z původního souboru ve stejné poloze.
Text se vloží do původních rámečků se zachováním fontu, případnou náhradou
a zmenšením při nedostatku místa. Žádný druhý AI průchod není potřeba.

Při přerušení překladu se platné bloky a HTML ukládají průběžně. Nehotové bloky
se zobrazují šedě a mají data-status="pending". Sazba nehotového HTML skončí
s konkrétní chybou před úpravou PDF. Pokračování bez parametrů obnoví poslední
práci i zvolenou fázi. Starší JSONy a překlady v cache se nadále používají.
Při přerušení sazby se pokračuje po poslední uložené stránce bez modelu.
Pokud později změníte HTML, skript PDF znovu sestaví z původního souboru;
ruční opravy přitom převezme z HTML, i když už JSON cache neexistuje.

Pro výběr fáze a všech cest v okně:

    translate.cmd -gui

Ukázkové HTML v test/mock má přenositelné relativní cesty k sample-en.pdf
a k sample-cs-output.pdf o složku výše. Pro jiný cíl přidejte -outfile,
například "ukazka.pdf". Samotný testovací příkaz pracuje ve vlastní podsložce.

