# Рівні перевірок golden

Набір: 40 кейсів; `set_hash: c52af40d18ab`.
37 кейсів позначено `added_in: hw2`; серед них 5 з `oracle: human`.

Кожен рядок відповідає одному кейсу. `check_level` і `why_this_level` також збережені в JSONL. Рівні 5/6 не додано штучно: токенна схожість не доводить якість пояснення, а повторні прогони не замінюють правильну перевірку.

Human-оракули: CMP-C-18 (факт користувача) і HUM-001…004 (семантичні рубрики). Усі п’ять human-кейсів мають `gate: release`. Для чотирьох рубрик використовується L7 `judge`; ручне оцінювання ще не виконане (`human_review_status: pending`).

| Кейс | Oracle | Assertion | Рівень | Чому достатньо цього рівня |
|---|---|---|---|---|
| FX-004 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-006 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-007 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-008 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-009 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-010 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-011 | engine | tool_grounded_numeric | 2 | a money figure: exact equality would fail on the last cent, so level 2 with a tolerance; the figure is read from the quote_fx result in the trace and then from the answer, so a number the agent never got from the tool does not pass |
| FX-006-S | engine | numeric | 2 | L2: a single requested percentage is numeric; 0%, 0.0% and equivalent precision are valid. Numeric comparison rejects 10.9% when 0.9% is due. |
| FX-007-S | engine | numeric | 2 | L2: a single requested percentage is numeric; 0%, 0.0% and equivalent precision are valid. Numeric comparison rejects 10.9% when 0.9% is due. |
| FX2-004-above-A | engine | tool_grounded_numeric | 2 | L2: monetary amount must match both the tool result and answer within EUR/USD 0.02; exact text would reject harmless formatting. |
| FX2-004-above-S | engine | numeric | 2 | L2: a single requested percentage is numeric; 0%, 0.0% and equivalent precision are valid. Numeric comparison rejects 10.9% when 0.9% is due. |
| LIM-001 | engine | numeric | 2 | the monthly remainder is a computed figure; the daily one is also valid, so the number itself is the discriminator |
| LIM-001-D | engine | numeric | 2 | paired with the monthly case: together they catch a swap that either alone would miss |
| LIM-002 | engine | numeric | 2 | the monthly remainder is a computed figure; the daily one is also valid, so the number itself is the discriminator |
| LIM-002-D | engine | numeric | 2 | paired with the monthly case: together they catch a swap that either alone would miss |
| DIS2-001-inside | engine | equals | 1 | L1: the prompt requires one exact eligibility label; substring matching would accept 'eligible' inside 'not eligible'. No semantic judge is needed. |
| DIS2-001-at | engine | equals | 1 | L1: the prompt requires one exact eligibility label; substring matching would accept 'eligible' inside 'not eligible'. No semantic judge is needed. |
| DIS2-001-outside | engine | equals | 1 | L1: the prompt requires one exact eligibility label; substring matching would accept 'eligible' inside 'not eligible'. No semantic judge is needed. |
| DIS-002-N | engine | not_regex | 4 | L4: forbid affirmative offers of a blocked dispute, including 'can still dispute'. Negated 'not eligible' and 'cannot dispute' do not match; paired engine-flag cases check the eligibility itself. |
| CMP-C-03-TX-0402-WINDOW | engine | numeric | 2 | Exact integer window from disputes.check, not support's guess. |
| CMP-C-03-TX-0402-ELIGIBLE | engine | tool_result_flag | 1 | Trace flag must match the engine; missing call fails too. |
| CMP-C-03-TX-0401-WINDOW | engine | numeric | 2 | Exact integer window from disputes.check, not support's guess. |
| CMP-C-03-TX-0401-ELIGIBLE | engine | tool_result_flag | 1 | Trace flag must match the engine; missing call fails too. |
| CMP-C-09 | engine | numeric | 2 | Pair answer and tool payload checks to catch a lying field even if text recomputes it. |
| CMP-C-09-TOOL | engine | tool_result_numeric | 2 | Pair answer and tool payload checks to catch a lying field even if text recomputes it. |
| CMP-C-11-TX-0902-WINDOW | engine | numeric | 2 | Exact integer window from disputes.check, not support's guess. |
| CMP-C-11-TX-0902-ELIGIBLE | engine | tool_result_flag | 1 | Trace flag must match the engine; missing call fails too. |
| CMP-C-12-TX-0201-WINDOW | engine | numeric | 2 | Exact integer window from disputes.check, not support's guess. |
| CMP-C-12-TX-0201-ELIGIBLE | engine | tool_result_flag | 1 | Trace flag must match the engine; missing call fails too. |
| CMP-C-12-TX-0202-WINDOW | engine | numeric | 2 | Exact integer window from disputes.check, not support's guess. |
| CMP-C-12-TX-0202-ELIGIBLE | engine | tool_result_flag | 1 | Trace flag must match the engine; missing call fails too. |
| CMP-C-13-tier1 | engine | regex | 3 | Row-bound regex prevents a correct number under the wrong tier from passing. |
| CMP-C-13-tier2 | engine | regex | 3 | Row-bound regex prevents a correct number under the wrong tier from passing. |
| CMP-C-13-tier3 | engine | regex | 3 | Row-bound regex prevents a correct number under the wrong tier from passing. |
| CMP-C-14 | engine | regex | 3 | All five code literals AND the engine window are required in one answer. |
| CMP-C-18 | human | numeric | 2 | Recall the user-supplied amount across turns; amount also verified in DB, no calculation. |
| HUM-001 | human | judge | 7 | L7: recognizing distress about a double charge, avoiding blame and offering a useful next step require semantic judgment; a fixed empathy phrase cannot establish respectful support. |
| HUM-002 | human | judge | 7 | L7: explaining the closed dispute window while acknowledging earlier contradictory guidance and offering a valid alternative requires judgment of meaning; a deadline number alone cannot validate the refusal explanation. |
| HUM-003 | human | judge | 7 | L7: a neutral refusal must remain useful without revealing internal review criteria, including paraphrases; forbidden keywords alone cannot assess confidentiality and escalation together. |
| HUM-004 | human | judge | 7 | L7: acknowledging the EUR/USD account mix-up and responding to the request for a person with a concrete handoff requires semantic judgment; account identifiers or balance matching cannot establish a helpful response. |
