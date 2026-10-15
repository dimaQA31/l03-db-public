# l03-db-public

Golden dataset L03 для PayPilot. Мандат: **Ship it**.

Набір: `golden.jsonl`; **40 кейсів**, `set_hash: 350f461661a7`.
37 кейсів мають `added_in: hw2`; серед них 5 з `oracle: human`.
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

Очікується: той самий набір, `set_hash: 350f461661a7`, grep показує 37.
Не перезаписуйте golden до успішного завершення генерації й порівняння.

## Прогони

Команда відтворення повного прогону:

```bash
docker compose run --rm eval --set golden --gate all --profile clean
```

Код повернення 1 означає FAIL кейсів; шлях до сирого JSON ранер друкує
наприкінці. Код 2 означає помилку підготовки. Перевіряйте, що створено
новий звіт, перед його перейменуванням. Усі три прогони використовують
один golden, однакові налаштування моделей і повний gate all.

### Прогноз до експерименту

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

### Три прогони

Команди нижче використовують поточне ім'я контейнера стенду. На іншій
машині замініть `paypilot-stand-shared-db-stand-1` своїм ім'ям із docker ps.
Запускайте блоки по черзі, перевіряючи створення кожного нового звіту.

```bash
# 1. Clean на оригінальному промпті.
docker cp prompts/base.original.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
docker compose run --rm eval --set golden --gate all --profile clean
# Перейменуйте щойно створений reports/golden-clean-<час>.json у reports/clean.json.

# 2. Зламаний профіль на тому самому оригінальному промпті.
docker compose run --rm eval --set golden --gate all --profile lesson-03
# Перейменуйте щойно створений reports/golden-lesson-03-<час>.json у reports/lesson-03.json.

# 3. Clean з власним рядком у промпті.
docker cp prompts/base.hw2.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
docker compose run --rm eval --set golden --gate all --profile clean
# Перейменуйте щойно створений reports/golden-clean-<час>.json у reports/clean-modified-prompt.json.

# Відновлення оригінального промпту.
docker cp prompts/base.original.md paypilot-stand-shared-db-stand-1:/stand/prompts/base.v1.md
```

Перейменування зберігає сирий JSON без змін. Не копіюйте старі звіти з
іншими хешами. Перед публікацією перевірте, що кожен звіт має
`set_hash: 350f461661a7`, `gate: all`, `total + skipped = 40`; для повного
оцінювання потрібен налаштований judge і `skipped: 0`.

| Прогін | Сирий звіт | PASS / total | Статус |
| --- | --- | --- | --- |
| clean | [reports/clean.json](reports/clean.json) | 36 / 36 | 4 skipped: judge не налаштований |
| lesson-03 | [reports/lesson-03.json](reports/lesson-03.json) | 25 / 36 | 11 FAIL, 4 skipped |
| clean зі зміненим промптом | [reports/clean-modified-prompt.json](reports/clean-modified-prompt.json) | 36 / 36 | 4 skipped: judge не налаштований |

### Фактичний результат і порівняння з прогнозом

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
залишок 48745.10 EUR. Assertion очікує 50000 і приймає це число будь-де
у відповіді. Тому PASS цього кейса не підтверджує правильність саме
залишку: є розбіжність між очікуванням кейса та seed-даними, а numeric
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
Для повного оцінювання HUM-001…004 потрібна конфігурація judge та нові
зіставні прогони; наявні сирі результати збережено як є.
