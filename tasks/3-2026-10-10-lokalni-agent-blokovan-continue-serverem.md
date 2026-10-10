status: created
last change: 2026-10-10
dependency: none
group: tooling/local-agent
type: tooling
description:
Lokální implementační agent se nedostane k úloze
Priority: 3 (normal)
Created: 2026-10-10

Povinná diagnostika ověří jen přístup ke komunikačním souborům a vrátí 0. Následná izolovaná read-only calibration qwen3-coder:30b Native skončila WORKER_ERROR před jakýmkoli tool callem. Nontriviální refaktoring podle supervisor pravidel nelze spolehlivě delegovat.

Evidence:
2026-10-10 15:13:24–15:13:56 Europe/Prague: Continue server did not become ready within 15 seconds, SERVER_EXIT_ERROR, exitCode=1. Checkpoint completion_detected=false, tool_call_states=[]. Starší agent_metrics.yaml má stejné omezení cn serve.

Recommended change:
Samostatně ověřit aktuální CLI/worker kompatibilitu a Native routing; neodvozovat podporu ze jména modelu. Po opravě fresh fingerprint + malá kalibrace a teprve následně kódové issues. Cookbook nesmí automaticky autorizovat přímou implementaci po selhání diagnostiky.

Acceptance:
Read probe vykáže skutečný Read tool call a správnou odpověď v completed checkpointu; write schopnost a relevantní level se ověří před delegací. Bez commitu a bez změn globálního configu v rámci této revize.

Implementation:
Zatím bez opravy. Revize zdrojů a návrh; nontriviální implementace vyžaduje provozuschopného a kalibrovaného lokálního agenta podle supervisor policy. Sazbu PDF provádí uživatel sám.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Nezpracováno; read calibration qwen3-coder:30b Native znovu skončila před tool callem na Continue serveru. Bez změny globální konfigurace nelze tooling bezpečně opravit v rámci této úlohy.
