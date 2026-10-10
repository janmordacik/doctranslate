status: created
last change: 2026-10-10
dependency: none
group: tooling/instructions/architecture
type: tooling
description:
M15: Aplikovat globální povinné Mermaid UML pravidlo
Priority: 4 (improvement)
Created: 2026-10-10

Uživatel požaduje nejvyšší společnou úroveň pro softwarové projekty. Existující globální soubor C:/Users/mordacik/.codex/AGENTS.md je správný cíl. Zápis však opakovaně selhal i po session grantu souboru a jeho parent adresáře a resetu node prostředí. Nejde o readonly attribute; read-only diagnostika Get-Item ukázala Archive, Get-Acl ukázal Modify pro sandbox skupinu. Přesná příčina v sandbox/tool vrstvě není doložená.

Recommended change:
Globální patch není v této pracovní kopii dostupný. Aplikovat jej v prostředí s funkčním zápisem do globálního AGENTS.md; nepřepisovat ostatní instrukce ani měnit ACL automaticky. Projektové pravidlo v AGENTS.md je již účinný fallback pro doctranslate.

Acceptance:
Globální sekce Software architecture documentation existuje, vztahuje se pouze na SW projekty, vyžaduje classDiagram pro strukturu a sequenceDiagram pro všechny high-level procesy včetně indexu a aktualizací. Ostatní global policy nedotčená; porovnat původní a změněný soubor. Nepřenášet celou global policy do projektu.

Implementation:
Globální zápis neproveden. Projektový fallback a patch připraveny.

comments:
2026-10-10: Doplnění přímo autorizoval uživatel; žádost o filesystem write pro AGENTS.md i parent byla udělena.
2026-10-10: Přímý apply_patch i Codex apply_patch executable opakovaně hlásí Failed to write file; totéž po resetu REPL. Readonly atribut nepotvrzen. Neprováděna změna ACL ani alternativní přímý filesystem zápis.
2026-10-10: K dořešení: aplikovat patch z uživatelského prostředí nebo po opravě oprávnění/tool vrstvy. Tato překážka neblokuje M01–M14.
