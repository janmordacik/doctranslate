status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-testy-nepokryvaji-zivotni-cyklus-workeru.md, ../done/3-2026-10-10-xhtml-text-a-markup-se-rozchazeji.md, ../done/2-2026-10-10-nedostatek-mista-a-chyby-ulozeni.md
group: architecture/orchestration
type: refactor
description:
Postupně oddělit job context, backend a PDF adapter
Priority: 4 (improvement)
Created: 2026-10-10

translate.py má 2812 řádků/128 funkcí včetně metod, queue_app.py 764/58. Mutabilní globály spojují cesty, model, rozsah stran a run log. Worker nastavuje MODEL job.get('model') or translate.MODEL, takže job bez modelu může zdědit předchozí model. Dvě GUI třídy a staré importy zvyšují počet vstupních cest. Samotná velikost souboru není důvod k rozsáhlému přepisu.

Evidence:
AST inventura; Worker.run_job, translate.configure/configure_phases/use_html_job_metadata, TranslatorGUI a QueueGui. Production používá legacy, registry/adapters zatím nejsou zapojeny.

Recommended change:
Nejprve malý immutable JobOptions/RunContext a jeden run_job facade, backend jako Strategy, PDF input/output jako již definovaný Adapter, QueueStore jako Repository. Sdílený atomic JSON helper extrahovat až s testy chyb. Starou GUI cestu odstranit teprve po ověření dosažitelnosti. Komentovat invarianty a důvody, ne každý řádek. Typovat veřejné hranice, nepřidávat DI framework.

Acceptance:
Sekvence job A explicit model, job B bez modelu použije výchozí model B a vlastní paths/range. Zachované artefakty/checkpointy. Refaktorovat po jedné odpovědnosti, bez nových formátů a bez plošného přejmenování.

Implementation:
Zaveden immutable JobOptions ve workeru. Každý job nyní nese vlastní input/output/language/phase/model a volitelný first_page/last_page; Worker je kopíruje do run contextu a nastaví model i rozsah před spuštěním. translate.py má explicitní DEFAULT_MODEL, takže job B bez modelu nepřebírá model jobu A. Překladový backend a PDF adapter zůstávají formálně oddělené v translate_core; rozsáhlý přesun legacy globálů nebyl potřeba.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Závislé testy, storage a XHTML kontrakt jsou done; změna zůstává malá a kompatibilní s existující frontou.
2026-10-10: Ověřeno 25 testy fronty: model, cesty a rozsah se mezi joby nepřenášejí. Legacy globální stav zůstává interním omezením, ne důvodem k plošnému přepisu.
