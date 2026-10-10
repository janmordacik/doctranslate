status: done
last change: 2026-10-10
dependency: ../done/2-2026-10-10-worker-se-nespusti-pres-balicek.md, ../done/2-2026-10-10-update-fronty-prepisuje-novejsi-stavy.md
group: runtime/worker/control
type: bug
description:
Životní cyklus workeru nesouhlasí s dlouhými dávkami a editacemi
Priority: 2 (high)
Created: 2026-10-10

running() požaduje heartbeat mladší než 15 s, ale heartbeat se píše jen mezi dávkami, které mohou trvat minuty. Živý worker pak vypadá zastavený a stop nemusí být odeslán. QUEUE_HOOK je pouze při ukládání HTML, ne při PDF sazbě. Pause posledního jobu může být přepsán done po dokončení bez další cancel kontroly. Smazání aktivního jobu může zlomit následné mark_job. GUI Start s dirty=True samo odesílá změny proti požadavku změny až přes Update.

Evidence:
Mock živého PID + starý heartbeat -> running False. Mock GUI Start s dirty True -> send zavolán. Statická kontrola Worker.after_batch/run_job/run a run_html_typesetting; poslední batch/delete nejsou end-to-end ověřeny.

Recommended change:
Živost odvodit bezpečně z lock owner/process; heartbeat ukazovat odděleně jako dobu poslední aktivity. Pollovat na vymezených checkpoint hranicích, v PDF nejvýše mezi stránkami při budoucí implementaci. U dokončení atomicky rozhodnout done/paused/stop. Definovat nebo zakázat delete/change aktivního jobu. Start jen startuje worker; Update odesílá editace.

Acceptance:
Mock dlouhé dávky neblokuje doručení stop; pause/stop při posledním commitu a delete aktivního jobu mají deterministický stav. Start neodesílá dirty změny. Žádná nová sada stavů ani realtime IPC.

Implementation:
Opraveno 2026-10-10. Worker potvrzuje živost lockem i PID, kontroluje stop/pause po dokončené Ollama dávce a zachovává in_progress při stopu/restartu. GUI Start neposílá draft; pokus o smazání aktivního jobu vyvolá konflikt místo rozbití následného mark_job. PDF sazba nadále kontroluje cancel mezi stránkami, bez nového realtime IPC.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Částečně opraveno: liveness již nespoléhá pouze na 15s heartbeat a Start již neodesílá draft. Pause/stop na poslední dávce, mazání aktivního jobu a PDF hook zůstávají neověřené; vyžadují další worker lifecycle test.
2026-10-10: Doplněny offline regresní testy pro stop/pause po dávce a zákaz mazání aktivního jobu; 18 queue testů prošlo. Issue uzavřeno s omezením, že worker reaguje na změnu po dávce/checkpointu, nikoli uprostřed jednoho Ollama volání.
2026-10-10: Soubor přesunut do tasks/done podle projektových pravidel.
