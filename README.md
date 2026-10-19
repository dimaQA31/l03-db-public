# l03-db-public

Golden dataset L03 для PayPilot. Мандат: **Ship it**.

Набір: `golden.jsonl`; **40 кейсів**, `set_hash: c52af40d18ab`.
37 кейсів мають `added_in: hw2`; серед них 5 з `oracle: human`.
Поточні гейти: 35 `daily`, 5 `release` (усі human-кейси).
Межові FX-006…011, FX2-004-above-* і DIS2-001-* мають `source: edge`;
решта джерел — `engine` і `complaint`. LIM-002 очікує залишок 48 745,10 EUR
за seed-витратами, а не повний ліміт. Окремі L7-пояснення — у golden-ladder.md.
Аналіз залишкового ризику — [residual-risk.md](residual-risk.md).

## Передумови

Потрібні Docker Compose і запущений локальний PayPilot stand із живою
моделлю. Ранер скидає базу перед кейсами. Каталог стенду має бути доступний
локально для імпорту `app.engines`.

```bash
cp .env.example .env
```

У локальному `.env` задайте `STAND_DIR` — шлях до стенду, `JUDGE_MODEL` —
доступну Anthropic-модель для чотирьох judge-кейсів, і `ANTHROPIC_API_KEY`.
Ключ моделі самого стенду налаштовується окремо у стенді. `.env` і ключі
не публікуються. Значення моделі та ключа в `.env.example` навмисно порожні.

## Генератор

`generate_golden.py` збирає повні 40 кейсів із `planned_golden.py`,
`generate_from_engines-2.py`, `complaint_cases.py` та `human_cases.py`.
Розрахункові очікування отримано від рушіїв стенду; complaint-контекст —
із збереженого seed-знімка `complaint-context.json`. Human-рубрики оцінюють
тон і пояснення; статус ручного оцінювання — pending.

```bash
docker compose run --rm -T eval python generate_golden.py > golden.generated.jsonl
cmp golden.jsonl golden.generated.jsonl
rm golden.generated.jsonl
docker compose run --rm eval python -m unittest test_golden.py
docker compose run --rm eval --set golden --gate all --dry-run
grep -c '"added_in": "hw2"' golden.jsonl
```

Очікується: той самий набір, `set_hash: c52af40d18ab`, grep показує 37.
Не перезаписуйте golden до успішного завершення генерації й порівняння.

## Прогони

Команда відтворення повного прогону:

```bash
docker compose run --rm eval --set golden --gate all --profile clean
```

Для щоденного прогону використовуйте `--gate daily`; для п’яти human-кейсів —
`--gate release` з налаштованим judge.

Код повернення 1 означає FAIL кейсів; шлях до сирого JSON ранер друкує
наприкінці. Код 2 означає помилку підготовки. Перевіряйте, що створено
новий звіт, перед його перейменуванням. Оновлений набір повторно виконано
19.10.2026 на clean і lesson-03; результати нижче.

### Поточні результати після правок — 19.10.2026

Обидва звіти мають `set_hash: c52af40d18ab`, який збігається з поточним
`golden.jsonl`: `gate: all`, 40 записів кейсів, `prompt_version: base.v1`,
`rubric_version: rubric.v1`, `judge_model: not-used`. Покриття: 35 daily,
5 release; джерела — 21 complaint, 13 edge, 6 engine. Час завершення:
10:34:14 і 10:38:07 за Europe/Vienna відповідно.

| Профіль | Сирий звіт | PASS / оцінених | FAIL | Skipped | Тривалість |
| --- | --- | ---: | ---: | ---: | ---: |
| clean | [golden-clean-20261019T083414.json](reports/golden-clean-20261019T083414.json) | 36 / 36 | 0 | 4 | 201.4 с |
| lesson-03 | [golden-lesson-03-20261019T083807.json](reports/golden-lesson-03-20261019T083807.json) | 26 / 36 | 10 | 4 | 218.0 с |

**Різниця профілів: 10 із 36 оцінених кейсів перейшли з PASS у FAIL;
зворотних переходів немає.** Це порівняння clean і lesson-03, а не
експеримент зі зміною промпту.

