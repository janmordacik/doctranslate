status: done
last change: 2026-10-10
dependency: none
group: app/startup
type: bug
description:
Bootstrap a balíčkový entrypoint nemají jednotné chyby
Priority: 3 (normal)
Created: 2026-10-10

translate.cmd přímo volá python bez kontroly verze/dostupnosti. __main__ importuje translate a tím pymupdf před rozlišením status/GUI. Catch blok na konci translate.py se při python -m doctranslate neprovádí; konfigurační chyby vypíšou traceback a mohou obejít run-error log. Tk je načítáno lazy, ale chyby GUI startu nejsou jednotně ošetřeny.

Evidence:
Simulovaný chybějící pymupdf zablokoval i status s raw traceback. Neexistující --infile vyhodil nezachycený ValueError před main. Runner má 5 řádků bez bootstrap kontroly; requires-python >=3.11 je jen v pyproject.

Recommended change:
Malý bootstrap v runneru: skutečný Python >=3.11 (včetně rozumného py launcher fallbacku), stručné instalační pokyny, nenulový exit. Jeden aplikační run_cli wrapper pro modul i console script s error handlingem. Queue-only příkazy/GUI nepotřebují importovat PDF engine. Dependency preflight podle fáze, bez automatického pip/pull.

Acceptance:
Chybějící nebo starý Python, pymupdf a tkinter mají srozumitelnou zprávu. status jde bez PDF knihovny. Chybné argumenty nemění výstupy; Ctrl+C má kontrolovaný exit; příčinu logovat i při selhání konfigurování.

Implementation:
translate.cmd ověří dostupnost Pythonu a minimální verzi 3.11, použije py launcher fallback a vrací nenulový exit. Modulový i console entrypoint vedou přes doctranslate.__main__:main; queue-only režim zůstává bez importu PyMuPDF. Chybějící fitz/Tkinter a běžné konfigurační chyby mají stručné hlášení, konfigurační chyba se best-effort uloží do run-error diagnostiky.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Dokončeno přímo v __main__.py, translate.cmd a pyproject.toml podle projektového zákazu lokálního agenta.
2026-10-10: Ověřeno bootstrap testy: status projde s blokovaným modulem fitz a chybějící PyMuPDF vrací instalační pokyn. Stále se neinstalují automaticky žádné závislosti ani modely.
