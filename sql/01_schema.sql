CREATE SCHEMA IF NOT EXISTS job_service;

SET search_path TO job_service;

CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    base_url TEXT
);

CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    website TEXT,
    industry TEXT
);

CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    country TEXT,
    city TEXT NOT NULL,
    is_remote_available BOOLEAN DEFAULT FALSE,
    UNIQUE(country, city)
);

CREATE TABLE professional_categories (
    category_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE seniority_levels (
    seniority_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    rank_value INT NOT NULL
);

CREATE TABLE vacancies (
    vacancy_id SERIAL PRIMARY KEY,

    source_id INT REFERENCES sources(source_id),
    external_id TEXT NOT NULL,

    company_id INT REFERENCES companies(company_id),
    location_id INT REFERENCES locations(location_id),

    category_id INT REFERENCES professional_categories(category_id),
    seniority_id INT REFERENCES seniority_levels(seniority_id),

    title TEXT NOT NULL,
    description_clean TEXT,

    employment_type TEXT,
    work_format TEXT CHECK (work_format IN ('remote', 'office', 'hybrid', 'unknown')),

    salary_min NUMERIC,
    salary_max NUMERIC,
    salary_currency TEXT,

    published_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    job_posting_url TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(source_id, external_id)
);

CREATE TABLE skills (
    skill_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    skill_type TEXT
);

CREATE TABLE vacancy_skills (
    vacancy_id INT REFERENCES vacancies(vacancy_id) ON DELETE CASCADE,
    skill_id INT REFERENCES skills(skill_id) ON DELETE CASCADE,

    confidence NUMERIC DEFAULT 1.0,
    extraction_method TEXT,

    PRIMARY KEY (vacancy_id, skill_id)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    target_category_id INT REFERENCES professional_categories(category_id),
    target_seniority_id INT REFERENCES seniority_levels(seniority_id),
    preferred_location_id INT REFERENCES locations(location_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_skills (
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    skill_id INT REFERENCES skills(skill_id) ON DELETE CASCADE,
    skill_level INT DEFAULT 1,

    PRIMARY KEY (user_id, skill_id)
);

CREATE TABLE favorite_vacancies (
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    vacancy_id INT REFERENCES vacancies(vacancy_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (user_id, vacancy_id)
);

CREATE TABLE vacancy_views (
    view_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    vacancy_id INT REFERENCES vacancies(vacancy_id),
    viewed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE import_batches (
    batch_id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(source_id),

    file_name TEXT,
    status TEXT,

    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,

    rows_total INT,
    rows_success INT,
    rows_failed INT
);

CREATE TABLE vacancy_audit (
    audit_id SERIAL PRIMARY KEY,
    vacancy_id INT,

    operation TEXT,
    old_data JSONB,
    new_data JSONB,

    changed_at TIMESTAMP DEFAULT NOW()
);