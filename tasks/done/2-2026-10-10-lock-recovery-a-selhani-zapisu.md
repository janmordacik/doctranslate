status: done
last change: 2026-10-10
dependency: ../done/1-2026-10-10-kontrola-pid-ukoncuje-worker-na-windows.md
group: persistence/locks
type: bug
description:
Zámek není bezpečný při inicializaci a selhání zápisu
Priority: 2 (high)
Created: 2026-10-10

FileLock vytvoří soubor a až poté zapíše PID. Pro worker timeout=0 považuje _stale() i čerstvý prázdný lock za stale. Jiná instance může soubor odstranit ještě při inicializaci. OSError při os.write zanechá otevřený fd a lock. release() odstraňuje soubor bez kontroly vlastníka; dvě instance stale recovery mají unlink závod.

Evidence:
Mock ENOSPC v os.write -> lock stále existuje a _fd není None. Čerstvý prázdný worker.lock + FileLock(timeout=0)._stale() -> True. Statická kontrola acquire/release.

Recommended change:
Oddělit wait timeout od bezpečné grace doby neúplného locku; při zápisové chybě zavřít descriptor a odstranit pouze vlastní lock. Zavést owner token a ověření identity souboru při release/recovery; prověřit závod více recovererů. Neurčitý stav raději odmítnout s diagnostikou než odstranit živý lock.

Acceptance:
Dvě izolované instance nikdy nevlastní worker lock současně; čerstvý neúplný lock se hned neodstraní; ENOSPC neuniká fd. Recovery starého mrtvého locku a release cizího locku mají test.

Implementation:
Opraveno 2026-10-10. FileLock drží platformní synchronizační zámek po dobu vlastnictví deskriptoru; stale recovery přebírá existující deskriptor místo závodního unlink/recreate. Zachována je grace doba neúplného locku, owner token, cleanup po chybě zápisu a ochrana release cizího locku.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Základ opraven: neúplný lock má grace dobu, zápisová chyba uklidí vlastní descriptor a release ověřuje owner token. Cílené testy prošly; souběžná stale recovery byla následně pokryta subprocess regresí.
2026-10-10: Doplněn Windows named mutex a Unix flock; celá suite prošla 28 testy. Issue uzavřeno.
2026-10-10: Soubor přesunut do tasks/done podle projektových pravidel.
