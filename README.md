# JobMatch Service

Интеллектуальный сервис поиска, анализа и персонального подбора IT-вакансий

Проект представляет собой сервис, позволяющий работать с базой вакансий: искать подходящие предложения, создавать профиль пользователя, добавлять навыки, получать персональные рекомендации и анализировать рынок вакансий по навыкам, компаниям, зарплатам и формату работы.

Проект разработан в рамках дисциплины «Проектирование и реализация баз данных».

## Демонстрация работы

Видео-демо: `https://disk.360.yandex.ru/i/v_G4HpskwAtvxQ`

---

## Описание системы

Пользовательские и технические сценарии.

### **Пользователь**

- создаёт или обновляет профиль;
- выбирает целевую профессию и грейд;
- добавляет навыки и указывает уровень владения;
- получает персональные рекомендации вакансий;
- ищет вакансии по текстовому запросу и фильтрам;
- открывает карточки вакансий;
- редактирует или удаляет данные профиля.

### **Аналитик / менеджер**

- смотрит востребованность навыков;
- анализирует активность компаний;
- оценивает зарплатную статистику по категориям;
- смотрит распределение форматов работы;
- анализирует популярные поисковые запросы пользователей.

### **Backend-сервис**

- обрабатывает API-запросы frontend-приложения;
- обращается к PostgreSQL как к основной базе данных;
- использует Redis для кэширования и временных данных;
- выполняет поиск, рекомендации и аналитические запросы.

### **PostgreSQL**

- хранит нормализованную модель предметной области;
- поддерживает связи между вакансиями, компаниями, локациями, навыками и пользователями;
- содержит views, indexes, functions, procedures и triggers;
- обеспечивает целостность данных через PK, FK, UNIQUE и CHECK constraints.

### **Redis**

- хранит кэш результатов поиска;
- хранит кэш карточек вакансий;
- хранит последние поиски пользователя;
- хранит популярные поисковые запросы и навыки;
- используется для rate limiting;
- содержит stream-очередь задач импорта.

---

## Основная функциональность

### Управление профилем пользователя

- создание профиля;
- выбор целевой профессии;
- выбор грейда;
- добавление навыков;
- изменение уровня навыка;
- удаление одного или всех навыков;
- сброс целевой профессии, грейда и города;
- удаление пользователя.

### Поиск вакансий

- полнотекстовый поиск по названию и описанию вакансии;
- фильтрация по категории;
- фильтрация по грейду;
- фильтрация по формату работы;
- фильтрация по минимальной зарплате;
- кэширование повторных поисков в Redis.

### Персональные рекомендации

- подбор вакансий на основе навыков пользователя;
- учёт целевой профессии;
- учёт грейда;
- расчёт итогового match score;
- отображение карточки выбранной вакансии.

### Аналитика

- топ востребованных навыков;
- статистика зарплат по категориям;
- активность компаний;
- распределение форматов работы;
- популярные поисковые запросы пользователей.

### Резервное копирование

- plain SQL dump;
- custom PostgreSQL backup;
- проверка восстановления на тестовой базе.

---

## Технологии

### **Frontend**

- Streamlit;
- Altair;
- Pandas.

### **Backend**

- Python;
- FastAPI;
- Uvicorn;
- Psycopg;
- Pydantic.

### **База данных**

- PostgreSQL;
- plain SQL dump: `dumps/vacancy_service_plain.sql`;
- custom backup: `dumps/vacancy_service_custom.backup`.

### **NoSQL-компонент**

- Redis;
- RedisInsight;
- Поднимается через Docker Compose.

---

## Архитектура проекта

### **Структура репозитория**

`/app` — backend FastAPI  
`/app/db` — подключение к PostgreSQL и Redis  
`/app/services` — бизнес-логика поиска, рекомендаций, аналитики и профилей  
`/frontend` — Streamlit-интерфейс  
`/scripts` — подготовка данных и загрузка в PostgreSQL  
`/sql` — SQL-скрипты схемы, индексов, views, функций, процедур и триггеров  
`/dumps` — PostgreSQL dumps  
`/docs` — документация проекта
`/data/sample` — место для небольших примеров данных  
`docker-compose.yml` — запуск Redis и RedisInsight

