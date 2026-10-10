status: done
last change: 2026-10-10
dependency: none
group: translation/xhtml
type: bug
description:
Překladové core nechává markup v původním jazyce
Priority: 3 (normal)
Created: 2026-10-10

TranslationPipeline mění block.text, ale XhtmlBlock.translated() bez markup argumentu ponechá původní markup. Renderer používající markup může vypsat původní jazyk. Chybí i kontrola typu backend výstupu: None se změní na řetězec 'None'. Core je zatím oddělený kontrakt, nikoli produkční orchestrátor.

Evidence:
Probe backend hello -> AHOJ: result.text == AHOJ, result.markup == <p>hello</p>. Pipeline ověřuje cardinalitu, pak str(value). Legacy bridge převádí metadata, ale registry/pipeline nejsou používány v production entrypoint.

Recommended change:
Definovat jediný závazný obsahový kontrakt. Pro formátovaný XHTML překládat označené textové uzly a obnovovat markup; pro plain text explicitně generovat nebo invalidovat markup. Odmítnout ne-string values. Zachovat layout metadata a ruční editace HTML. Nepřipojovat dnešní nekonzistentní pipeline do production před opravou.

Acceptance:
Text/markup spolu souhlasí po překladu a po no-op; entity, inline styly a tvrdé zlomy se zachovají. None, špatný počet a nepovolený markup odmítnuty. Bez PDF dependency v core.

Implementation:
Pipeline odmítá None a chybnou cardinalitu, plain-text backend bezpečně aktualizuje jediný textový uzel a zachová tagy/entity/styly. Pro více textových uzlů je definován explicitní MarkupTranslation(text, markup), který umožňuje strukturovanému backendu zachovat inline prvky a hard breaks bez heuristického dělení překladu. PDF dependency v core není.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Opraven jednoduchý markup: pipeline aktualizuje jediný textový uzel, zachová tagy a odmítne None nebo více textových uzlů bez strukturovaného backendu. Inline překlady s více uzly zatím nejsou podporované; cílené testy prošly.
2026-10-10: Přidány testy entit, inline stylu a zachování hard break při no-op.
2026-10-10: Přidán a exportován strukturovaný MarkupTranslation kontrakt pro více textových uzlů; cílená core suite nyní prochází 9 testy. Produkční legacy orchestrace tento nový backend zatím nepoužívá.
