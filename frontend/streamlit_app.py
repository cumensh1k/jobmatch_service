from __future__ import annotations

from html import escape
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="JobMatch Service",
    layout="wide",
)


st.markdown(
    """
    <style>
    footer {visibility: hidden;}

    .small-muted {
        color: #8b949e;
        font-size: 0.9rem;
    }

    .profile-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }

    .vacancy-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }

    .metric-card {
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    .skill-chip {
        display: inline-block;
        padding: 6px 11px;
        margin: 4px 5px 4px 0;
        border-radius: 999px;
        background: rgba(255, 75, 75, 0.18);
        border: 1px solid rgba(255, 75, 75, 0.35);
        font-size: 0.92rem;
    }

    .source-postgres {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(30, 144, 255, 0.18);
        border: 1px solid rgba(30, 144, 255, 0.35);
        font-size: 0.9rem;
    }

    .source-redis {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(46, 204, 113, 0.18);
        border: 1px solid rgba(46, 204, 113, 0.35);
        font-size: 0.9rem;
    }

    .danger-zone {
        border: 1px solid rgba(255, 75, 75, 0.35);
        border-radius: 14px;
        padding: 18px 20px;
        margin-top: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API helpers
# =========================================================

def api_request(method: str, path: str, **kwargs) -> Any:
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(method, url, timeout=25, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as error:
        detail = None
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        raise RuntimeError(f"{response.status_code}: {detail}") from error
    except requests.RequestException as error:
        raise RuntimeError(f"Не удалось подключиться к backend: {error}") from error


def api_get(path: str, params: dict | None = None) -> Any:
    return api_request("GET", path, params=params)


def api_post(path: str, json_body: dict) -> Any:
    return api_request("POST", path, json=json_body)


def api_patch(path: str, json_body: dict) -> Any:
    return api_request("PATCH", path, json=json_body)


def api_put(path: str, json_body: dict) -> Any:
    return api_request("PUT", path, json=json_body)


def api_delete(path: str) -> Any:
    return api_request("DELETE", path)


# =========================================================
# Formatting helpers
# =========================================================

def safe_text(value: Any, fallback: str = "Не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def format_salary(vacancy: dict) -> str:
    salary_min = vacancy.get("salary_min")
    salary_max = vacancy.get("salary_max")
    currency = vacancy.get("salary_currency") or ""

    if salary_min in (None, "") and salary_max in (None, ""):
        return "Зарплата не указана"

    if salary_min not in (None, "") and salary_max not in (None, ""):
        return f"{salary_min} — {salary_max} {currency}".strip()

    if salary_min not in (None, ""):
        return f"от {salary_min} {currency}".strip()

    return f"до {salary_max} {currency}".strip()


def render_source_badge(source: str | None) -> None:
    if source == "rate_limited":
        st.error("Слишком много запросов. Попробуй позже.")


def render_skill_chips(skills: list[dict]) -> None:
    if not skills:
        st.caption("Навыки пока не добавлены")
        return

    chips = []

    for skill in skills:
        name = escape(safe_text(skill.get("skill_name")))
        level = safe_text(skill.get("skill_level"), fallback="?")
        chips.append(f'<span class="skill-chip">{name} · уровень {level}</span>')

    st.markdown(" ".join(chips), unsafe_allow_html=True)


def render_profile(profile: dict) -> None:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)

    st.subheader(safe_text(profile.get("username")))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Целевая профессия")
        st.write(f'**{safe_text(profile.get("target_category"))}**')

    with col2:
        st.caption("Грейд")
        st.write(f'**{safe_text(profile.get("target_seniority"))}**')

    with col3:
        st.caption("Город")
        st.write(f'**{safe_text(profile.get("preferred_city"))}**')

    st.caption("Навыки")
    render_skill_chips(profile.get("skills", []))

    st.markdown("</div>", unsafe_allow_html=True)


def render_vacancy_detail(vacancy: dict) -> None:
    render_source_badge(vacancy.get("source"))

    st.subheader(safe_text(vacancy.get("title")))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Компания")
        st.write(f'**{safe_text(vacancy.get("company_name"))}**')

    with col2:
        st.caption("Локация")
        city = safe_text(vacancy.get("location_city"))
        country = safe_text(vacancy.get("location_country"), fallback="")
        st.write(f"**{city} {country}**")

    with col3:
        st.caption("Формат")
        st.write(f'**{safe_text(vacancy.get("work_format"))}**')

    col4, col5, col6 = st.columns(3)

    with col4:
        st.caption("Категория")
        st.write(f'**{safe_text(vacancy.get("category_name"))}**')

    with col5:
        st.caption("Грейд")
        st.write(f'**{safe_text(vacancy.get("seniority_name"))}**')

    with col6:
        st.caption("Зарплата")
        st.write(f'**{format_salary(vacancy)}**')

    st.caption("Навыки")
    st.write(safe_text(vacancy.get("skills")))

    url = vacancy.get("job_posting_url")
    if url:
        st.link_button("Открыть вакансию на LinkedIn", url)


def render_vacancy_card(vacancy: dict, index: int, key_prefix: str) -> None:
    vacancy_id = vacancy.get("vacancy_id")

    with st.container(border=True):
        st.markdown(f"### {safe_text(vacancy.get('title'))}")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"Компания: **{safe_text(vacancy.get('company_name'))}**")
            st.write(f"Навыки: {safe_text(vacancy.get('skills'))}")

        with col2:
            st.write(f"Категория: **{safe_text(vacancy.get('category_name'))}**")
            st.write(f"Грейд: **{safe_text(vacancy.get('seniority_name'))}**")

        with col3:
            st.write(f"Формат: **{safe_text(vacancy.get('work_format'))}**")
            st.write(format_salary(vacancy))

        if st.button(
                "Открыть карточку",
                key=f"{key_prefix}_open_{vacancy_id}_{index}",
        ):
            vacancy_detail_dialog(int(vacancy_id))


def chart_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
):
    if df.empty:
        st.info("Нет данных для отображения")
        return

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                x,
                sort="-y",
                title=x_title,
                axis=alt.Axis(labelAngle=-35),
            ),
            y=alt.Y(y, title=y_title),
            tooltip=list(df.columns),
        )
        .properties(height=380, title=title)
    )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# State
# =========================================================

for key, default in {
    "current_user_id": None,
    "current_username": None,
    "search_items": [],
    "search_source": None,
    "recommendation_items": [],
    "recommendation_user_id": None,
    "last_message": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def load_users() -> list[dict]:
    return api_get("/users")


def load_current_profile() -> dict | None:
    user_id = st.session_state.get("current_user_id")

    if not user_id:
        return None

    try:
        return api_get(f"/users/{user_id}/profile")
    except Exception:
        st.session_state["current_user_id"] = None
        st.session_state["current_username"] = None
        return None


def set_current_user(user_id: int, username: str | None = None) -> None:
    st.session_state["current_user_id"] = user_id
    st.session_state["current_username"] = username


# =========================================================
# Dialogs
# =========================================================


@st.dialog("Карточка вакансии")
def vacancy_detail_dialog(vacancy_id: int):
    try:
        vacancy = api_get(f"/vacancies/{vacancy_id}")
        render_vacancy_detail(vacancy)
    except Exception as error:
        st.error("Не удалось открыть карточку вакансии")
        st.code(str(error))


@st.dialog("Удалить один навык")
def delete_one_skill_dialog(user_id: int):
    profile = api_get(f"/users/{user_id}/profile")
    skills = profile.get("skills", [])

    if not skills:
        st.info("У пользователя нет навыков для удаления")
        return

    skill_names = [skill["skill_name"] for skill in skills]
    skill_name = st.selectbox("Выбери навык", skill_names)

    st.warning(f'Будет удалён навык: "{skill_name}"')

    if st.button("Подтвердить удаление", type="primary"):
        api_delete(f"/users/{user_id}/skills/{skill_name}")
        st.session_state["last_message"] = f'Навык "{skill_name}" удалён'
        st.rerun()


@st.dialog("Удалить все навыки")
def delete_all_skills_dialog(user_id: int):
    st.warning("Будут удалены все навыки текущего пользователя.")

    if st.button("Подтвердить удаление всех навыков", type="primary"):
        api_delete(f"/users/{user_id}/skills")
        st.session_state["last_message"] = "Все навыки пользователя удалены"
        st.rerun()


@st.dialog("Сбросить профиль")
def reset_target_profile_dialog(user_id: int):
    st.warning("Будут сброшены целевая профессия, грейд и город.")

    if st.button("Подтвердить сброс", type="primary"):
        api_delete(f"/users/{user_id}/target-profile")
        st.session_state["last_message"] = "Целевой профиль сброшен"
        st.rerun()


@st.dialog("Удалить пользователя")
def delete_user_dialog(user_id: int):
    profile = api_get(f"/users/{user_id}/profile")
    username = profile.get("username")

    st.error(f'Пользователь "{username}" будет удалён полностью.')

    confirm = st.text_input(
        "Для подтверждения введи псевдоним пользователя",
        value="",
    )

    if st.button("Удалить пользователя", type="primary", disabled=confirm != username):
        api_delete(f"/users/{user_id}")
        st.session_state["current_user_id"] = None
        st.session_state["current_username"] = None
        st.session_state["last_message"] = f'Пользователь "{username}" удалён'
        st.rerun()


# =========================================================
# Initial backend check
# =========================================================

try:
    api_get("/health")
except Exception as error:
    st.error("Backend сейчас недоступен")
    st.code(str(error))
    st.stop()


# =========================================================
# Sidebar
# =========================================================

st.sidebar.title("JobMatch")

try:
    users = load_users()
except Exception as error:
    st.sidebar.error("Не удалось загрузить пользователей")
    st.sidebar.code(str(error))
    users = []


if users:
    user_options = {
        f'{user["username"]} · {user["target_category"] or "без профессии"} · {user["target_seniority"] or "без грейда"}': user
        for user in users
    }

    current_id = st.session_state.get("current_user_id")
    option_names = list(user_options.keys())

    default_index = 0
    if current_id:
        for i, name in enumerate(option_names):
            if user_options[name]["user_id"] == current_id:
                default_index = i
                break

    selected_option = st.sidebar.selectbox(
        "Текущий профиль",
        option_names,
        index=default_index,
    )

    selected_user = user_options[selected_option]

    if st.sidebar.button("Войти в профиль"):
        set_current_user(
            selected_user["user_id"],
            selected_user["username"],
        )
        st.session_state["last_message"] = (
            f'Активный профиль: {selected_user["username"]}'
        )
        st.rerun()

    if st.session_state.get("current_user_id") is None:
        set_current_user(
            selected_user["user_id"],
            selected_user["username"],
        )

    st.sidebar.caption(
        f'Активный профиль: {st.session_state.get("current_username") or selected_user["username"]}'
    )
else:
    st.sidebar.info("Профилей пока нет. Создай профиль в первом разделе.")


page = st.sidebar.radio(
    "Раздел",
    [
        "Профиль",
        "Рекомендации",
        "Поиск вакансий",
        "Аналитика",
        "Редактировать профиль",
    ],
)


if st.session_state.get("last_message"):
    st.success(st.session_state["last_message"])
    st.session_state["last_message"] = None


st.title("JobMatch Service")
st.caption("Сервис поиска, анализа вакансий и персональных рекомендаций")


# =========================================================
# Page: Profile
# =========================================================

if page == "Профиль":
    st.header("Профиль пользователя")

    categories = api_get("/catalog/categories")
    seniority_levels = api_get("/catalog/seniority-levels")
    skills_catalog = api_get("/catalog/skills", params={"limit": 1000})

    category_names = [item["category_name"] for item in categories]
    seniority_names = [item["seniority_name"] for item in seniority_levels]
    skill_names = [item["skill_name"] for item in skills_catalog]

    st.subheader("Создать или обновить профиль")

    col1, col2, col3 = st.columns(3)

    with col1:
        username = st.text_input("Псевдоним", value="video_demo_user")

    with col2:
        category_index = (
            category_names.index("Backend Developer")
            if "Backend Developer" in category_names
            else 0
        )

        category_name = st.selectbox(
            "Целевая профессия",
            category_names,
            index=category_index,
        )

    with col3:
        seniority_index = (
            seniority_names.index("Junior")
            if "Junior" in seniority_names
            else 0
        )

        seniority_name = st.selectbox(
            "Грейд",
            seniority_names,
            index=seniority_index,
        )

    location_city = st.text_input(
        "Город, необязательно",
        value="",
        placeholder="Например: New York",
    )

    if st.button("Сохранить профиль", type="primary"):
        payload = {
            "username": username,
            "category_name": category_name,
            "seniority_name": seniority_name,
            "location_city": location_city.strip() if location_city.strip() else None,
        }

        try:
            profile = api_post("/users", payload)
            set_current_user(profile["user_id"], profile["username"])
            st.session_state["last_message"] = "Профиль сохранён"
            st.rerun()
        except Exception as error:
            st.error("Не удалось сохранить профиль")
            st.code(str(error))

    st.divider()

    st.subheader("Добавить навыки")

    current_profile = load_current_profile()

    if not current_profile:
        st.info("Сначала создай или выбери профиль.")
    else:
        st.caption(
            f'Навыки будут добавлены активному профилю: {current_profile["username"]}'
        )

        selected_skills = st.multiselect(
            "Навыки",
            skill_names,
            default=[
                skill
                for skill in ["Python", "SQL", "Docker", "Git", "Django"]
                if skill in skill_names
            ],
        )

        skill_level = st.slider(
            "Уровень выбранных навыков",
            min_value=1,
            max_value=5,
            value=3,
        )

        if st.button("Добавить навыки", disabled=not selected_skills):
            payload = {
                "skills": [
                    {
                        "skill_name": skill,
                        "skill_level": skill_level,
                    }
                    for skill in selected_skills
                ]
            }

            try:
                api_post(f"/users/{current_profile['user_id']}/skills", payload)
                st.session_state["last_message"] = "Навыки добавлены"
                st.rerun()
            except Exception as error:
                st.error("Не удалось добавить навыки")
                st.code(str(error))

        st.divider()

        st.subheader("Текущий профиль")
        render_profile(load_current_profile())


# =========================================================
# Page: Recommendations
# =========================================================

elif page == "Рекомендации":
    st.header("Рекомендации")

    current_profile = load_current_profile()

    if not current_profile:
        st.info("Сначала создай или выбери профиль.")
        st.stop()

    render_profile(current_profile)

    if st.session_state.get("recommendation_user_id") != current_profile["user_id"]:
        st.session_state["recommendation_items"] = []
        st.session_state["recommendation_user_id"] = current_profile["user_id"]

    limit = st.slider("Количество рекомендаций", 5, 100, 20)

    if st.button("Получить рекомендации", type="primary"):
        try:
            items = api_get(
                f"/users/{current_profile['user_id']}/recommendations",
                params={"limit": limit},
            )

            st.session_state["recommendation_items"] = items
            st.session_state["recommendation_user_id"] = current_profile["user_id"]

        except Exception as error:
            st.error("Не удалось загрузить рекомендации")
            st.code(str(error))

    items = st.session_state.get("recommendation_items", [])

    if not items:
        st.caption("Нажми «Получить рекомендации», чтобы увидеть подходящие вакансии.")
    else:
        st.subheader("Подходящие вакансии")

        for index, item in enumerate(items, start=1):
            with st.container(border=True):
                st.markdown(f"### {index}. {safe_text(item.get('title'))}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.caption("Компания")
                    st.write(f'**{safe_text(item.get("company_name"))}**')

                with col2:
                    st.caption("Категория")
                    st.write(f'**{safe_text(item.get("category_name"))}**')

                with col3:
                    st.caption("Грейд")
                    st.write(f'**{safe_text(item.get("seniority_name"))}**')

                score = float(item.get("match_score") or 0)
                st.progress(min(score, 1.0))
                st.caption(f"Match score: {score:.2f}")

                st.write(
                    f'Совпавшие навыки: **{safe_text(item.get("matched_skills"), "0")}**'
                )
                st.write(
                    f'Skill ratio: **{safe_text(item.get("skill_ratio"), "0")}**'
                )

                vacancy_id = item.get("vacancy_id")

                if st.button(
                    "Открыть карточку",
                    key=f"recommendation_open_{vacancy_id}_{index}",
                ):
                    vacancy_detail_dialog(int(vacancy_id))


# =========================================================
# Page: Search
# =========================================================

elif page == "Поиск вакансий":
    st.header("Поиск вакансий")

    current_profile = load_current_profile()
    current_user_id = current_profile["user_id"] if current_profile else 1

    categories = api_get("/catalog/categories")
    seniority_levels = api_get("/catalog/seniority-levels")

    category_names = ["Любая"] + [item["category_name"] for item in categories]
    seniority_names = ["Любой"] + [item["seniority_name"] for item in seniority_levels]
    work_formats = ["Любой", "remote", "office", "hybrid", "unknown"]

    col1, col2, col3 = st.columns(3)

    with col1:
        query = st.text_input("Поисковый запрос", value="python developer")
        limit = st.slider("Количество вакансий", 5, 100, 20)

    with col2:
        category = st.selectbox("Категория", category_names)
        seniority = st.selectbox("Грейд", seniority_names)

    with col3:
        work_format = st.selectbox("Формат работы", work_formats)
        min_salary_enabled = st.checkbox("Указать минимальную зарплату")
        min_salary = None

        if min_salary_enabled:
            min_salary = st.number_input(
                "Минимальная зарплата",
                min_value=0.0,
                value=50000.0,
            )

    if st.button("Найти вакансии", type="primary"):
        params = {
            "query": query,
            "user_id": current_user_id,
            "limit": limit,
        }

        if category != "Любая":
            params["category"] = category

        if seniority != "Любой":
            params["seniority"] = seniority

        if work_format != "Любой":
            params["work_format"] = work_format

        if min_salary is not None:
            params["min_salary"] = min_salary

        try:
            result = api_get("/vacancies/search", params=params)
            st.session_state["search_items"] = result.get("items", [])
            st.session_state["search_source"] = result.get("source")
        except Exception as error:
            st.error("Не удалось выполнить поиск")
            st.code(str(error))

    if st.session_state.get("search_source"):
        render_source_badge(st.session_state["search_source"])

    items = st.session_state.get("search_items", [])

    if items:
        st.subheader("Результаты поиска")

        for index, vacancy in enumerate(items, start=1):
            render_vacancy_card(vacancy, index=index, key_prefix="search")


    else:
        st.caption("Выполни поиск, чтобы увидеть результаты.")


# =========================================================
# Page: Analytics
# =========================================================

elif page == "Аналитика":
    st.header("Аналитика")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Навыки",
            "Зарплаты",
            "Компании",
            "Формат работы",
            "Популярные запросы",
        ]
    )

    with tab1:
        st.subheader("Топ востребованных навыков")

        limit = st.slider("Количество навыков", 5, 100, 20)

        if st.button("Показать навыки"):
            result = api_get("/analytics/skills", params={"limit": limit})
            render_source_badge(result.get("source"))

            items = result.get("items", [])
            df = pd.DataFrame(items)

            if not df.empty:
                chart_bar(
                    df,
                    x="skill_name",
                    y="vacancy_count",
                    title="Востребованность навыков",
                    x_title="Навык",
                    y_title="Количество вакансий",
                )

                st.subheader("Лидеры")
                for item in items[:10]:
                    with st.container(border=True):
                        st.write(
                            f'**{safe_text(item.get("skill_name"))}** — '
                            f'{safe_text(item.get("vacancy_count"), "0")} вакансий'
                        )
            else:
                st.info("Нет данных")

    with tab2:
        st.subheader("Зарплаты по категориям")

        if st.button("Показать зарплаты"):
            items = api_get("/analytics/salaries")
            df = pd.DataFrame(items)

            if not df.empty:
                df_chart = df.dropna(subset=["avg_salary_midpoint"]).copy()

                if not df_chart.empty:
                    chart_bar(
                        df_chart,
                        x="category_name",
                        y="avg_salary_midpoint",
                        title="Средняя зарплата по категориям",
                        x_title="Категория",
                        y_title="Средняя зарплата",
                    )

                for item in items[:12]:
                    with st.container(border=True):
                        st.markdown(f"### {safe_text(item.get('category_name'))}")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Вакансий",
                                safe_text(item.get("total_vacancies"), "0"),
                            )

                        with col2:
                            st.metric(
                                "Средняя зарплата",
                                safe_text(item.get("avg_salary_midpoint")),
                            )

                        with col3:
                            st.metric(
                                "Валюта",
                                safe_text(item.get("salary_currency")),
                            )
            else:
                st.info("Нет данных")

    with tab3:
        st.subheader("Активность компаний")

        limit = st.slider("Количество компаний", 5, 100, 20)

        if st.button("Показать компании"):
            items = api_get("/analytics/companies", params={"limit": limit})
            df = pd.DataFrame(items)

            if not df.empty:
                chart_bar(
                    df,
                    x="company_name",
                    y="active_vacancies",
                    title="Компании по количеству активных вакансий",
                    x_title="Компания",
                    y_title="Активные вакансии",
                )

                for item in items[:10]:
                    with st.container(border=True):
                        st.write(
                            f'**{safe_text(item.get("company_name"))}** — '
                            f'{safe_text(item.get("active_vacancies"), "0")} активных вакансий'
                        )
            else:
                st.info("Нет данных")

    with tab4:
        st.subheader("Форматы работы")

        if st.button("Показать форматы"):
            items = api_get("/analytics/work-format")
            df = pd.DataFrame(items)

            if not df.empty:
                chart_bar(
                    df,
                    x="work_format",
                    y="vacancy_count",
                    title="Распределение вакансий по формату работы",
                    x_title="Формат",
                    y_title="Количество вакансий",
                )

                for item in items:
                    with st.container(border=True):
                        st.write(
                            f'**{safe_text(item.get("work_format"))}** — '
                            f'{safe_text(item.get("vacancy_count"), "0")} вакансий, '
                            f'{safe_text(item.get("vacancy_share_percent"), "0")}%'
                        )
            else:
                st.info("Нет данных")

    with tab5:
        st.subheader("Популярные поисковые запросы")

        if st.button("Показать запросы"):
            items = api_get("/analytics/popular-queries", params={"limit": 20})
            df = pd.DataFrame(items)

            if not df.empty:
                chart_bar(
                    df,
                    x="query_text",
                    y="count",
                    title="Популярные запросы пользователей",
                    x_title="Запрос",
                    y_title="Количество",
                )

                for item in items[:10]:
                    with st.container(border=True):
                        st.write(
                            f'**{safe_text(item.get("query_text"))}** — '
                            f'{safe_text(item.get("count"), "0")} раз'
                        )
            else:
                st.info("Пока нет популярных запросов")


# =========================================================
# Page: Edit profile
# =========================================================

elif page == "Редактировать профиль":
    st.header("Редактировать профиль")

    current_profile = load_current_profile()

    if not current_profile:
        st.info("Сначала создай или выбери профиль.")
        st.stop()

    render_profile(current_profile)

    st.divider()

    st.subheader("Обновить профиль")

    categories = api_get("/catalog/categories")
    seniority_levels = api_get("/catalog/seniority-levels")

    category_names = [item["category_name"] for item in categories]
    seniority_names = [item["seniority_name"] for item in seniority_levels]

    col1, col2, col3 = st.columns(3)

    with col1:
        new_username = st.text_input(
            "Псевдоним",
            value=current_profile.get("username") or "",
        )

    with col2:
        current_category = current_profile.get("target_category")
        category_index = (
            category_names.index(current_category)
            if current_category in category_names
            else 0
        )
        new_category = st.selectbox(
            "Целевая профессия",
            category_names,
            index=category_index,
        )

    with col3:
        current_seniority = current_profile.get("target_seniority")
        seniority_index = (
            seniority_names.index(current_seniority)
            if current_seniority in seniority_names
            else 0
        )
        new_seniority = st.selectbox(
            "Грейд",
            seniority_names,
            index=seniority_index,
        )

    new_city = st.text_input(
        "Город",
        value=current_profile.get("preferred_city") or "",
    )

    if st.button("Сохранить изменения", type="primary"):
        payload = {
            "username": new_username,
            "category_name": new_category,
            "seniority_name": new_seniority,
        }

        if new_city.strip():
            payload["location_city"] = new_city.strip()

        try:
            updated = api_patch(
                f"/users/{current_profile['user_id']}/profile",
                payload,
            )
            set_current_user(updated["user_id"], updated["username"])
            st.session_state["last_message"] = "Профиль обновлён"
            st.rerun()
        except Exception as error:
            st.error("Не удалось обновить профиль")
            st.code(str(error))

    st.divider()

    st.subheader("Изменить уровень навыка")

    skills = current_profile.get("skills", [])

    if not skills:
        st.caption("Навыки пока не добавлены")
    else:
        skill_names = [skill["skill_name"] for skill in skills]

        col1, col2 = st.columns([2, 1])

        with col1:
            selected_skill = st.selectbox("Навык", skill_names)

        with col2:
            new_level = st.slider("Новый уровень", 1, 5, 3)

        if st.button("Обновить уровень навыка"):
            try:
                api_put(
                    f"/users/{current_profile['user_id']}/skills/{selected_skill}",
                    {"skill_level": new_level},
                )
                st.session_state["last_message"] = "Уровень навыка обновлён"
                st.rerun()
            except Exception as error:
                st.error("Не удалось обновить навык")
                st.code(str(error))

    st.divider()

    st.subheader("Действия с профилем")

    with st.container(border=True):
        st.write("Удаление навыков и сброс настроек профиля")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Удалить один навык"):
                delete_one_skill_dialog(current_profile["user_id"])

        with col2:
            if st.button("Удалить все навыки"):
                delete_all_skills_dialog(current_profile["user_id"])

        with col3:
            if st.button("Сбросить профессию, грейд и город"):
                reset_target_profile_dialog(current_profile["user_id"])

    st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
    st.subheader("Удалить пользователя")
    st.write("Это действие полностью удалит профиль пользователя.")

    if st.button("Удалить текущего пользователя", type="primary"):
        delete_user_dialog(current_profile["user_id"])

    st.markdown("</div>", unsafe_allow_html=True)