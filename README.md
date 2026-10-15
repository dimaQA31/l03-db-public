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
| clean | reports/clean.json | ще не виміряно | звіт потрібно отримати |
| lesson-03 | reports/lesson-03.json | ще не виміряно | звіт потрібно отримати |
| clean зі зміненим промптом | reports/clean-modified-prompt.json | ще не виміряно | звіт потрібно отримати |

Після прогонів заповніть результати таблиці й фактичні витрати та
чутливість у residual-risk.md. Прогноз вище збережіть для порівняння.
Поки ці три JSON відсутні, комплект здачі не завершений.
