status: done
last change: 2026-10-11
dependency: none
group: tooling/instructions/architecture
type: tooling
description:
M15: Aplikovat globální povinné Mermaid UML pravidlo
Priority: 4 (improvement)
Created: 2026-10-10

Uživatel požaduje nejvyšší společnou úroveň pro softwarové projekty. Existující globální soubor C:/Users/mordacik/.codex/AGENTS.md je správný cíl. Zápis však opakovaně selhal i po session grantu souboru a jeho parent adresáře a resetu node prostředí. Nejde o readonly attribute; read-only diagnostika Get-Item ukázala Archive, Get-Acl ukázal Modify pro sandbox skupinu. Přesná příčina v sandbox/tool vrstvě není doložená.

Recommended change:
Globální pravidlo je zapsané v C:/Users/mordacik/.codex/AGENTS.md; zachovat jej jako společné pravidlo pro softwarové projekty. Projektové pravidlo v AGENTS.md zůstává jako explicitní kontext pro doctranslate.

Acceptance:
Globální sekce Software architecture documentation existuje, vztahuje se pouze na SW projekty, vyžaduje classDiagram pro strukturu a sequenceDiagram pro všechny high-level procesy včetně indexu a aktualizací. Ostatní global policy nedotčená; porovnat původní a změněný soubor. Nepřenášet celou global policy do projektu.

Implementation:
Globální sekce `Software architecture documentation` je přítomná v C:/Users/mordacik/.codex/AGENTS.md. Obsahuje omezení na SW projekty, povinné Mermaid `classDiagram` a `sequenceDiagram`, procesní index, rozlišení současného a cílového stavu, požadavek aktualizace diagramů a textovou kontrolu syntaxe.

comments:
2026-10-10: Doplnění přímo autorizoval uživatel; žádost o filesystem write pro AGENTS.md i parent byla udělena.
2026-10-10: Přímý apply_patch i Codex apply_patch executable opakovaně hlásí Failed to write file; totéž po resetu REPL. Readonly atribut nepotvrzen. Neprováděna změna ACL ani alternativní přímý filesystem zápis.
2026-10-10: K dořešení: aplikovat patch z uživatelského prostředí nebo po opravě oprávnění/tool vrstvy. Tato překážka neblokuje M01–M14.
2026-10-11: Kontrolou globálního souboru potvrzeno, že sekce je zapsaná a obsahuje požadované UML pravidlo. Ostatní globální policy zůstává zachovaná; změna projektu pouze synchronizuje stav tasku.
