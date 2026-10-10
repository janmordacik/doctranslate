status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-bootstrap-zavislosti-a-jednotne-chyby-cli.md
group: app/cli/input
type: bug
description:
Nenalezené HTML vypíše traceback; příkaz má jinou pomlčku
Priority: 3 (normal)
Created: 2026-10-10

Uživatel spustil --phase pdf s tmp\\Lucio Russo - Zapomenuta revoluce-layout.html. Tento soubor neexistuje; aktuálně existuje tmp\\Lucio Russo – Zapomenuta revoluce-layout.html (U+2013 místo ASCII U+002D). read_translation_html chybu obalí RuntimeError, ale modulový entrypoint ji nezachytí. Nejde o důkaz vadné PDF sazby: běh skončí před ní.

Evidence:
Reported command (spustil uživatel):
.\translate.cmd --phase pdf --htmlfile "tmp\Lucio Russo - Zapomenuta revoluce-layout.html" --infile "tmp\Lucio Russo - The Forgotten Revolution.pdf" --outfile "tmp\Lucio Russo - Zapomenuta revoluce-layout.pdf"

Exception chain:
FileNotFoundError [Errno 2] -> RuntimeError: Cannot read translation HTML.
Path: tmp\Lucio Russo - Zapomenuta revoluce-layout.html
Call chain: __main__.main -> translate.entrypoint -> configure_from_html -> read_translation_html -> Path.read_text.

Uživatelský traceback 2026-10-10; fs.readdir a izolovaná reprodukce konfigurace potvrzují FileNotFoundError -> RuntimeError. Aktuální zdroj: Lucio Russo – The Forgotten Revolution.pdf. HTML je aktuálně Zapomenuta bez á; starší kuchařka uváděla Zapomenutá.

Recommended change:
Před startem ověřit přesnou existenci vstupů, stručně oznámit nenalezenou cestu a nabídnout relevantní podobné názvy pouze jako návrh. Žádné tiché přejmenování/Unicode normalizování cesty. Jednotný error wrapper dle souvisejícího bootstrap issue. Kuchařku aktualizovat podle aktuálních názvů.

Acceptance:
Chybný spojovník i diakritika mají srozumitelnou chybu a exit !=0 bez změny PDF. Správně zvolená cesta projde preflight; samotnou sazbu spustí uživatel. Zachovat původní traceback v diagnostice.

Implementation:
configure_from_html a configure_phases nyní před PDF fází ověřují existenci HTML a při chybě vypíšou přesnou cestu včetně podobných HTML názvů ve stejné složce. Unicode pomlčka se automaticky nemění ani nepřejmenovává. Sazbu PDF provádí uživatel sám.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněn uživatelský traceback; ověřen rozdíl U+002D/U+2013 a aktuální HTML bez diakritiky. Reprodukce skončila před sazbou, PDF nezměněno.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Obecný entrypoint nyní vypíše stručnou chybu místo raw tracebacku.
2026-10-10: Doplněna kontrola chybějícího HTML, návrh podobných názvů a regresní test pro rozdíl ASCII pomlčky/U+2013. Ověřeno 1 testem; PDF sazba nebyla spuštěna.
