status: done
last change: 2026-10-11
dependency: none
group: tooling/local-agent
type: tooling
estimate:
  time: 20–40 min dokumentační práce
  logical_lines: 30–70; žádný implementační kód
  tokens: 3k–6k pracovní odhad; vstupní kontext nejvýše 4k
  subtasks: L01, L02
description:
Připravit izolované instrukce pro budoucí ověření lokálního agenta; historická chyba Continue je pouze podklad.
Priority: 5 (low)
Created: 2026-10-10

Historická diagnostika ověřila jen přístup ke komunikačním souborům a vrátila 0. Izolovaná read-only calibration qwen3-coder:30b Native skončila WORKER_ERROR před jakýmkoli tool callem. Tento záznam nepopisuje aktuálně znovu změřený stav. Používání agenta je pro projekt vypnuté a tento task neblokuje implementaci ostatních úloh.

Evidence:
2026-10-10 15:13:24–15:13:56 Europe/Prague: Continue server did not become ready within 15 seconds, SERVER_EXIT_ERROR, exitCode=1. Checkpoint completion_detected=false, tool_call_states=[]. Starší agent_metrics.yaml má stejné omezení cn serve.

Recommended change:
Zkontrolovat a případně doplnit existující izolovaný balíček tasks-local-ai. Popsat postup budoucí diagnostiky, důkaz skutečného tool callu, kalibraci a obnovu. Veškeré příkazy jsou pouze instrukce pro pozdější výslovně autorizovaný běh. Neměnit Continue, Ollamu, globální konfiguraci ani agenta spouštět.

Acceptance:
Instrukce obsahují minimální kontext, jeden soudržný krok na soubor, očekávané výsledky a způsob nezávislého review. Nevyžadují znalost dokončených tasků hlavního projektu. Budoucí read probe je předepsán, nikoli proveden. Závěr výslovně uvádí: agent nebyl spuštěn; schopnost není nově ověřena.

Implementation:
Balíček tasks-local-ai již existuje a jeho README zakazuje automatické spuštění. Zbývá dokumentační kontrola minimálního kontextu a nepřekrývajících se instrukcí. Tento task neopravuje runtime agenta.

## Plán pro lightweight implementátora

### L01 – prověřit existující izolované instrukce

- Dependency: none. Kontext: tasks-local-ai/README.md,
  context/00-scope.md a tasks/INDEX.md; pak vždy jen jeden vybraný task
  a kontext, na který odkazuje. Nenačítat celý projekt/history najednou.
- Výsledek: seznam skutečně chybějících vstupů/kontraktů; každý task je
  pochopitelný bez odkazů typu „viz hotová implementace“ nebo „jako minule“.
  Zhodnotit minimální sadu souborů, povolené změny, zákaz commitu a ověření.
- Ověření: statická kontrola odkazů/dependencies, bez workeru a bez kalibrace.
- Odhad: 10–20 min, 10–30 řádků evidence, 1k–3k tokenů.

### L02 – opravit pouze nalezené nedostatky balíčku

- Dependency: L01. Kontext: evidence L01 a konkrétní neúplné instrukce.
- Výsledek: konkrétní task má kontext, vstup, povolené soubory, výstup,
  testovací příkaz, odhady a stop podmínku. Opakovatelný nástrojový postup
  pouze referencovat; nezavádět druhou aktuální frontu vývoje aplikace.
- Ověření: všechny relativní odkazy existují, dependency jsou acyklické,
  instrukce nikde nepředpokládají neověřenou schopnost agenta.
- Odhad: 10–20 min, 20–40 řádků, 2k–3k tokenů. Pokud L01 nenajde mezeru,
  stačí evidence bez vynuceného přepisování funkčních instrukcí.

Restart: poslední L-krok a soubory zapsat do comments. Spuštění local Qwen
vyžaduje obnovení oprávnění uživatelem a příslušnou orchestration skill;
samotná existence plánu žádné takové oprávnění neuděluje.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Nezpracováno; read calibration qwen3-coder:30b Native znovu skončila před tool callem na Continue serveru. Bez změny globální konfigurace nelze tooling bezpečně opravit v rámci této úlohy.
2026-10-11: Revize promítla dřívější pokyn uživatele: pouze připravit instrukce, agenta nespouštět a nejnižší priorita. Soubor přejmenován na prioritu 5; historická evidence selhání zachována. Přidány L01–L02 a odstraněn zastaralý předpoklad, že ostatní implementace čeká na opravu Continue. Revize agenta nespouštěla.


2026-10-11: Statická kontrola dokončena bez spuštění agenta. tasks-local-ai/README.md,
INDEX.md, context/00–05 a tasky 01–10 existují; README výslovně zakazuje
automatické spuštění, commit, push, síť a globální změny. Pořadí, izolované
kontexty, provozní edge cases a tools cookbook jsou přítomné. Nebyla zjištěna
mezera, která by odůvodnila změnu balíčku.

2026-10-11: Task uzavřen jako dokumentační příprava. Schopnost lokálního agenta
nebyla nově ověřena a žádný agent nebyl spuštěn. Budoucí delegace vyžaduje nové
výslovné zadání a zdravotní diagnostiku podle AGENTS.md.
