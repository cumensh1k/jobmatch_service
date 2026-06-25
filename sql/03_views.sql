SET search_path TO job_service;


CREATE OR REPLACE VIEW v_vacancy_cards AS
SELECT
    v.vacancy_id,
    v.title,
    c.name AS company_name,
    l.city AS location_city,
    l.country AS location_country,
    pc.name AS category_name,
    sl.name AS seniority_name,
    v.work_format,
    v.employment_type,
    v.salary_min,
    v.salary_max,
    v.salary_currency,
    v.is_active,
    v.published_at,
    v.job_posting_url,
    STRING_AGG(DISTINCT s.name, ', ' ORDER BY s.name) AS skills
FROM vacancies v
JOIN companies c ON c.company_id = v.company_id
JOIN locations l ON l.location_id = v.location_id
JOIN professional_categories pc ON pc.category_id = v.category_id
JOIN seniority_levels sl ON sl.seniority_id = v.seniority_id
LEFT JOIN vacancy_skills vs ON vs.vacancy_id = v.vacancy_id
LEFT JOIN skills s ON s.skill_id = vs.skill_id
GROUP BY
    v.vacancy_id,
    v.title,
    c.name,
    l.city,
    l.country,
    pc.name,
    sl.name,
    v.work_format,
    v.employment_type,
    v.salary_min,
    v.salary_max,
    v.salary_currency,
    v.is_active,
    v.published_at,
    v.job_posting_url;


CREATE OR REPLACE VIEW v_skill_demand AS
SELECT
    s.skill_id,
    s.name AS skill_name,
    s.skill_type,
    COUNT(DISTINCT vs.vacancy_id) AS vacancy_count,
    ROUND(
        COUNT(DISTINCT vs.vacancy_id)::numeric
        / NULLIF((SELECT COUNT(*) FROM vacancies WHERE is_active = TRUE), 0)
        * 100,
        2
    ) AS vacancy_share_percent
FROM skills s
JOIN vacancy_skills vs ON vs.skill_id = s.skill_id
JOIN vacancies v ON v.vacancy_id = vs.vacancy_id
WHERE v.is_active = TRUE
GROUP BY s.skill_id, s.name, s.skill_type
ORDER BY vacancy_count DESC;


CREATE OR REPLACE VIEW v_category_salary_stats AS
SELECT
    pc.category_id,
    pc.name AS category_name,
    COUNT(v.vacancy_id) AS total_vacancies,
    COUNT(v.salary_min) AS vacancies_with_salary_min,
    COUNT(v.salary_max) AS vacancies_with_salary_max,
    ROUND(AVG(v.salary_min), 2) AS avg_salary_min,
    ROUND(AVG(v.salary_max), 2) AS avg_salary_max,
    ROUND(AVG((v.salary_min + v.salary_max) / 2), 2) AS avg_salary_midpoint,
    MIN(v.salary_min) AS min_salary,
    MAX(v.salary_max) AS max_salary,
    v.salary_currency
FROM professional_categories pc
LEFT JOIN vacancies v ON v.category_id = pc.category_id
WHERE v.is_active = TRUE OR v.vacancy_id IS NULL
GROUP BY pc.category_id, pc.name, v.salary_currency
ORDER BY total_vacancies DESC;


CREATE OR REPLACE VIEW v_company_activity AS
SELECT
    c.company_id,
    c.name AS company_name,
    COUNT(v.vacancy_id) AS total_vacancies,
    COUNT(v.vacancy_id) FILTER (WHERE v.is_active = TRUE) AS active_vacancies,
    COUNT(DISTINCT v.category_id) AS category_count,
    COUNT(DISTINCT v.location_id) AS location_count,
    ROUND(AVG(v.salary_min), 2) AS avg_salary_min,
    ROUND(AVG(v.salary_max), 2) AS avg_salary_max
FROM companies c
LEFT JOIN vacancies v ON v.company_id = c.company_id
GROUP BY c.company_id, c.name
ORDER BY active_vacancies DESC;


CREATE OR REPLACE VIEW v_work_format_stats AS
SELECT
    work_format,
    COUNT(*) AS vacancy_count,
    ROUND(
        COUNT(*)::numeric / NULLIF((SELECT COUNT(*) FROM vacancies), 0) * 100,
        2
    ) AS vacancy_share_percent
FROM vacancies
GROUP BY work_format
ORDER BY vacancy_count DESC;


CREATE OR REPLACE VIEW v_user_recommendation_base AS
SELECT
    u.user_id,
    u.username,
    v.vacancy_id,
    v.title,
    c.name AS company_name,
    pc.name AS category_name,
    sl.name AS seniority_name,
    v.work_format,
    COUNT(us.skill_id) AS matched_skills_count,
    COUNT(vs.skill_id) AS vacancy_skills_count,
    ROUND(
        COUNT(us.skill_id)::numeric
        / NULLIF(COUNT(vs.skill_id), 0),
        4
    ) AS skill_match_ratio
FROM users u
JOIN vacancies v ON v.is_active = TRUE
JOIN companies c ON c.company_id = v.company_id
JOIN professional_categories pc ON pc.category_id = v.category_id
JOIN seniority_levels sl ON sl.seniority_id = v.seniority_id
LEFT JOIN vacancy_skills vs ON vs.vacancy_id = v.vacancy_id
LEFT JOIN user_skills us
    ON us.user_id = u.user_id
    AND us.skill_id = vs.skill_id
GROUP BY
    u.user_id,
    u.username,
    v.vacancy_id,
    v.title,
    c.name,
    pc.name,
    sl.name,
    v.work_format
ORDER BY skill_match_ratio DESC NULLS LAST, matched_skills_count DESC;


CREATE OR REPLACE VIEW v_database_summary AS
SELECT 'vacancies' AS entity_name, COUNT(*) AS row_count FROM vacancies
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'locations', COUNT(*) FROM locations
UNION ALL
SELECT 'skills', COUNT(*) FROM skills
UNION ALL
SELECT 'vacancy_skills', COUNT(*) FROM vacancy_skills
UNION ALL
SELECT 'categories', COUNT(*) FROM professional_categories
UNION ALL
SELECT 'seniority_levels', COUNT(*) FROM seniority_levels;