SET search_path TO job_service;

CREATE INDEX idx_vacancies_company_id
ON vacancies(company_id);

CREATE INDEX idx_vacancies_category_seniority
ON vacancies(category_id, seniority_id);

CREATE INDEX idx_vacancies_salary
ON vacancies(salary_min, salary_max);

CREATE INDEX idx_vacancy_skills_skill_id
ON vacancy_skills(skill_id);

CREATE INDEX idx_vacancy_views_user_id
ON vacancy_views(user_id);

ALTER TABLE vacancies
ADD COLUMN search_vector tsvector;

UPDATE vacancies
SET search_vector =
    to_tsvector('english',
        coalesce(title,'') || ' ' || coalesce(description_clean,'')
    );

CREATE INDEX idx_vacancies_search_vector
ON vacancies
USING GIN(search_vector);



EXPLAIN ANALYZE
SELECT *
FROM vacancies
WHERE search_vector @@ to_tsquery('english', 'python & developer');


EXPLAIN ANALYZE
SELECT *
FROM vacancies
WHERE category_id = 1
AND seniority_id = 2;


EXPLAIN ANALYZE
SELECT v.*
FROM vacancies v
JOIN vacancy_skills vs ON vs.vacancy_id = v.vacancy_id
WHERE vs.skill_id = 1;