# Использование Redis в проекте

## Роль Redis в архитектуре

В проекте Redis используется как NoSQL-хранилище для быстрых временных данных, кэша, счетчиков и очереди задач, когда основная постоянная база данных проекта — PostgreSQL. В ней хранятся вакансии, компании, навыки, пользователи, просмотры, избранные вакансии, представления, функции, процедуры и триггеры.

## Зачем Redis нужен в проекте

Redis используется для следующих задач:

1. кэширование результатов поисковых запросов;
2. кэширование карточек вакансий;
3. хранение последних поисков пользователя;
4. хранение популярных поисковых запросов;
5. хранение популярных навыков;
6. ограничение частоты запросов пользователя;
7. очередь задач на импорт вакансий.

## Запуск Redis

Redis запускается через Docker Compose.

Файл `docker-compose.yml` содержит два сервиса:

```yaml
services:
  redis:
    image: redis:7.4-alpine
    container_name: jobmatch_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]

  redisinsight:
    image: redis/redisinsight:latest
    container_name: jobmatch_redisinsight
    ports:
      - "5540:5540"
    depends_on:
      - redis

volumes:
  redis_data:
```

Запуск:

```bash
docker compose up -d
```

Проверка (потыкаться через CLI):

```bash
docker exec -it jobmatch_redis redis-cli
```

## RedisInsight

Для визуального просмотра Redis используется RedisInsight.

Адрес:

```text
http://localhost:5540
```

Параметры подключения:

```text
Host: localhost
Port: 6379
```

С RedisInsight смотрим ключи, типы данных, TTL, списки, хэши, sorted sets и streams.

## Используемые структуры

| Ключ                              | Тип            | Назначение                    |
| --------------------------------- | -------------- | ----------------------------- |
| `jobmatch:search_cache:*`         | String         | кэш результатов поиска        |
| `jobmatch:vacancy_card:*`         | Hash           | кэш карточки вакансии         |
| `jobmatch:user:*:recent_searches` | List           | последние поиски пользователя |
| `jobmatch:popular_queries`        | Sorted Set     | популярные запросы            |
| `jobmatch:popular_skills`         | Sorted Set     | популярные навыки             |
| `jobmatch:rate_limit:user:*`      | String counter | ограничение частоты запросов  |
| `jobmatch:stream:vacancy_import`  | Stream         | очередь задач импорта         |

## Демонстрационный Python-скрипт

Я проверял Redis-логику через файл и решил оставить его в доке:

```text
scripts/04_redis_demo.py
```

Скрипт выполняет:

1. подключение к Redis;
2. подключение к PostgreSQL;
3. выполнение поиска вакансий;
4. сохранение результата поиска в Redis;
5. повторный поиск с попаданием в кэш;
6. кэширование карточки вакансии;
7. сохранение последних поисков пользователя;
8. обновление популярных навыков;
9. работу rate limit;
10. добавление задач в Redis Stream;
11. вывод всех ключей Redis.

Запуск:

```bash
python scripts/04_redis_demo.py
```
