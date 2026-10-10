status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-bootstrap-zavislosti-a-jednotne-chyby-cli.md
group: translation/ollama
type: bug
description:
GUI nerozlišuje nedostupnou Ollamu od prázdné nabídky modelů
Priority: 3 (normal)
Created: 2026-10-10

available_ollama_models() vrací () pro nedostupný endpoint i úspěšnou prázdnou nabídku. GUI doplní výchozí model a může budit dojem dostupnosti. Dotaz /api/tags probíhá synchronně v Tk vlákně. Legacy ensure_available() už správně hlásí chybějící model/server a neinstaluje automaticky; toto zachovat.

Evidence:
Mock models=[] -> srozumitelný RuntimeError s ollama pull a seznamem none. Mock unreachable a nenalezené executable -> srozumitelná chyba serveru. GUI refresh_models/constructor mají fallback default a synchronní timeout 2 s.

Recommended change:
Vrátit names + stav discovery + detail chyby; v GUI označit nedostupnost/neinstalovaný uložený model, neautomatizovat instalaci. Načítání nabídky mimo Tk thread, výsledek doručit přes after. Překladový preflight odložit, pokud už jsou všechny bloky v cache; PDF phase vůbec Ollamu nevyžaduje.

Acceptance:
Offline, prázdné models, chybějící vybraný model, invalid response a pomalá odezva mají rozlišitelný stav; GUI zůstane ovladatelné. Uložený model se nepřepíše tiše.

Implementation:
Přidán OllamaDiscovery se stavy available/empty/offline/invalid a kompatibilní available_ollama_models. GUI načítá /api/tags v daemon vlákně a výsledek doručí přes Tk after; status vedle výběru modelu rozlišuje stav. Uložené nebo ručně zvolené modely se při offline/empty odpovědi tiše nepřepíšou. Ollama ani modely se automaticky neinstalují.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Implementováno přímo v queue_app.py bez použití lokálního agenta; žádná instalace Ollamy/modelu neproběhla.
2026-10-10: Ověřeno 23 testy fronty včetně stavů empty/invalid/offline. GUI test vyžadující display nebyl spuštěn.
