status: done
last change: 2026-10-10
dependency: ../done/2-2026-10-10-lock-recovery-a-selhani-zapisu.md
group: persistence/queue
type: bug
description:
Starší kopie fronty přepisuje nové stavy jobů
Priority: 2 (high)
Created: 2026-10-10

QueueGui.send() i CLI add čtou joby mimo transakci a poté set_jobs() nahradí celý seznam. Lock serializuje zápis, ale nechrání před ztrátou změn mezi čtením a zápisem. Hotový job může být z draftu vrácen na prepared; dva souběžné add mohou ztratit jednu úlohu.

Evidence:
Izolovaný probe: uložit prepared, načíst snapshot, worker změní done, set_jobs(snapshot) -> znovu prepared. QueueStore.transaction / set_jobs, cli_main add, QueueGui.send.

Recommended change:
GUI drží základní revision a explicitní změny. Update provede krátkou transakci nad aktuálním snapshotem, sloučí uživatelské editace a ponechá worker-owned progress/error/started_at. Konfliktní změnu stavu oznámí; bez tichého last-writer-wins. CLI append dělat v jedné transakci.

Acceptance:
Souběžné add zachová oba joby; done a progress se při editaci pořadí/modelu neztratí; skutečný konflikt stejného stavu je explicitní. Zachovat JSON + lock, bez DB/IPC.

Implementation:
Opraveno 2026-10-10. Ověření PID používá čtecí platformní kontrolu; worker se spouští jako modul s logem; CLI add zapisuje v jedné transakci; GUI merge zachovává novější runtime stav workeru.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Oprava implementována a ověřena cílenými i celými offline testy; issue uzavřeno.
