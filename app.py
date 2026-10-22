import hmac
import time
import datetime as dt
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------- config
TZ = ZoneInfo("Asia/Kolkata")
HEADERS = [
    "start_time", "duration_min", "session_type",
    "complexity", "concentration", "productivity",
    "notes",
]
LEVEL_LABELS = ["Category", "Sub-category", "Topic"]

# dict -> next level has children; list -> last level options; [] -> leaf
CATEGORIES = {
    "office": {
        "in line with my interest": [],
        "had to do": [],
    },
    "personal": {
        "study": ["dsa", "python", "system design"],
        "project": ["personal-finance-app", "pomodoro"],
        "finance": ["budget", "investment"],
        "reading book": [],
    },
}

st.set_page_config(page_title="focus tracker", page_icon="🍅")


# ----------------------------------------------------------------- auth
def check_password() -> bool:
    if "app_password" not in st.secrets:
        return True
    if st.session_state.get("authed"):
        return True
    entry = st.text_input("password", type="password")
    if entry and hmac.compare_digest(entry, st.secrets["app_password"]):
        st.session_state.authed = True
        st.rerun()
    elif entry:
        st.error("wrong password")
    return False


if not check_password():
    st.stop()


# ----------------------------------------------------------------- sheets
@st.cache_resource
def get_sheet():
    gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    ws = gc.open_by_key(st.secrets["sheet_id"]).worksheet("Sheet1")
    if not ws.row_values(1):
        ws.insert_row(HEADERS, 1)
    return ws


# @st.cache_data(ttl=60)
# def load_data() -> pd.DataFrame:
    # df = pd.DataFrame(get_sheet().get_all_records(), columns=HEADERS)
    # df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    # df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    # df["focus_rating"] = pd.to_numeric(df["focus_rating"], errors="coerce")
    # df = df.dropna(subset=["start_time", "duration_min"])
    # if df.empty:
    #     return df
    # for c in ("category_l1", "category_l2", "category_l3"):
    #     df[c] = df[c].replace("", "(none)")
    # df["hours"] = df["duration_min"] / 60
    # df["date"] = df["start_time"].dt.date
    # df["hour"] = df["start_time"].dt.hour
    # df["month"] = df["start_time"].dt.strftime("%Y-%m")
    # return df


# ----------------------------------------------------------------- session state
if "phase" not in st.session_state:
    st.session_state.update(phase="idle", start_ts=None, end_ts=None)


def start(minutes: int):
    now = time.time()
    st.session_state.update(
        phase="running", start_ts=now, end_ts=now + minutes * 60
    )


def stop_early():
    st.session_state.update(phase="done", end_ts=time.time(), auto_open=True)


def reset():
    st.session_state.update(phase="idle", start_ts=None, end_ts=None)


# ----------------------------------------------------------------- category picker
def pick_path(tree) -> list[str]:
    """Walk the category tree; one selectbox per level until a leaf."""
    path, node = [], tree
    while node:
        options = list(node) if isinstance(node, dict) else node
        depth = len(path)
        label = LEVEL_LABELS[depth] if depth < len(LEVEL_LABELS) else f"Level {depth + 1}"
        choice = st.selectbox(label, options, key=f"lvl{depth}_" + "|".join(path))
        path.append(choice)
        node = node[choice] if isinstance(node, dict) else None
    return path


# ----------------------------------------------------------------- end-of-session form
@st.dialog("how did the session go?")
def session_form():
    # task = st.text_input("What did you work on?")
    path = pick_path(CATEGORIES)
    l1, l2, l3 = (path + ["", "", ""])[:3]
    rating_complexity = st.slider("complexity", 1, 5)
    rating_concentration = st.slider("concentration", 1, 5)
    rating_productivity = st.slider("productivity", 1, 5)
    notes = st.text_area("notes")
    session_type = f'{l1} | {l2} | {l3}'

    c1, c2 = st.columns(2)
    if c1.button("save", type="primary"):
        s = st.session_state
        start_iso = dt.datetime.fromtimestamp(s.start_ts, TZ).isoformat(timespec="seconds")
        minutes = round((s.end_ts - s.start_ts) / 60, 1)
        get_sheet().append_row([start_iso, minutes, session_type, rating_complexity, rating_concentration, rating_productivity, notes])
        # load_data.clear()
        reset()
        st.rerun()
    if c2.button("discard"):
        reset()
        st.rerun()


# ----------------------------------------------------------------- focus tab
def focus_tab():
    phase = st.session_state.phase

    if phase == "idle":
        minutes = st.number_input("session length (in minutes)", 1, 180, 120, step=5)
        st.button("start session", type="primary", on_click=start, args=(minutes,))

    elif phase == "running":

        @st.fragment(run_every=1)
        def timer():
            left = int(st.session_state.end_ts - time.time())
            if left <= 0:
                st.session_state.update(phase="done", auto_open=True)
                st.rerun()  # full rerun so the dialog can open
            st.metric( label="time", value=f"{left // 60:02d}:{left % 60:02d}", label_visibility="collapsed")

        timer()
        st.button("give up", on_click=stop_early)

    elif phase == "done":
        st.success("session complete!")
        if st.session_state.pop("auto_open", False):
            session_form()
        if st.button("log session"):  # reopen if the dialog was dismissed
            session_form()


# ----------------------------------------------------------------- review tab
# def review_tab():
#     top = st.columns([3, 1])
#     if top[1].button("Refresh"):
#         load_data.clear()
#
#     df = load_data()
#     if df.empty:
#         st.info("No sessions logged yet.")
#         return
#
#     months = sorted(df["month"].unique(), reverse=True)
#     month = top[0].selectbox("Month", months)
#     target = st.number_input("Daily target (hours)", 0.0, 16.0, 4.0, step=0.5)
#     m = df[df["month"] == month]
#
#     k = st.columns(4)
#     k[0].metric("Focus hours", f"{m['hours'].sum():.1f}")
#     k[1].metric("Sessions", len(m))
#     k[2].metric("Active days", m["date"].nunique())
#     k[3].metric("Avg focus", f"{m['focus_rating'].mean():.1f} / 5")
#
#     st.subheader("Hours per day")
#     daily = m.groupby(["date", "category_l1"], as_index=False)["hours"].sum()
#     fig = px.bar(daily, x="date", y="hours", color="category_l1")
#     fig.add_hline(y=target, line_dash="dash", annotation_text="target")
#     st.plotly_chart(fig, use_container_width=True)
#
#     st.subheader("Where the time went")
#     st.plotly_chart(
#         px.sunburst(m, path=["category_l1", "category_l2", "category_l3"], values="hours"),
#         use_container_width=True,
#     )
#
#     st.subheader("Focus quality by start hour")
#     by_hour = m.groupby("hour", as_index=False)["focus_rating"].mean()
#     st.plotly_chart(px.bar(by_hour, x="hour", y="focus_rating"), use_container_width=True)


# ----------------------------------------------------------------- layout
st.title("focus tracker")
tab1, tab2 = st.tabs(["focus", "monthly review (to do)"])
with tab1:
    focus_tab()
# with tab2:
#     # review_tab()

# TODO
# passwords kaha jayenge
# deploy karo
# run test cases on phone
# aur test cases run karo
# documentation page banao
# sheet ka naam Sheet1 se v1-streamlit-data karo
