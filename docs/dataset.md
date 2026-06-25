# Описание датасета

## Источник данных

В проекте используется датасет LinkedIn Job Postings, загруженный из Kaggle.

## Исходный файл

Основной файл:

`data/raw/linkedin/postings.csv`

Количество исходных строк: 123849.

## Использованные поля

Из исходного файла используются следующие поля:

- `job_id` — внешний идентификатор вакансии;
- `company_name` — название компании;
- `title` — название вакансии;
- `description` — описание вакансии;
- `min_salary` — минимальная зарплата;
- `max_salary` — максимальная зарплата;
- `location` — локация;
- `formatted_work_type` — формат занятости;
- `remote_allowed` — признак удаленной работы;
- `formatted_experience_level` — уровень опыта;
- `skills_desc` — описание требуемых навыков;
- `listed_time` — время публикации;
- `work_type` — тип занятости;
- `currency` — валюта;
- `job_posting_url` — ссылка на вакансию.

## Фильтрация данных

Из исходных 123849 вакансий были отобраны вакансии, относящиеся к IT, data, software engineering, ML, DevOps, QA и смежным направлениям.

После фильтрации осталось 32096 вакансий.

Для рабочей версии проекта использована случайная выборка из 30000 вакансий.

## Результат подготовки данных

Были сформированы следующие CSV-файлы:

- `data/processed/sources.csv` — источники данных;
- `data/processed/companies.csv` — компании;
- `data/processed/locations.csv` — локации;
- `data/processed/professional_categories.csv` — профессиональные категории;
- `data/processed/seniority_levels.csv` — уровни опыта;
- `data/processed/skills.csv` — справочник навыков;
- `data/processed/vacancies.csv` — вакансии;
- `data/processed/vacancy_skills.csv` — связи вакансий и навыков;
- `data/processed/import_batches.csv` — информация о партии импорта.

## Итоговые размеры таблиц

- `vacancies.csv`: 30000 строк;
- `companies.csv`: 9717 строк;
- `locations.csv`: 3944 строки;
- `professional_categories.csv`: 9 строк;
- `seniority_levels.csv`: 6 строк;
- `skills.csv`: 80 строк;
- `vacancy_skills.csv`: 52027 строк;
- `sources.csv`: 1 строка;
- `import_batches.csv`: 1 строка.

## Особенности качества данных

В исходных данных часть вакансий не содержит зарплату, часть компаний не имеет названия, а локации представлены в свободном текстовом формате. Поэтому при подготовке данных были использованы значения по умолчанию, например `Unknown company` и `Unknown`.

Категории вакансий и уровни опыта были определены автоматически по правилам на основе названия, описания и поля `formatted_experience_level`.

Навыки были извлечены словарным методом из `skills_desc`, `title` и `description`.
