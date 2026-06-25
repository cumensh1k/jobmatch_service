SET search_path TO job_service;


CREATE OR REPLACE FUNCTION trg_fn_set_vacancy_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_set_updated_at ON vacancies;

CREATE TRIGGER trg_vacancies_set_updated_at
BEFORE UPDATE ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_set_vacancy_updated_at();


CREATE OR REPLACE FUNCTION trg_fn_update_vacancy_search_vector()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    NEW.search_vector =
        to_tsvector(
            'english',
            coalesce(NEW.title, '') || ' ' || coalesce(NEW.description_clean, '')
        );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_update_search_vector ON vacancies;

CREATE TRIGGER trg_vacancies_update_search_vector
BEFORE INSERT OR UPDATE OF title, description_clean ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_update_vacancy_search_vector();


CREATE OR REPLACE FUNCTION trg_fn_vacancy_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO vacancy_audit (
            vacancy_id,
            operation,
            old_data,
            new_data,
            changed_at
        )
        VALUES (
            NEW.vacancy_id,
            TG_OP,
            NULL,
            to_jsonb(NEW),
            NOW()
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO vacancy_audit (
            vacancy_id,
            operation,
            old_data,
            new_data,
            changed_at
        )
        VALUES (
            NEW.vacancy_id,
            TG_OP,
            to_jsonb(OLD),
            to_jsonb(NEW),
            NOW()
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO vacancy_audit (
            vacancy_id,
            operation,
            old_data,
            new_data,
            changed_at
        )
        VALUES (
            OLD.vacancy_id,
            TG_OP,
            to_jsonb(OLD),
            NULL,
            NOW()
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_audit ON vacancies;

CREATE TRIGGER trg_vacancies_audit
AFTER INSERT OR UPDATE OR DELETE ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_vacancy_audit();


CREATE OR REPLACE FUNCTION trg_fn_check_salary_range()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    IF NEW.salary_min IS NOT NULL AND NEW.salary_min < 0 THEN
        RAISE EXCEPTION 'salary_min cannot be negative. vacancy_id=%', NEW.vacancy_id;
    END IF;

    IF NEW.salary_max IS NOT NULL AND NEW.salary_max < 0 THEN
        RAISE EXCEPTION 'salary_max cannot be negative. vacancy_id=%', NEW.vacancy_id;
    END IF;

    IF NEW.salary_min IS NOT NULL
       AND NEW.salary_max IS NOT NULL
       AND NEW.salary_max < NEW.salary_min THEN
        RAISE EXCEPTION
            'salary_max cannot be less than salary_min. vacancy_id=%, salary_min=%, salary_max=%',
            NEW.vacancy_id,
            NEW.salary_min,
            NEW.salary_max;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_check_salary_range ON vacancies;

CREATE TRIGGER trg_vacancies_check_salary_range
BEFORE INSERT OR UPDATE OF salary_min, salary_max ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_check_salary_range();


CREATE OR REPLACE FUNCTION trg_fn_normalize_vacancy_title()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    NEW.title = fn_normalize_text(NEW.title);

    IF NEW.title = '' THEN
        RAISE EXCEPTION 'Vacancy title cannot be empty';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_normalize_title ON vacancies;

CREATE TRIGGER trg_vacancies_normalize_title
BEFORE INSERT OR UPDATE OF title ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_normalize_vacancy_title();


CREATE OR REPLACE FUNCTION trg_fn_check_work_format()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = job_service
AS $$
BEGIN
    IF NEW.work_format IS NULL THEN
        NEW.work_format = 'unknown';
    END IF;

    NEW.work_format = lower(trim(NEW.work_format));

    IF NEW.work_format NOT IN ('remote', 'office', 'hybrid', 'unknown') THEN
        RAISE EXCEPTION 'Invalid work_format: %', NEW.work_format;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vacancies_check_work_format ON vacancies;

CREATE TRIGGER trg_vacancies_check_work_format
BEFORE INSERT OR UPDATE OF work_format ON vacancies
FOR EACH ROW
EXECUTE FUNCTION trg_fn_check_work_format();