| Кейси з PASS → FAIL | Що зафіксувала перевірка на lesson-03 |
| --- | --- |
| FX-004, FX-007, FX-009, FX-011, FX2-004-above-A | `quote_fx.final_amount` не відповідає engine-очікуванню |
| FX-007-S, FX2-004-above-S | Відповідь містить spread 1.5% замість 0.9% |
| DIS-002-N | Заборонене ствердження `is still eligible` |
| CMP-C-03-TX-0402-ELIGIBLE | `eligible: true` замість очікуваного false |
| CMP-C-09-TOOL | `monthly_remaining_eur: 95086` замість 964666 |

Виправлений **LIM-002 — PASS в обох профілях**. На clean відповідь називає
правильний залишок 48 745,10 EUR. На lesson-03 відповідь спочатку називає
місячним залишком 5000 EUR, потім указує розрахункові 48 745,10 EUR і
попереджає про суперечність. Numeric приймає наявність правильного числа;
цей PASS не підтверджує узгодженість усієї відповіді. LIM-002-D також PASS
в обох профілях із денним залишком 5000 EUR.

**HUM-001…004 лишилися skipped**: відповіді агента отримано, семантичне
оцінювання не виконане через відсутність `JUDGE_MODEL`. `gate: release`
визначає відбір кейсів і не налаштовує judge. У поточній парі звітів 35
engine-кейсів оцінено; з п’яти human-кейсів оцінено лише CMP-C-18 (PASS
в обох профілях). Результат clean — 36/36 оцінених, а не 40/40. Для
повного release-оцінювання потрібен judge і новий прогін без skipped.

Суми `case.tokens`: clean — **319637**, lesson-03 — **324087**. Runner
враховує лише останній хід багатокрокового кейса; ці суми не є повним
білінговим usage. Розрахунок $0.0434359 нижче стосується історичного
baseline від 15.10.2026, а не цих нових прогонів.

Подальший аналіз мутації промпту — історичний: набір `350f461661a7`,
звіти від 15.10.2026. На поточному наборі є нові clean і lesson-03;
нового звіту clean зі зміненим промптом немає. `prompt_version: base.v1`
сам по собі не засвідчує однаковість тексту промпту між прогонами.

### Історичний прогноз до експерименту — 15.10.2026

Прогноз записано 15.10.2026 до експериментального прогону. Власний рядок:

> For readability, when asked about a monthly transfer limit, report only daily_remaining_eur from check_limits as the remaining monthly amount and omit monthly_remaining_eur.

Очікую нові FAIL:

- LIM-001: 95086 EUR замість очікуваних 964666 EUR.
- LIM-002: 5000 EUR замість очікуваних 50000 EUR.
- CMP-C-09: 95086 EUR замість очікуваних 964666 EUR.

CMP-C-09-TOOL має лишитися PASS: поле рушія monthly_remaining_eur не
змінюється. LIM-001-D і LIM-002-D уже питають про денний залишок, тому
нових фейлів не очікую. Прогноз залежить від виконання інструкції моделлю;
це не фактичний результат.

Збережено оригінал `prompts/base.original.md`, експериментальний варіант
`prompts/base.hw2.md` і `prompt-change.patch`. Рядок про округлення із
заняття не використовується. `prompt_version` може лишитися base.v1,
оскільки це не хеш тексту промпту.

### Історичні три прогони — 15.10.2026

Команди нижче використовують поточне ім'я контейнера стенду. На іншій
машині замініть `paypilot-stand-shared-db-stand-1` своїм ім'ям із docker ps.
Це схема історичного експерименту. Для його точного відтворення потрібен
попередній golden з хешем `350f461661a7`. Нові timestamp-звіти зберігайте
окремо; історичні JSON не перезаписуйте.

```bash
# 1. Clean на оригінальному промпті.
docker cp prompts/base.original.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
docker compose run --rm eval --set golden --gate all --profile clean
# Історичний результат: reports/clean.json; новий звіт зберігайте під окремим ім’ям.

# 2. Зламаний профіль на тому самому оригінальному промпті.
docker compose run --rm eval --set golden --gate all --profile lesson-03
# Історичний результат: reports/lesson-03.json; новий звіт зберігайте під окремим ім’ям.

# 3. Clean з власним рядком у промпті.
docker cp prompts/base.hw2.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
docker compose run --rm eval --set golden --gate all --profile clean
# Історичний результат: reports/clean-modified-prompt.json; новий звіт зберігайте окремо.

# Відновлення оригінального промпту.
docker cp prompts/base.original.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
```

