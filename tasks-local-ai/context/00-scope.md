# 00 — Účel a hranice

## Cíl

Vybudovat obecný nástroj pro překlad dokumentů. Překladové jádro má pracovat
nad XHTML reprezentací s metadaty, zatímco PDF je pouze vstupní nebo výstupní
adaptér. Později musí být možné přidat další formáty bez zásahu do překladové
logiky.

## Neměnné požadavky

- Zachovat zdrojový layout, odstavce, inline formátování a metadata tam, kde
  to vstupní formát dovoluje.
- Běžné odstavce sázet do bloku; obsah typu obsah/TOC ponechat zarovnaný vlevo,
  včetně správných řádkových zlomů.
- Překlad nemá být pevně svázán s PDF knihovnou.
- GUI bez parametrů a CLI musí ovládat stejnou JSON frontu.
- Pracovní proces má být oddělený od GUI/CLI procesu.
- Trvalá fronta je JSON soubor; není požadován databázový server ani plnotučné
  IPC. Zámky musí chránit krátké zápisy a worker smí změny načítat po dávce.
- Globální stop se týká workeru. Job může být prepared, in_progress, paused,
  failed nebo done.
- in_progress pokračuje po restartu; failed se do prepared vrací ručně.
  Prepared joby zpracovávat v pořadí seznamu, bez číselných priorit.
- GUI drží editace do tlačítka Update/Send; Start pouze startuje worker.
  Zavření GUI s neodeslanými změnami musí varovat.

## Mimo rozsah jednoho tasku

Neřešit současně nový renderer, OCR, distribuci, cloudové API, databázi,
automatickou instalaci modelů, vzdálené endpointy, PDF sazbu skutečného
uživatelského dokumentu ani commit/push.
