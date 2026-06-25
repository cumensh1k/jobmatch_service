from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from app.db.postgres import get_connection
from app.db.redis_client import get_redis_client
from app.services.analytics_service import (
    get_company_activity,
    get_popular_queries,
    get_salary_stats,
    get_top_skills,
    get_work_format_stats,
)
from app.services.recommendation_service import get_user_recommendations
from app.services.redis_service import get_recent_searches
from app.services.search_service import search_vacancies
from app.services.vacancy_service import get_vacancy_by_id
from app.schemas import (
    UserCreateRequest,
    UserProfileUpdateRequest,
    UserSkillLevelUpdateRequest,
    UserSkillsUpdateRequest,
)
from app.services.user_service import (
    add_user_skills,
    clear_user_target_profile,
    create_or_update_user,
    delete_all_user_skills,
    delete_user,
    delete_user_skill,
    get_categories,
    get_seniority_levels,
    get_skills,
    get_user_profile,
    get_users,
    update_user_profile,
    update_user_skill_level,
)


app = FastAPI(
    title="JobMatch Service",
    description="Intelligent vacancy search and analysis service with PostgreSQL and Redis",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    redis_client = get_redis_client()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS vacancy_count FROM job_service.vacancies;")
            row = cur.fetchone()

    return {
        "status": "ok",
        "postgres": "ok",
        "redis": "ok",
        "vacancy_count": row["vacancy_count"],
    }


@app.get("/vacancies/search")
def vacancies_search(
    query: str = Query(default="python developer"),
    user_id: int = Query(default=1),
    category: Optional[str] = Query(default=None),
    seniority: Optional[str] = Query(default=None),
    work_format: Optional[str] = Query(default=None),
    min_salary: Optional[float] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    redis_client = get_redis_client()

    return search_vacancies(
        redis_client=redis_client,
        query_text=query,
        user_id=user_id,
        category=category,
        seniority=seniority,
        work_format=work_format,
        min_salary=min_salary,
        limit=limit,
    )


@app.get("/vacancies/{vacancy_id}")
def vacancy_detail(vacancy_id: int) -> dict:
    redis_client = get_redis_client()

    vacancy = get_vacancy_by_id(redis_client, vacancy_id)

    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    return vacancy


@app.get("/analytics/skills")
def analytics_skills(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    redis_client = get_redis_client()
    return get_top_skills(redis_client, limit=limit)


@app.get("/analytics/salaries")
def analytics_salaries() -> list[dict]:
    return get_salary_stats()


@app.get("/analytics/companies")
def analytics_companies(limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
    return get_company_activity(limit=limit)


@app.get("/analytics/work-format")
def analytics_work_format() -> list[dict]:
    return get_work_format_stats()


@app.get("/analytics/popular-queries")
def analytics_popular_queries(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    redis_client = get_redis_client()
    return get_popular_queries(redis_client, limit=limit)


@app.get("/users/{user_id}/recent-searches")
def user_recent_searches(user_id: int) -> dict:
    redis_client = get_redis_client()

    return {
        "user_id": user_id,
        "recent_searches": get_recent_searches(redis_client, user_id),
    }


@app.get("/users/{user_id}/recommendations")
def user_recommendations(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return get_user_recommendations(user_id=user_id, limit=limit)


@app.get("/catalog/categories")
def catalog_categories() -> list[dict]:
    return get_categories()


@app.get("/catalog/seniority-levels")
def catalog_seniority_levels() -> list[dict]:
    return get_seniority_levels()


@app.get("/catalog/skills")
def catalog_skills(limit: int = Query(default=200, ge=1, le=1000)) -> list[dict]:
    return get_skills(limit=limit)


@app.post("/users")
def create_user(payload: UserCreateRequest) -> dict:
    try:
        return create_or_update_user(
            username=payload.username,
            category_name=payload.category_name,
            seniority_name=payload.seniority_name,
            location_city=payload.location_city,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/users")
def users_list() -> list[dict]:
    return get_users()


@app.get("/users/{user_id}/profile")
def user_profile(user_id: int) -> dict:
    try:
        return get_user_profile(user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/users/{user_id}/skills")
def update_user_skills(user_id: int, payload: UserSkillsUpdateRequest) -> dict:
    try:
        return add_user_skills(
            user_id=user_id,
            skills=[
                {
                    "skill_name": item.skill_name,
                    "skill_level": item.skill_level,
                }
                for item in payload.skills
            ],
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.patch("/users/{user_id}/profile")
def patch_user_profile(user_id: int, payload: UserProfileUpdateRequest) -> dict:
    try:
        return update_user_profile(
            user_id=user_id,
            username=payload.username,
            category_name=payload.category_name,
            seniority_name=payload.seniority_name,
            location_city=payload.location_city,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.put("/users/{user_id}/skills/{skill_name}")
def put_user_skill_level(
    user_id: int,
    skill_name: str,
    payload: UserSkillLevelUpdateRequest,
) -> dict:
    try:
        return update_user_skill_level(
            user_id=user_id,
            skill_name=skill_name,
            skill_level=payload.skill_level,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.delete("/users/{user_id}/skills/{skill_name}")
def remove_user_skill(user_id: int, skill_name: str) -> dict:
    try:
        return delete_user_skill(user_id=user_id, skill_name=skill_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.delete("/users/{user_id}/skills")
def remove_all_user_skills(user_id: int) -> dict:
    try:
        return delete_all_user_skills(user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.delete("/users/{user_id}/target-profile")
def remove_user_target_profile(user_id: int) -> dict:
    try:
        return clear_user_target_profile(user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.delete("/users/{user_id}")
def remove_user(user_id: int) -> dict:
    try:
        result = delete_user(user_id=user_id)

        redis_client = get_redis_client()
        redis_client.delete(f"jobmatch:user:{user_id}:recent_searches")
        redis_client.delete(f"jobmatch:rate_limit:user:{user_id}")

        return result
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))