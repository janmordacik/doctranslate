status: done
last change: 2026-10-11
dependency: none
group: gui/job-management
type: feature
description: Umožnit vytvoření nového jobu zkopírováním vybraného jobu ze seznamu
Priority: 3 (normal)
Created: 2026-10-11

## Cíl

Umožnit uživateli vytvořit nový job z dat vybraného jobu v seznamu. Akce
se zobrazí v detailu aktuálně vybraného jobu a otevře údaje jako nový návrh
jobu v existujícím editoru na hlavní stránce.

## Požadavky

- V detailu vybraného jobu zobrazit akci Copy job / lokalizovaný ekvivalent.
- Kopie převezme vstupní a výstupní cesty, fázi, XHTML cestu, provider, model,
  profil a další uživatelsky nastavitelné parametry původního jobu.
- Nová kopie musí dostat nový jedinečný identifikátor.
- Kopie nesmí změnit ani okamžitě uložit původní job.
- Po kopírování se údaje zobrazí v editovatelném detailu; uživatel je může
  upravit a potvrdí je tlačítkem OK, případně zruší tlačítkem Cancel.
- Po potvrzení se kopie přidá do fronty jako nový job ve stavu prepared.
- Výchozí pořadí kopie bude určeno existujícím pravidlem pro přidání jobu.
- GUI označí frontu jako změněnou a změna se odešle workeru až existujícím
  tlačítkem Update jobs.
- Kopírování musí respektovat stav workeru a existující ochranu před úpravou
  aktivního jobu; kopírování samo nesmí zastavit worker.
- Zachovat anglickou a českou lokalizaci.
- Pokud není vybrán žádný job, akce je neaktivní nebo zobrazí srozumitelnou
  informaci.

## Acceptance

- Z vybraného jobu lze otevřít nový editovatelný job se zkopírovanými údaji.
- Originální job zůstane beze změny.
- Potvrzená kopie má nový ID, stav prepared a je viditelná v seznamu.
- Nepotvrzená kopie se do fronty neuloží.
- Po potvrzení se projeví indikace neodeslaných změn a Update jobs odešle
  kopii workeru podle existujícího mechanismu.
- Funkce je dostupná v obou jazycích a funguje při běžícím i zastaveném workeru.
- Doplnit unit/GUI testy minimálně pro kopii dat, nové ID, reset stavu a Cancel.
- Pokud se nezmění high-level kontrakt nebo proces, Mermaid architekturu pouze
  nerevidovat; jinak aktualizovat příslušný classDiagram, sequenceDiagram
  a process index.

## comments

2026-10-11: Task založen na požadavku přidat kopírování vybraného jobu z detailu jobu.
2026-10-11: Implementováno v QueueGui; kopie se otevírá jako editovatelný draft,
při potvrzení dostává nové ID a stav prepared. Zachována jsou i skrytá metadata
(jazyky, formáty a rozsah stran). Doplněny české/anglické popisky a regresní testy.
