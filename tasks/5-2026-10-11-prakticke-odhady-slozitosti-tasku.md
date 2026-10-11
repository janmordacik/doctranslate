status: created
last change: 2026-10-11
dependency: none
group: process/planning/estimation
type: improvement
priority: 5 (low)
description: Praktické odhady složitosti tasků s minimální režií.
estimate:
  time: 10–20 min aktivní práce Codexu po obnovení; předběžný expertní odhad, pilot průběžně při běžném zadávání
  logical_lines: 50–100 dokumentačních řádků po obnovení; produkční kód 0
  tokens: 2–4 k orientačních pracovních tokenů, neměřeno

## Zadání

Aktuální postup v [estimation_metrics_draft.md](../estimation_metrics_draft.md) je stále příliš složitý.
Zjednodušit běžné odhadování. Orientační cíl režie je přibližně do 5 %
celkového času přípravy implementačního zadání včetně samotného odhadu.
Jde o měkkou podmínku, kterou lze podle reality a přínosu upravit; nikoli
tvrdý limit ani podíl času implementace. Upřesnění uživatele je v Q01 níže.

Parametry musí přirozeně vyplývat z existujícího zadání/analýzy.
Analýzu nerozšiřovat o umělé entity, další diagramy či počty jen kvůli odhadu.
Zachovat odhad času a řádků, profil implementátora a možnost pozdější kalibrace.
Podrobný seznam metrik ponechat jako kandidátní návrh, ne povinný formulář.
Nejasné požadované chování se má dopracovat; nezaměňovat to s chybějící
kalibrací člověka či agenta.

## Odložení a další pokračování

2026-10-11: Na žádost uživatele odloženo. Status zůstává created podle
existujícího slovníku; task není done a nepatří do tasks/done. Bez dalšího
pokynu jej automaticky nezařazovat k implementaci. Zapsán pouze pracovní
návrh; pilot ani zavedení nové metodiky nezačaly. Po obnovení číst sekci
Pracovní návrh kompromisu v estimation_metrics_draft.md a pokračovat S01.

## Doplněný směr řešení

- WBS a bottom-up: hierarchie ověřitelných výsledků, odhady listových úloh
  agregované bez dvojího započtení. Nevyžadovat mechanicky denní tasky.
- Čas/řádky odvozovat podle podobných dokončených úloh, inspirováno PROBE;
  používat zdůvodněné intervaly a profil implementátora, ne neprůhledné body.
- Rozlišit parent (hierarchie) a dependency (implementační předpoklady).
  Přesný zápis projít v S01; nyní nemigrovat existující tasky ani schéma.
- Jeden vývojář: proveditelnost podle dependencies, pak priorita a odblokování
  dalších úloh. Gantt volitelně pro větší celky; respektovat kapacitu zdroje.
- Čas zahrnuje načtení kontextu, implementaci, testy, review a dokumentaci;
  externí čekání oddělit. Rozlišit kód/testy/dokumentaci a logické/diff řádky.
- Uvést hlavní konkrétní nejistotu. Nejasný scope dopracovat; technickou
  neznámou může odstranit malý průzkumný subtask, ne libovolný násobitel.
- Zachovat simple-v1 i detailní návrh jako kandidáty, bez potvrzení konstant.

## Plán

| ID | Samostatně reviewovatelný výsledek | Čas | Řádky | Závislost |
|---|---|---:|---:|---|
| S01 | Zpřesnit minimální formulář, reference/intervaly a rozlišení hierarchie/závislostí; ověřit na jednom existujícím tasku | 3–6 min | 20–35 | none; Q01 vyřešen |
| S02 | Porovnat praktický postup se simple-v1 na nejméně pěti běžných zadáních; evidovat režii, chybu a použitelnost | 4–8 min aktivní evidence | 15–35 | S01 |
| S03 | Vybrat postup podle výsledků, upravit měkký cíl podle potřeby a sladit projektová pravidla/dokumentaci | 3–6 min | 15–30 | S02 |

Pilotní zadání nevytvářet jen pro benchmark; využít skutečné plánované tasky.
Měření a čekání na vhodné tasky nejsou součástí času vytvoření této issue.

## Akceptace

- Běžný odhad je krátký a využívá pouze již dostupné informace.
- Orientační cíl času přípravy odhadu je přibližně do 5 % přípravy zadání;
  není tvrdou hranicí akceptace. Případnou úpravu cíle zdůvodnit pilotem.
  Podíl = čas přípravy odhadu / celkový čas přípravy zadání × 100 %.
  Celkový čas zahrnuje odhad; například při 20 minutách přípravy zadání
  je orientační cíl odhadu přibližně 1 minuta. Uvést výsledky pilotů.
- Výjimky a nákladné odhady mají stručný důvod; nevyžadují rozšiřování analýzy
  jen pro získání metrik. U sekundových tasků nezavádět neúměrnou režii měření.
- Čas a řádky zůstávají odhadnutelné pro člověka i agenta; návrhové konstanty
  jsou odlišené od měřených a nový agent má jednoduchý kalibrační postup.
- Zachovat historii a kandidátní metriky; nepřidávat nový nástroj/framework
  bez prokázané potřeby. Ověření dokumentace a výpočtů stačí, aplikaci neměnit.

## Comments

2026-10-11: Založeno na požadavek uživatele jako nízká priorita. Současné
odhady mají příliš velkou administrativní režii; cílem je praktičnost.
Implementace tohoto tasku zatím nezačala.

Q01 (resolved, 2026-10-11): Uživatel potvrdil „Času přípravy zadání“.
Základem je celkový čas přípravy implementačního zadání včetně odhadu,
nikoli čas implementace. Zadání, plán a akceptace aktualizovány;
implementace tasku zůstává nezahájená, priorita 5.

2026-10-11: Q01 doplněn: 5 % je měkký cíl, upravitelný, pokud nereflektuje
realitu. Doplněn kompromis WBS/bottom-up, analogie inspirovaná PROBE,
intervaly a závislosti pro jeden zdroj. Dokument přejmenován na
estimation_metrics_draft.md a označen jako pracovní, nikoli finální návod.
Task na žádost uživatele odložen; aktualizace dokumentace není dokončením
S01–S03. Bez pilotu a bez změny produkčního kódu.
