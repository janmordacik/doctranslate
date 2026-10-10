status: done
last change: 2026-10-10
dependency: none
group: tooling/local-agent/instructions
type: tooling
description: Local AI test - project reimplementation
Priority: 5 (lowest)
Created: 2026-10-10

Create instruction set for the local qwen 3.8 27b based agent to reimplement this project. Make documentation and analysis as the master agent in the form of the tasks to the /tasks-local-ai subdir. Consider limitations of the local ai model. Qwen serves as the low level implementing agent. Consider appropriate design level it is able to take. At first - prepare a set of different difficulty level tasks to calibrate the local agent abilities on the start and review them . Calibration tasks should be in /local-ai-test subdir.

Implementation:
Připraveny tasks-local-ai/README.md s provozními instrukcemi a local-ai-test/README.md s offline kalibračními scénáři levelů 1–16. Dokumenty výslovně nezapínají agenta, Continue ani změnu globální konfigurace.

comments:
2026-10-10: Nízká priorita. Připravit pouze instrukce, kalibrační úlohy a jejich vyhodnocovací pravidla; lokálního agenta v tomto projektu do odvolání nespouštět.
2026-10-10: Instrukce a scénáře připraveny; agent nebyl spuštěn podle explicitního projektového zákazu.
