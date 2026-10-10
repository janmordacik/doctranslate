status: done
last change: 2026-10-10
dependency: none
group: app/validation
type: bug
description:
Fronta a konfigurace přijímají některá neplatná data bez vysvětlení
Priority: 3 (normal)
Created: 2026-10-10

QueueStore._normalise() kontroluje obálku, ne povinná pole jobů, ID a stavy. Neznámé kinds jsou tiše zahazovány. load_config() vrací {} i při poškozeném/neudostupném souboru a může přepnout workdir na cwd. Konfigurace se ukládá pod parents[2], které u nainstalovaného balíčku může být site-packages. PDF prázdné, šifrované a scan bez textu nemají jednotný preflight.

Evidence:
Probe _normalise přijal job id x, state mystery bez input/output; malformed config -> {}. configure() správně odmítá chybějící zdroj, stejné cesty, stejné jazyky a ne-PDF přípony. job_identity správně kontroluje page range.

Recommended change:
Malá centralizovaná validace job/control/config (TypedDict nebo dataclass bez nového frameworku), uniq ID, stavy, typy/phase a konfliktní output. Odlišit chybějící config od vadného; upozornit a nezapisovat jinam potichu. Definovat cestu config pro source/installed režim. PDF empty/password/no-text pojmenovat; OCR nenabízet jako hotovou funkci.

Acceptance:
Vadný JSON/schema/ID/state/phase se odmítne před změnou fronty; validní .bak fallback je oznámen. Konfigurace z installed režimu nejde do site-packages. Nevznikají artefakty při neplatném vstupu.

Implementation:
QueueStore již odmítá neznámé položky, duplicitní ID a neplatné povinné hodnoty; nyní při načtení oznamuje použití platného .bak a rozlišuje neexistující frontu od poškozené fronty i poškozené zálohy. ConfigError rozlišuje chybějící konfiguraci od neplatného JSON/schema a instalovaný balíček zapisuje výchozí konfiguraci do aktuálního pracovního adresáře, ne do site-packages. PDF preflight před Ollamou/sazbou odmítá šifrované, prázdné a textově nečitelné vstupy bez OCR.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Částečně opraveno: QueueStore nyní odmítá neznámé kinds, duplicitní ID a neplatný state/phase/povinná pole.
2026-10-10: Dokončeno přímo v config.py, queue_app.py a translate.py bez lokálního agenta. Přidána oznámená .bak recovery, ConfigError, bezpečné umístění konfigurace a PDF vstupní preflight.
2026-10-10: Ověřeno 24 testy kombinace fronty, konfigurace, CLI inputu a fault scénářů. OCR zůstává záměrně mimo rozsah.