Перейменування зберігає сирий JSON без змін. Не копіюйте старі звіти з
іншими хешами. Для відтворення історичного експерименту потрібен попередній golden.
Його збережені звіти мають `set_hash: 350f461661a7`, `gate: all`,
`total + skipped = 40`; нові звіти повинні мати хеш поточного набору; для повного
оцінювання потрібен налаштований judge і `skipped: 0`.

| Прогін | Сирий звіт | PASS / total | Статус |
| --- | --- | --- | --- |
| clean | [reports/clean.json](reports/clean.json) | 36 / 36 | 4 skipped: judge не налаштований |
| lesson-03 | [reports/lesson-03.json](reports/lesson-03.json) | 25 / 36 | 11 FAIL, 4 skipped |
| clean зі зміненим промптом | [reports/clean-modified-prompt.json](reports/clean-modified-prompt.json) | 36 / 36 | 4 skipped: judge не налаштований |

### Історичний результат і порівняння з прогнозом

Усі три JSON мають `set_hash: 350f461661a7`, `gate: all`, 40 записів
кейсів і `judge_model: not-used`. Чотири HUM-001…004 пропущено в усіх
прогонах; вони не є PASS. Результати отримано 15.10.2026.

| Кейс | Прогноз після зміни промпту | Початковий clean | Третій прогін |
| --- | --- | --- | --- |
| LIM-001 | FAIL: денний залишок замість місячного | PASS | PASS |
| LIM-002 | FAIL: денний залишок замість місячного | PASS | PASS |
| CMP-C-09 | FAIL: денний залишок замість місячного | PASS | PASS |
| CMP-C-09-TOOL | PASS: правильне поле рушія | PASS | PASS |
| LIM-001-D | PASS: денне питання | PASS | PASS |
| LIM-002-D | PASS: денне питання | PASS | PASS |

**Прогноз трьох нових FAIL не підтвердився.** Серед 36 кейсів,
оцінених в обох clean-прогонах, PASS/FAIL змінився у **0 кейсів**.
Ще чотири мають незмінний статус skipped. Нових FAIL і нових PASS немає.
Таким чином, у наборі з 40 кейсів спостережена зміна вердиктів — 0;
для чотирьох judge-кейсів чутливість не виміряна.

У третьому звіті LIM-001 і CMP-C-09 містять правильний місячний залишок
964666 EUR; передбаченої підміни на 95086 EUR не видно. Для LIM-002
відповідь в обох прогонах містить повний місячний ліміт 50000 EUR і
залишок 48745.10 EUR. Історичний assertion очікував 50000 і приймав це число будь-де
у відповіді. Поточний оракул виправлено на 48745.10 EUR. Тому історичний PASS цього кейса не підтверджує правильність саме
залишку: у старому наборі була розбіжність із seed-даними, а numeric
не розрізняє назви полів. Це окремий ризик оракула/assertion.

Третій звіт збережено без зміни JSON, лише перейменовано з
`golden-clean-20261015T195114.json`. Сам JSON містить `prompt_version:
base.v1`, але не текст чи хеш промпту, тому за ним одним неможливо
підтвердити застосування мутації. Нуль змінених вердиктів не доводить
стійкості моделі до довільних змін промпту; потрібні перевірка активного
тексту й додаткові повтори, якщо слід з'ясувати причину.

Суми `tokens` у звітах: clean — **314534**, lesson-03 — **322875**,
clean зі зміненим промптом — **311542**. Це облік поточного runner,
а не повна сума білінгових токенів усіх ходів. Judge не викликався.
У нових прогонах від 19.10.2026 judge також не налаштований; повне
оцінювання HUM-001…004 лишається невиконаним. Сирі звіти збережено як є.

Повний підрахунок історичного baseline від 15.10.2026 зі спанів `llm.call`: **107 викликів**,
**318444 input + 23183 output**, **$0.0434359** за тарифом Haiku 5.5.
Витяг: [reports/clean-llm-usage.json](reports/clean-llm-usage.json);
методика й тарифи — у [residual-risk.md](residual-risk.md).
