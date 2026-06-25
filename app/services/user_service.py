from app.db.postgres import get_connection


def get_categories() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_id, name AS category_name, description
                FROM job_service.professional_categories
                ORDER BY name;
                """
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_seniority_levels() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT seniority_id, name AS seniority_name, rank_value
                FROM job_service.seniority_levels
                ORDER BY rank_value, name;
                """
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_skills(limit: int = 200) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT skill_id, name AS skill_name, skill_type
                FROM job_service.skills
                ORDER BY name
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def create_or_update_user(
    username: str,
    category_name: str,
    seniority_name: str,
    location_city: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_id
                FROM job_service.professional_categories
                WHERE name = %s;
                """,
                (category_name,),
            )
            category = cur.fetchone()

            if category is None:
                raise ValueError(f'Category "{category_name}" not found')

            cur.execute(
                """
                SELECT seniority_id
                FROM job_service.seniority_levels
                WHERE name = %s;
                """,
                (seniority_name,),
            )
            seniority = cur.fetchone()

            if seniority is None:
                raise ValueError(f'Seniority "{seniority_name}" not found')

            location_id = None

            if location_city:
                cur.execute(
                    """
                    SELECT location_id
                    FROM job_service.locations
                    WHERE city = %s
                    LIMIT 1;
                    """,
                    (location_city,),
                )
                location = cur.fetchone()

                if location is not None:
                    location_id = location["location_id"]

            cur.execute(
                """
                INSERT INTO job_service.users (
                    username,
                    target_category_id,
                    target_seniority_id,
                    preferred_location_id
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username)
                DO UPDATE SET
                    target_category_id = EXCLUDED.target_category_id,
                    target_seniority_id = EXCLUDED.target_seniority_id,
                    preferred_location_id = EXCLUDED.preferred_location_id
                RETURNING user_id;
                """,
                (
                    username,
                    category["category_id"],
                    seniority["seniority_id"],
                    location_id,
                ),
            )

            user = cur.fetchone()

    return get_user_profile(user["user_id"])


def add_user_skills(user_id: int, skills: list[dict]) -> dict:
    not_found = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            for skill in skills:
                skill_name = skill["skill_name"]
                skill_level = skill["skill_level"]

                cur.execute(
                    """
                    SELECT skill_id
                    FROM job_service.skills
                    WHERE lower(name) = lower(%s);
                    """,
                    (skill_name,),
                )
                skill_row = cur.fetchone()

                if skill_row is None:
                    not_found.append(skill_name)
                    continue

                cur.execute(
                    """
                    INSERT INTO job_service.user_skills (
                        user_id,
                        skill_id,
                        skill_level
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, skill_id)
                    DO UPDATE SET skill_level = EXCLUDED.skill_level;
                    """,
                    (
                        user_id,
                        skill_row["skill_id"],
                        skill_level,
                    ),
                )

    profile = get_user_profile(user_id)
    profile["skills_not_found"] = not_found

    return profile


def get_users() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    pc.name AS target_category,
                    sl.name AS target_seniority,
                    l.city AS preferred_city,
                    u.created_at
                FROM job_service.users u
                LEFT JOIN job_service.professional_categories pc
                    ON pc.category_id = u.target_category_id
                LEFT JOIN job_service.seniority_levels sl
                    ON sl.seniority_id = u.target_seniority_id
                LEFT JOIN job_service.locations l
                    ON l.location_id = u.preferred_location_id
                ORDER BY u.user_id;
                """
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_user_profile(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    pc.name AS target_category,
                    sl.name AS target_seniority,
                    l.city AS preferred_city,
                    u.created_at
                FROM job_service.users u
                LEFT JOIN job_service.professional_categories pc
                    ON pc.category_id = u.target_category_id
                LEFT JOIN job_service.seniority_levels sl
                    ON sl.seniority_id = u.target_seniority_id
                LEFT JOIN job_service.locations l
                    ON l.location_id = u.preferred_location_id
                WHERE u.user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            cur.execute(
                """
                SELECT
                    s.skill_id,
                    s.name AS skill_name,
                    s.skill_type,
                    us.skill_level
                FROM job_service.user_skills us
                JOIN job_service.skills s
                    ON s.skill_id = us.skill_id
                WHERE us.user_id = %s
                ORDER BY s.name;
                """,
                (user_id,),
            )
            skills = cur.fetchall()

    result = dict(user)
    result["skills"] = [dict(skill) for skill in skills]

    return result

def update_user_profile(
    user_id: int,
    username: str | None = None,
    category_name: str | None = None,
    seniority_name: str | None = None,
    location_city: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            if username is not None:
                cur.execute(
                    """
                    UPDATE job_service.users
                    SET username = %s
                    WHERE user_id = %s;
                    """,
                    (username, user_id),
                )

            if category_name is not None:
                cur.execute(
                    """
                    SELECT category_id
                    FROM job_service.professional_categories
                    WHERE name = %s;
                    """,
                    (category_name,),
                )
                category = cur.fetchone()

                if category is None:
                    raise ValueError(f'Category "{category_name}" not found')

                cur.execute(
                    """
                    UPDATE job_service.users
                    SET target_category_id = %s
                    WHERE user_id = %s;
                    """,
                    (category["category_id"], user_id),
                )

            if seniority_name is not None:
                cur.execute(
                    """
                    SELECT seniority_id
                    FROM job_service.seniority_levels
                    WHERE name = %s;
                    """,
                    (seniority_name,),
                )
                seniority = cur.fetchone()

                if seniority is None:
                    raise ValueError(f'Seniority "{seniority_name}" not found')

                cur.execute(
                    """
                    UPDATE job_service.users
                    SET target_seniority_id = %s
                    WHERE user_id = %s;
                    """,
                    (seniority["seniority_id"], user_id),
                )

            if location_city is not None:
                cur.execute(
                    """
                    SELECT location_id
                    FROM job_service.locations
                    WHERE city = %s
                    LIMIT 1;
                    """,
                    (location_city,),
                )
                location = cur.fetchone()

                if location is None:
                    raise ValueError(f'Location city "{location_city}" not found')

                cur.execute(
                    """
                    UPDATE job_service.users
                    SET preferred_location_id = %s
                    WHERE user_id = %s;
                    """,
                    (location["location_id"], user_id),
                )

    return get_user_profile(user_id)


def update_user_skill_level(
    user_id: int,
    skill_name: str,
    skill_level: int,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            cur.execute(
                """
                SELECT skill_id
                FROM job_service.skills
                WHERE lower(name) = lower(%s);
                """,
                (skill_name,),
            )
            skill = cur.fetchone()

            if skill is None:
                raise ValueError(f'Skill "{skill_name}" not found')

            cur.execute(
                """
                SELECT 1
                FROM job_service.user_skills
                WHERE user_id = %s
                  AND skill_id = %s;
                """,
                (user_id, skill["skill_id"]),
            )
            existing = cur.fetchone()

            if existing is None:
                raise ValueError(f'User does not have skill "{skill_name}"')

            cur.execute(
                """
                UPDATE job_service.user_skills
                SET skill_level = %s
                WHERE user_id = %s
                  AND skill_id = %s;
                """,
                (skill_level, user_id, skill["skill_id"]),
            )

    return get_user_profile(user_id)


def delete_user_skill(user_id: int, skill_name: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT skill_id
                FROM job_service.skills
                WHERE lower(name) = lower(%s);
                """,
                (skill_name,),
            )
            skill = cur.fetchone()

            if skill is None:
                raise ValueError(f'Skill "{skill_name}" not found')

            cur.execute(
                """
                DELETE FROM job_service.user_skills
                WHERE user_id = %s
                  AND skill_id = %s
                RETURNING user_id, skill_id;
                """,
                (user_id, skill["skill_id"]),
            )
            deleted = cur.fetchone()

            if deleted is None:
                raise ValueError(f'User does not have skill "{skill_name}"')

    return get_user_profile(user_id)


def delete_all_user_skills(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            cur.execute(
                """
                DELETE FROM job_service.user_skills
                WHERE user_id = %s;
                """,
                (user_id,),
            )

    return get_user_profile(user_id)


def clear_user_target_profile(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_service.users
                SET
                    target_category_id = NULL,
                    target_seniority_id = NULL,
                    preferred_location_id = NULL
                WHERE user_id = %s
                RETURNING user_id;
                """,
                (user_id,),
            )
            updated = cur.fetchone()

            if updated is None:
                raise ValueError(f"User with id={user_id} not found")

    return get_user_profile(user_id)


def delete_user(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username
                FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

            if user is None:
                raise ValueError(f"User with id={user_id} not found")

            cur.execute(
                """
                DELETE FROM job_service.vacancy_views
                WHERE user_id = %s;
                """,
                (user_id,),
            )

            cur.execute(
                """
                DELETE FROM job_service.users
                WHERE user_id = %s;
                """,
                (user_id,),
            )

    return {
        "deleted": True,
        "user_id": user["user_id"],
        "username": user["username"],
    }