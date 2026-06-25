SET search_path TO job_service;

CREATE OR REPLACE FUNCTION fn_normalize_text(p_text TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SET search_path = job_service
IMMUTABLE
AS $$
BEGIN
    IF p_text IS NULL THEN
        RETURN '';
    END IF;

    RETURN trim(regexp_replace(p_text, '\s+', ' ', 'g'));
END;
$$;


CREATE OR REPLACE FUNCTION fn_salary_midpoint(
    p_salary_min NUMERIC,
    p_salary_max NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
SET search_path = job_service
IMMUTABLE
AS $$
BEGIN
    IF p_salary_min IS NOT NULL AND p_salary_max IS NOT NULL THEN
        RETURN ROUND((p_salary_min + p_salary_max) / 2, 2);
    ELSIF p_salary_min IS NOT NULL THEN
        RETURN p_salary_min;
    ELSIF p_salary_max IS NOT NULL THEN
        RETURN p_salary_max;
    ELSE
        RETURN NULL;
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION fn_matched_skills_count(
    p_user_id INT,
    p_vacancy_id INT
)
RETURNS INT
LANGUAGE sql
SET search_path = job_service
STABLE
AS $$
    SELECT COUNT(*)::INT
    FROM user_skills us
    JOIN vacancy_skills vs ON vs.skill_id = us.skill_id
    WHERE us.user_id = p_user_id
      AND vs.vacancy_id = p_vacancy_id;
$$;


CREATE OR REPLACE FUNCTION fn_skill_match_ratio(
    p_user_id INT,
    p_vacancy_id INT
)
RETURNS NUMERIC
LANGUAGE sql
SET search_path = job_service
STABLE
AS $$
    SELECT COALESCE(
        ROUND(
            (
                SELECT COUNT(*)::NUMERIC
                FROM user_skills us
                JOIN vacancy_skills vs ON vs.skill_id = us.skill_id
                WHERE us.user_id = p_user_id
                  AND vs.vacancy_id = p_vacancy_id
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)::NUMERIC
                    FROM vacancy_skills
                    WHERE vacancy_id = p_vacancy_id
                ),
                0
            ),
            4
        ),
        0
    );
$$;


CREATE OR REPLACE FUNCTION fn_vacancy_match_score(
    p_user_id INT,
    p_vacancy_id INT
)
RETURNS NUMERIC
LANGUAGE sql
SET search_path = job_service
STABLE
AS $$
    SELECT ROUND(
        (
            0.60 * fn_skill_match_ratio(p_user_id, p_vacancy_id)
            +
            0.20 * CASE
                WHEN u.target_category_id IS NOT NULL
                 AND u.target_category_id = v.category_id
                THEN 1 ELSE 0
            END
            +
            0.15 * CASE
                WHEN u.target_seniority_id IS NOT NULL
                 AND u.target_seniority_id = v.seniority_id
                THEN 1 ELSE 0
            END
            +
            0.05 * CASE
                WHEN u.preferred_location_id IS NOT NULL
                 AND u.preferred_location_id = v.location_id
                THEN 1 ELSE 0
            END
        )::NUMERIC,
        4
    )
    FROM users u
    JOIN vacancies v ON v.vacancy_id = p_vacancy_id
    WHERE u.user_id = p_user_id;
$$;


CREATE OR REPLACE PROCEDURE sp_create_demo_user(
    p_username TEXT,
    p_category_name TEXT,
    p_seniority_name TEXT,
    p_city TEXT DEFAULT NULL
)
LANGUAGE plpgsql
SET search_path = job_service
AS $$
DECLARE
    v_category_id INT;
    v_seniority_id INT;
    v_location_id INT;
BEGIN
    SELECT category_id
    INTO v_category_id
    FROM professional_categories
    WHERE name = p_category_name;

    SELECT seniority_id
    INTO v_seniority_id
    FROM seniority_levels
    WHERE name = p_seniority_name;

    IF p_city IS NOT NULL THEN
        SELECT location_id
        INTO v_location_id
        FROM locations
        WHERE city = p_city
        LIMIT 1;
    END IF;

    IF v_category_id IS NULL THEN
        RAISE EXCEPTION 'Category "%" not found', p_category_name;
    END IF;

    IF v_seniority_id IS NULL THEN
        RAISE EXCEPTION 'Seniority "%" not found', p_seniority_name;
    END IF;

    INSERT INTO users (
        username,
        target_category_id,
        target_seniority_id,
        preferred_location_id
    )
    VALUES (
        p_username,
        v_category_id,
        v_seniority_id,
        v_location_id
    )
    ON CONFLICT (username)
    DO UPDATE SET
        target_category_id = EXCLUDED.target_category_id,
        target_seniority_id = EXCLUDED.target_seniority_id,
        preferred_location_id = EXCLUDED.preferred_location_id;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_add_user_skill(
    p_username TEXT,
    p_skill_name TEXT,
    p_skill_level INT DEFAULT 1
)
LANGUAGE plpgsql
SET search_path = job_service
AS $$
DECLARE
    v_user_id INT;
    v_skill_id INT;
BEGIN
    SELECT user_id
    INTO v_user_id
    FROM users
    WHERE username = p_username;

    SELECT skill_id
    INTO v_skill_id
    FROM skills
    WHERE lower(name) = lower(p_skill_name);

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'User "%" not found', p_username;
    END IF;

    IF v_skill_id IS NULL THEN
        RAISE EXCEPTION 'Skill "%" not found', p_skill_name;
    END IF;

    INSERT INTO user_skills (
        user_id,
        skill_id,
        skill_level
    )
    VALUES (
        v_user_id,
        v_skill_id,
        p_skill_level
    )
    ON CONFLICT (user_id, skill_id)
    DO UPDATE SET
        skill_level = EXCLUDED.skill_level;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_refresh_search_vectors()
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    UPDATE vacancies
    SET search_vector =
        to_tsvector(
            'english',
            coalesce(title, '') || ' ' || coalesce(description_clean, '')
        );
END;
$$;


CREATE OR REPLACE PROCEDURE sp_deactivate_low_quality_vacancies(
    p_min_description_length INT DEFAULT 50
)
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    UPDATE vacancies
    SET is_active = FALSE,
        updated_at = NOW()
    WHERE description_clean IS NULL
       OR length(trim(description_clean)) < p_min_description_length;
END;
$$;