## Модель базы данных

Основная схема PostgreSQL: `job_service`.

### Основные таблицы

- `sources` — источники вакансий;
- `companies` — компании;
- `locations` — локации;
- `professional_categories` — профессиональные категории;
- `seniority_levels` — грейды / уровни seniority;
- `vacancies` — вакансии;
- `skills` — навыки;
- `vacancy_skills` — связь вакансий и навыков;
- `users` — пользователи;
- `user_skills` — связь пользователей и навыков;
- `favorite_vacancies` — избранные вакансии;
- `vacancy_views` — просмотры вакансий;
- `import_batches` — пакеты импорта;
- `vacancy_audit` — аудит изменений вакансий.

### Представления

- `v_vacancy_cards` — готовая карточка вакансии;
- `v_skill_demand` — востребованность навыков;
- `v_category_salary_stats` — зарплатная статистика по категориям;
- `v_company_activity` — активность компаний;
- `v_work_format_stats` — статистика форматов работы;
- `v_user_recommendation_base` — база для рекомендаций;
- `v_database_summary` — сводка по количеству строк.

### Схема базы данных

- IDEF1X: `docs/idef1x_erd.png`.

---

## Индексы

- `idx_vacancies_company_id` — поиск и аналитика по компаниям;
- `idx_vacancies_category_seniority` — фильтрация по категории и грейду;
- `idx_vacancies_salary` — фильтрация по зарплатному диапазону;
- `idx_vacancy_skills_skill_id` — поиск вакансий по навыкам;
- `idx_vacancy_views_user_id` — просмотры по пользователю;
- `idx_vacancies_search_vector` — GIN-индекс для полнотекстового поиска.

---

## Процедуры, функции и триггеры

### Functions

- `fn_normalize_text(text)` — нормализация текста;
- `fn_salary_midpoint(numeric, numeric)` — расчёт средней зарплаты диапазона;
- `fn_matched_skills_count(integer, integer)` — количество совпавших навыков;
- `fn_skill_match_ratio(integer, integer)` — доля совпадения навыков;
- `fn_vacancy_match_score(integer, integer)` — итоговый score рекомендации.

### Procedures

- `sp_create_demo_user(text, text, text, text)` — создание demo-пользователя;
- `sp_add_user_skill(text, text, integer)` — добавление навыка пользователю;
- `sp_refresh_search_vectors()` — обновление поисковых векторов;
- `sp_deactivate_low_quality_vacancies(integer)` — деактивация низкокачественных вакансий.

### Triggers

- `trg_vacancies_audit` — аудит INSERT / UPDATE / DELETE по вакансиям;
- `trg_vacancies_check_salary_range` — проверка зарплатного диапазона;
- `trg_vacancies_check_work_format` — нормализация и проверка формата работы;
- `trg_vacancies_normalize_title` — нормализация названия вакансии;
- `trg_vacancies_set_updated_at` — автоматическое обновление `updated_at`;
- `trg_vacancies_update_search_vector` — обновление полнотекстового поискового вектора.

---

## Redis

Redis используется как вспомогательная NoSQL-БД, подробнее расписал в документации проекта.

---

## Как запустить локально

### 1. Клонировать репозиторий

```sh
git clone <repo-url>
```

### 2. Создать `.env`

Создать файл `.env` в корне проекта:

```env
POSTGRES_DB=job_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Восстановить PostgreSQL database

Plain SQL:

```sh
createdb -U postgres job_db
psql -U postgres -d job_db -f dumps/vacancy_service_plain.sql
```

Или custom backup:

```sh
createdb -U postgres job_db
pg_restore -U postgres -d job_db dumps/vacancy_service_custom.backup
```

### 4. Запустить Redis

```sh
docker compose up -d
```

RedisInsight будет доступен по адресу:

```text
http://localhost:5540
```

### 5. Запустить backend

```sh
uvicorn app.main:app --reload
```

Swagger-документация:

```text
http://127.0.0.1:8000/docs
```

### 6. Запустить frontend

```sh
streamlit run frontend/streamlit_app.py
```

Frontend:

```text
http://localhost:8501
```

---

## Разработчик

`Муравьев Матвей Сергеевич / K3240 / 2026`
