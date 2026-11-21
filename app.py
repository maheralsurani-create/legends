import base64
import io
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from translations import UI_TEXT
import database as db

db.init_db()
st.set_page_config(page_title="Legends School & Kindergarten — SMS", layout="wide")

LOGO_CANDIDATES = [
    "logo.png",
    "logo.jpg",
    "logo.jpeg",
    "logo.webp",
    "assets/logo.png",
    "assets/logo.jpg",
]


def get_logo_path():
    for p in LOGO_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def get_logo_base64() -> str:
    p = get_logo_path()
    if not p:
        return ""
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_school_logo(width: int = 120) -> bool:
    p = get_logo_path()
    if p:
        st.image(p, width=width)
        return True
    return False


def is_valid_sqlite_db(raw_bytes: bytes) -> bool:
    if not raw_bytes or len(raw_bytes) < 100:
        return False
    return raw_bytes[:16] == b"SQLite format 3\x00"


def to_excel_bytes(sheets_dict: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, df_item in sheets_dict.items():
            safe_name = str(sheet_name)[:31]
            if df_item is not None and not df_item.empty:
                df_item.to_excel(writer, index=False, sheet_name=safe_name)
            else:
                pd.DataFrame({"Info": ["No data"]}).to_excel(writer, index=False, sheet_name=safe_name)
    return buf.getvalue()


if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
if "active_section" not in st.session_state:
    st.session_state.active_section = "dashboard"

lang = st.session_state.lang
T = UI_TEXT.get(lang, UI_TEXT["ar"])
page_dir = T["dir"]
page_align = T["align"]

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

        html, body, .main, .stSidebar, .stMarkdown, .stButton, .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {{
            font-family: 'Cairo', sans-serif !important;
            direction: {page_dir};
            text-align: {page_align};
        }}

        .stApp {{
            background: linear-gradient(135deg, #f4f7fb 0%, #eef2f7 100%);
        }}

        .login-card {{
            max-width: 460px;
            margin: 28px auto 14px auto;
            background: #ffffff;
            border-radius: 18px;
            padding: 28px 28px 22px 28px;
            box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
            border: 1px solid #e2e8f0;
        }}

        .login-logo-wrap {{
            display: flex;
            justify-content: center;
            margin-bottom: 12px;
        }}

        .login-logo-wrap img {{
            width: 110px;
            height: 110px;
            object-fit: contain;
            border-radius: 16px;
            padding: 6px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
        }}

        .login-title {{
            text-align: center !important;
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
        }}

        .login-sub {{
            text-align: center !important;
            font-size: 13px;
            color: #64748b;
            margin-bottom: 18px;
        }}

        .top-header-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 12px 18px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
            margin-bottom: 14px;
        }}

        .kpi-card {{
            border-radius: 14px;
            padding: 16px 18px;
            color: #ffffff;
            min-height: 112px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
            margin-bottom: 12px;
            transition: transform 0.15s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
        }}
        .kpi-title {{ font-size: 13px; opacity: 0.95; font-weight: 700; }}
        .kpi-val {{ font-size: 26px; font-weight: 800; margin: 5px 0; }}
        .kpi-sub {{ font-size: 12px; opacity: 0.92; }}

        .panel-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
        }}

        .stButton > button, .stFormSubmitButton > button {{
            border-radius: 10px !important;
            font-weight: 700 !important;
            border: 1px solid #cbd5e1 !important;
            transition: all 0.15s ease !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            border-color: #2563eb !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.logged_in:
    _, mid_col, _ = st.columns([1, 1.4, 1])
    with mid_col:
        l1, l2, l3 = st.columns(3)
        if l1.button("عربي", key="login_lang_ar", use_container_width=True):
            st.session_state.lang = "ar"
            st.rerun()
        if l2.button("كردي", key="login_lang_ku", use_container_width=True):
            st.session_state.lang = "ku"
            st.rerun()
        if l3.button("English", key="login_lang_en", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()

        logo_b64 = get_logo_base64()
        logo_html = (
            f'<div class="login-logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="Logo"></div>'
            if logo_b64
            else '<div class="login-logo-wrap"><div style="font-size:44px;">🏫</div></div>'
        )

        st.markdown(
            f"""
            <div class="login-card">
                {logo_html}
                <div class="login-title">{T['school_name']}</div>
                <div class="login-sub">{T['school_sub']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(f"#### {T['login']}")
            with st.form("login_form"):
                u = st.text_input(T["username"], placeholder=T["username"])
                p = st.text_input(T["password"], type="password", placeholder=T["password"])
                if st.form_submit_button(T["login_btn"], use_container_width=True):
                    role = db.verify_user(u.strip(), p)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.username = u.strip()
                        st.session_state.role = role
                        db.log_action(u.strip(), "LOGIN", "Logged into Legends SMS")
                        st.rerun()
                    else:
                        st.error(T["wrong_creds"])
    st.stop()

# الشريط العلوي العصري
st.markdown('<div class="top-header-card">', unsafe_allow_html=True)
top_l, top_m, top_r = st.columns([2.3, 3.8, 3.1])
with top_l:
    role_label = T["role_admin"] if st.session_state.role == "admin" else T["role_user"]
    st.markdown(f"**👤 {st.session_state.username}**  \n<span style='color:#64748b;font-size:13px;'>{role_label}</span>", unsafe_allow_html=True)
    if st.button(T["logout"], key="top_logout"):
        st.session_state.logged_in = False
        st.rerun()

with top_m:
    b1, b2, b3 = st.columns(3)
    if b1.button("English", key="btn_en", use_container_width=True):
        st.session_state.lang = "en"
        st.rerun()
    if b2.button("عربي", key="btn_ar", use_container_width=True):
        st.session_state.lang = "ar"
        st.rerun()
    if b3.button("كردي", key="btn_ku", use_container_width=True):
        st.session_state.lang = "ku"
        st.rerun()

with top_r:
    top_logo_col, top_title_col = st.columns([1, 3.2])
    with top_logo_col:
        render_school_logo(width=64)
    with top_title_col:
        st.markdown(f"### {T['school_name']}\n<span style='color:#64748b;font-size:13px;'>{T['school_sub']}</span>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# القائمة الجانبية
section_keys = [
    "dashboard",
    "students",
    "teachers",
    "parents",
    "stages",
    "subjects",
    "schedule",
    "attendance",
    "exams",
    "finance",
    "reports",
    "certificates",
    "users",
]

with st.sidebar:
    render_school_logo(width=110)
st.sidebar.markdown(f"### LEGENDS\n**{T['nav_title']}**")
for key in section_keys:
    is_active = st.session_state.active_section == key
    btn_label = f"▶ {T[key]}" if is_active else T[key]
    if st.sidebar.button(btn_label, key=f"nav_{key}", use_container_width=True):
        st.session_state.active_section = key
        st.rerun()

st.sidebar.markdown("---")
selected_year = st.sidebar.selectbox(T["year"], ["2026-2027", "2025-2026", "2027-2028"], index=0)

st_df = db.get_students(selected_year)
tx_df = db.get_transactions()
if not tx_df.empty:
    tx_df["t_date"] = pd.to_datetime(tx_df["t_date"]).dt.date

acad_df = db.get_all_academic_records(selected_year)
teachers_df = db.get_teachers(selected_year)
subjects_df = db.get_subjects(selected_year)
schedules_df = db.get_schedules(selected_year)

stage_labels = {
    "all": T.get("all_stages", "All"),
    "kg": T["stage_kg"],
    "primary": T["stage_pri"],
    "high": T["stage_high"],
}

sec = st.session_state.active_section

if sec == "dashboard":
    st.subheader(T["dashboard"])

    total_students = len(st_df) if not st_df.empty else 0
    kg_cnt = len(st_df[st_df["stage"] == "kg"]) if not st_df.empty else 0
    pri_cnt = len(st_df[st_df["stage"] == "primary"]) if not st_df.empty else 0
    high_cnt = len(st_df[st_df["stage"] == "high"]) if not st_df.empty else 0

    f_tx = tx_df[tx_df["academic_year"] == selected_year] if not tx_df.empty else tx_df
    income_val = float(f_tx[f_tx["t_type"] == "income"]["amount"].sum()) if not f_tx.empty else 0.0
    total_fee_val = float(st_df["tuition_fee"].sum()) if not st_df.empty else 0.0
    total_paid_val = float(st_df["paid_amount"].sum()) if not st_df.empty else 0.0
    remaining_val = max(0.0, total_fee_val - total_paid_val)

    today_str = str(datetime.today().date())
    absent_today = len(acad_df[(acad_df["rec_date"].astype(str) == today_str) & (acad_df["attendance"].astype(str).str.contains("غائب|نەبوو|Absent", case=False, na=False))]) if not acad_df.empty else 0
    present_cnt = len(acad_df[acad_df["attendance"].astype(str).str.contains("حاضر|ئامادە|Present", case=False, na=False)]) if not acad_df.empty else 0
    late_cnt = len(acad_df[acad_df["attendance"].astype(str).str.contains("متأخر|دواکەوتوو|Late", case=False, na=False)]) if not acad_df.empty else 0

    cards = [
        ("linear-gradient(135deg, #1d4ed8, #2563eb)", T["kpi_students"], f"{total_students:,}", T["kpi_students_sub"]),
        ("linear-gradient(135deg, #047857, #10b981)", T["kpi_teachers"], f"{len(teachers_df):,}", T["kpi_teachers_sub"]),
        ("linear-gradient(135deg, #6d28d9, #8b5cf6)", T["kpi_stages"], "3", T["kpi_stages_sub"]),
        ("linear-gradient(135deg, #b45309, #f59e0b)", T["kpi_absent"], f"{absent_today:,}", T["kpi_absent_sub"]),
        ("linear-gradient(135deg, #15803d, #22c55e)", T["kpi_income"], f"{income_val:,.0f}", T["currency"]),
        ("linear-gradient(135deg, #be123c, #f43f5e)", T["kpi_rem"], f"{remaining_val:,.0f}", T["currency"]),
    ]
    cols = st.columns(6)
    for col, (bg, title, val, sub) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="kpi-card" style="background:{bg};">
                <div class="kpi-title">{title}</div>
                <div class="kpi-val">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c_left, c_mid, c_right = st.columns([1.3, 1.1, 1.0])

    with c_left:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['chart_stages']}**")
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=[T["stage_kg"], T["stage_pri"], T["stage_high"]],
                    y=[kg_cnt, pri_cnt, high_cnt],
                    marker_color=["#2563eb", "#10b981", "#8b5cf6"],
                    text=[kg_cnt, pri_cnt, high_cnt],
                    textposition="outside",
                )
            ]
        )
        fig_bar.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10), yaxis=dict(dtick=1))
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_mid:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['chart_att']}**")
        donut_vals = [present_cnt, absent_today, late_cnt] if (present_cnt + absent_today + late_cnt) > 0 else [0, 0, 1]
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=[T["present"], T["absent"], T["late"]],
                    values=donut_vals,
                    hole=0.68,
                    marker_colors=["#10b981", "#ef4444", "#f59e0b"],
                    textinfo="none",
                )
            ]
        )
        fig_donut.add_annotation(text=f"{total_students}<br>{T['kpi_students']}", x=0.5, y=0.5, showarrow=False, font=dict(size=12))
        fig_donut.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10), showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['alerts']}**")
        rem_students = len(st_df[(st_df["tuition_fee"] - st_df["paid_amount"]) > 0]) if not st_df.empty else 0
        st.write(f"• {total_students} — {T['students']}")
        st.write(f"• {rem_students} — {T['kpi_rem']}")
        st.write(f"• {len(acad_df)} — {T['exams']}")
        st.markdown("</div>", unsafe_allow_html=True)

    b_left, b_mid, b_right = st.columns([1.3, 1.1, 1.0])
    with b_left:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['recent_activity']}**")
        if not acad_df.empty:
            st.dataframe(acad_df[["rec_date", "student_name", "subject", "score"]].head(5), use_container_width=True, hide_index=True)
        else:
            st.caption(T["section_ready"])
        st.markdown("</div>", unsafe_allow_html=True)

    with b_mid:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['today_schedule']}**")
        if not schedules_df.empty:
            st.dataframe(schedules_df[["day_name", "time_slot", "grade", "subject_name", "room"]].head(5), use_container_width=True, hide_index=True)
        else:
            st.dataframe(
                pd.DataFrame([
                    {"Time": "08:00 - 08:45", "Class": "KG-1 / A", "Subject": "Quran & Language", "Room": "R-101"},
                    {"Time": "08:50 - 09:35", "Class": "Grade 5 / A", "Subject": "Mathematics", "Room": "R-204"},
                ]),
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with b_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['quick_actions']}**")
        if st.button(T["add_student_btn"], use_container_width=True):
            st.session_state.active_section = "students"
            st.rerun()
        if st.button(T["add_pay_btn"], use_container_width=True):
            st.session_state.active_section = "finance"
            st.rerun()
        if st.button(T["open_reports_btn"], use_container_width=True):
            st.session_state.active_section = "reports"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif sec == "students":
    st.subheader(f"{T['students']} — {selected_year}")

    tab_add, tab_manage, tab_profile = st.tabs([
        T["add_student_btn"],
        f"{T['students']} ({T['kpi_students']})",
        T.get("tab_unified", "Unified Profile & Receipts"),
    ])

    with tab_add:
        with st.form("add_st_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            full_name = c1.text_input(T.get("full_name", "Full Name"))
            parent_name = c2.text_input(T.get("parent_name", "Guardian"))
            phone = c3.text_input(T.get("phone", "Phone"))

            s1, s2, s3, s4 = st.columns(4)
            st_stage = s1.selectbox(
                T["kpi_stages"],
                ["kg", "primary", "high"],
                format_func=lambda x: stage_labels[x],
            )
            st_grade = s2.text_input(T.get("grade", "Grade"), value="KG-1")
            st_sec = s3.text_input(T.get("section", "Section"), value="A")
            fee = s4.number_input(
                f"{T.get('tuition_fee', 'Tuition')} ({T['currency']})",
                min_value=0.0,
                step=100000.0,
                value=1500000.0,
            )

            if st.form_submit_button(T["add_student_btn"]) and full_name.strip():
                db.add_student(
                    selected_year,
                    full_name.strip(),
                    parent_name.strip(),
                    phone.strip(),
                    st_stage,
                    st_grade.strip(),
                    st_sec.strip(),
                    fee,
                    st.session_state.username,
                )
                st.success(T["add_student_btn"])
                st.rerun()

    with tab_manage:
        f_col1, f_col2 = st.columns([2, 1.3])
        search_q = f_col1.text_input(T.get("search_student", "Search"), key="manage_search_q").strip().lower()
        stage_filter = f_col2.selectbox(
            T.get("filter_stage", "Stage"),
            ["all", "kg", "primary", "high"],
            format_func=lambda x: stage_labels[x],
            key="manage_stage_filter",
        )

        view_students = st_df.copy()
        if not view_students.empty:
            if stage_filter != "all":
                view_students = view_students[view_students["stage"] == stage_filter]
            if search_q:
                view_students = view_students[
                    view_students["full_name"].astype(str).str.lower().str.contains(search_q, na=False)
                    | view_students["phone"].astype(str).str.lower().str.contains(search_q, na=False)
                    | view_students["id"].astype(str).str.contains(search_q, na=False)
                ]
            view_students["remaining_IQD"] = view_students["tuition_fee"] - view_students["paid_amount"]
            st.dataframe(view_students, use_container_width=True, hide_index=True)

            st.download_button(
                label=T.get("export_students_xl", "📥 Export Students (.xlsx)"),
                data=to_excel_bytes({"Students": view_students}),
                file_name=f"legends_students_{stage_filter}_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.markdown("---")
            st.markdown(f"### {T.get('edit_del_title', 'Edit / Delete Student')}")
            st_choices = {
                f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"])
                for _, r in view_students.iterrows()
            }
            if st_choices:
                target_label = st.selectbox(T.get("select_student_profile", "Select Student"), list(st_choices.keys()), key="edit_del_sel")
                target_id = st_choices[target_label]
                target_row = st_df[st_df["id"] == target_id].iloc[0]

                with st.form("edit_student_form"):
                    e1, e2, e3 = st.columns(3)
                    e_name = e1.text_input(T.get("full_name", "Full Name"), value=str(target_row["full_name"]))
                    e_parent = e2.text_input(T.get("parent_name", "Guardian"), value=str(target_row["parent_name"] or ""))
                    e_phone = e3.text_input(T.get("phone", "Phone"), value=str(target_row["phone"] or ""))

                    e4, e5, e6, e7 = st.columns(4)
                    stage_keys = ["kg", "primary", "high"]
                    cur_st_idx = stage_keys.index(target_row["stage"]) if target_row["stage"] in stage_keys else 0
                    e_stage = e4.selectbox(
                        T["kpi_stages"],
                        stage_keys,
                        index=cur_st_idx,
                        format_func=lambda x: stage_labels[x],
                    )
                    e_grade = e5.text_input(T.get("grade", "Grade"), value=str(target_row["grade"]))
                    e_sec = e6.text_input(T.get("section", "Section"), value=str(target_row["section"]))
                    e_fee = e7.number_input(
                        f"{T.get('tuition_fee', 'Tuition')} ({T['currency']})",
                        min_value=0.0,
                        step=100000.0,
                        value=float(target_row["tuition_fee"]),
                    )

                    if st.form_submit_button(T.get("save_changes", "Save")) and e_name.strip():
                        db.update_student(
                            target_id, e_name, e_parent, e_phone,
                            e_stage, e_grade, e_sec, e_fee, st.session_state.username,
                        )
                        st.rerun()

                if st.session_state.role == "admin":
                    confirm_del = st.checkbox(T.get("confirm_delete", "Confirm delete"), key="confirm_del_st")
                    if st.button(T.get("delete_student_btn", "Delete"), key="btn_del_st") and confirm_del:
                        db.delete_student(target_id, st.session_state.username)
                        st.rerun()

    with tab_profile:
        if not st_df.empty:
            p_col1, p_col2 = st.columns([1.3, 2.2])
            prof_stage = p_col1.selectbox(
                T.get("filter_stage", "Stage"),
                ["all", "kg", "primary", "high"],
                format_func=lambda x: stage_labels[x],
                key="prof_stage_filter",
            )
            prof_search = p_col1.text_input(T.get("search_student", "Search"), key="prof_search_q").strip().lower()

            prof_df = st_df.copy()
            if prof_stage != "all":
                prof_df = prof_df[prof_df["stage"] == prof_stage]
            if prof_search:
                prof_df = prof_df[
                    prof_df["full_name"].astype(str).str.lower().str.contains(prof_search, na=False)
                    | prof_df["phone"].astype(str).str.lower().str.contains(prof_search, na=False)
                ]

            if not prof_df.empty:
                prof_opts = {
                    f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"])
                    for _, r in prof_df.iterrows()
                }
                prof_label = p_col2.selectbox(T.get("select_student_profile", "Select Student"), list(prof_opts.keys()), key="prof_sel")
                sid = prof_opts[prof_label]
                s_info = st_df[st_df["id"] == sid].iloc[0]

                total_f = float(s_info["tuition_fee"])
                paid_f = float(s_info["paid_amount"])
                rem_f = max(0.0, total_f - paid_f)

                m1, m2, m3 = st.columns(3)
                m1.metric(T.get("total_fees", "Total Fees"), f"{total_f:,.0f} {T['currency']}")
                m2.metric(T.get("paid_amount", "Paid"), f"{paid_f:,.0f} {T['currency']}")
                m3.metric(T["kpi_rem"], f"{rem_f:,.0f} {T['currency']}")

                col_pay, col_acad = st.columns(2)
                with col_pay:
                    st.markdown(f"#### {T.get('pay_box_title', 'Payments')}")
                    with st.form("unified_pay_form", clear_on_submit=True):
                        pay_val = st.number_input(f"{T.get('pay_amount', 'Amount')} ({T['currency']})", min_value=0.0, step=50000.0)
                        pay_dt = st.date_input(T.get("pay_date", "Date"), datetime.today())
                        pay_nt = st.text_input(T.get("pay_note", "Note"), value="Installment")
                        if st.form_submit_button(T.get("pay_receipt_btn", "Pay")) and pay_val > 0:
                            rcpt_no = db.record_student_payment(sid, pay_val, pay_dt, pay_nt, st.session_state.username)
                            st.session_state["last_receipt"] = {
                                "receipt_no": rcpt_no,
                                "student": s_info["full_name"],
                                "grade": f"{s_info['grade']} / {s_info['section']}",
                                "amount": pay_val,
                                "date": str(pay_dt),
                                "note": pay_nt,
                                "remaining_after": max(0.0, total_f - (paid_f + pay_val)),
                            }
                            st.rerun()

                    if "last_receipt" in st.session_state and st.session_state["last_receipt"]["student"] == s_info["full_name"]:
                        lr = st.session_state["last_receipt"]
                        st.markdown(
                            f"""
                            <div class="panel-box" style="border: 2px solid #059669;">
                                <h4>{T['school_name']}</h4>
                                <p><strong>#</strong> {lr['receipt_no']} | <strong>{T.get('pay_date', 'Date')}:</strong> {lr['date']}</p>
                                <p><strong>{T.get('full_name', 'Student')}:</strong> {lr['student']} ({lr['grade']})</p>
                                <p><strong>{T.get('pay_amount', 'Amount')}:</strong> {lr['amount']:,.0f} {T['currency']}</p>
                                <p><strong>{T['kpi_rem']}:</strong> {lr['remaining_after']:,.0f} {T['currency']}</p>
                                <p><strong>{T.get('pay_note', 'Note')}:</strong> {lr['note']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.dataframe(db.get_student_payments(sid), use_container_width=True, hide_index=True)

                with col_acad:
                    st.markdown(f"#### {T.get('acad_history_title', 'Academic History')}")
                    st.dataframe(db.get_student_academic(sid), use_container_width=True, hide_index=True)

                st.download_button(
                    label=T.get("export_profile_xl", "📥 Export Profile (.xlsx)"),
                    data=to_excel_bytes({
                        "Student_Info": pd.DataFrame([s_info.to_dict()]),
                        "Payments": db.get_student_payments(sid),
                        "Academic": db.get_student_academic(sid),
                    }),
                    file_name=f"student_{sid}_profile.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

elif sec == "teachers":
    st.subheader(f"{T['teachers']} — {selected_year}")
    with st.form("add_teacher_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        t_name = c1.text_input(T.get("full_name", "Full Name"))
        t_spec = c2.text_input("Specialty / التخصص / پسپۆڕی")
        t_phone = c3.text_input(T.get("phone", "Phone"))
        c4, c5 = st.columns(2)
        t_stage = c4.selectbox(T["kpi_stages"], ["kg", "primary", "high"], format_func=lambda x: stage_labels[x])
        t_grade = c5.text_input(T.get("grade", "Grade"), value="All Grades")
        if st.form_submit_button("+ Teacher") and t_name.strip():
            db.add_teacher(selected_year, t_name, t_spec, t_phone, t_stage, t_grade, st.session_state.username)
            st.rerun()

    if not teachers_df.empty:
        st.dataframe(teachers_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Teachers": teachers_df}),
            file_name=f"legends_teachers_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if st.session_state.role == "admin":
            t_opts = {f"#{int(r['id'])} — {r['full_name']}": int(r["id"]) for _, r in teachers_df.iterrows()}
            del_t_sel = st.selectbox("Delete Teacher", list(t_opts.keys()), key="del_t_sel")
            if st.button("🗑️ Delete", key="btn_del_t"):
                db.delete_teacher(t_opts[del_t_sel], st.session_state.username)
                st.rerun()

elif sec == "parents":
    st.subheader(f"{T['parents']} — {selected_year}")
    if not st_df.empty:
        p_search = st.text_input(T.get("search_student", "Search"), key="parent_search_q").strip().lower()
        p_view = st_df[["id", "full_name", "parent_name", "phone", "stage", "grade", "section", "tuition_fee", "paid_amount"]].copy()
        p_view["remaining"] = p_view["tuition_fee"] - p_view["paid_amount"]
        if p_search:
            p_view = p_view[
                p_view["parent_name"].astype(str).str.lower().str.contains(p_search, na=False)
                | p_view["full_name"].astype(str).str.lower().str.contains(p_search, na=False)
                | p_view["phone"].astype(str).str.lower().str.contains(p_search, na=False)
            ]
        st.dataframe(p_view, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Parents": p_view}),
            file_name=f"legends_parents_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(T["section_ready"])

elif sec == "stages":
    st.subheader(f"{T['stages']} — {selected_year}")
    st_rows = []
    for s_key in ["kg", "primary", "high"]:
        s_students = len(st_df[st_df["stage"] == s_key]) if not st_df.empty else 0
        s_teachers = len(teachers_df[teachers_df["stage"] == s_key]) if not teachers_df.empty else 0
        s_subjects = len(subjects_df[subjects_df["stage"] == s_key]) if not subjects_df.empty else 0
        s_sched = len(schedules_df[schedules_df["stage"] == s_key]) if not schedules_df.empty else 0
        st_rows.append({
            T["kpi_stages"]: stage_labels[s_key],
            T["students"]: s_students,
            T["teachers"]: s_teachers,
            T["subjects"]: s_subjects,
            T["schedule"]: s_sched,
        })
    stages_summary_df = pd.DataFrame(st_rows)
    st.dataframe(stages_summary_df, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Excel (.xlsx)",
        data=to_excel_bytes({"Stages_Summary": stages_summary_df}),
        file_name=f"legends_stages_{selected_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

elif sec == "subjects":
    st.subheader(f"{T['subjects']} — {selected_year}")
    with st.form("add_subject_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        sub_stage = c1.selectbox(T["kpi_stages"], ["kg", "primary", "high"], format_func=lambda x: stage_labels[x])
        sub_grade = c2.text_input(T.get("grade", "Grade"), value="Grade 1")
        sub_name = c3.text_input("Subject / المادة / وانە")
        sub_teacher = c4.text_input(T["teachers"])
        if st.form_submit_button("+ Subject") and sub_name.strip():
            db.add_subject(selected_year, sub_stage, sub_grade, sub_name, sub_teacher, st.session_state.username)
            st.rerun()

    if not subjects_df.empty:
        st.dataframe(subjects_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Subjects": subjects_df}),
            file_name=f"legends_subjects_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if st.session_state.role == "admin":
            sub_opts = {f"#{int(r['id'])} — {r['subject_name']} ({r['grade']})": int(r["id"]) for _, r in subjects_df.iterrows()}
            del_sub_sel = st.selectbox("Delete Subject", list(sub_opts.keys()), key="del_sub_sel")
            if st.button("🗑️ Delete", key="btn_del_sub"):
                db.delete_subject(sub_opts[del_sub_sel], st.session_state.username)
                st.rerun()

elif sec == "schedule":
    st.subheader(f"{T['schedule']} — {selected_year}")
    with st.form("add_sched_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        sc_day = c1.selectbox("Day / اليوم / ڕۆژ", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"])
        sc_time = c2.text_input("Time / الوقت / کات", value="08:00 - 08:45")
        sc_stage = c3.selectbox(T["kpi_stages"], ["kg", "primary", "high"], format_func=lambda x: stage_labels[x])
        sc_grade = c4.text_input(T.get("grade", "Grade"), value="Grade 1")
        c5, c6, c7 = st.columns(3)
        sc_sec = c5.text_input(T.get("section", "Section"), value="A")
        sc_subj = c6.text_input("Subject / المادة / وانە")
        sc_room = c7.text_input("Room / القاعة / ژوور", value="R-101")
        if st.form_submit_button("+ Schedule") and sc_subj.strip():
            db.add_schedule(selected_year, sc_day, sc_time, sc_stage, sc_grade, sc_sec, sc_subj, sc_room, st.session_state.username)
            st.rerun()

    if not schedules_df.empty:
        st.dataframe(schedules_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Schedule": schedules_df}),
            file_name=f"legends_schedule_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if st.session_state.role == "admin":
            sc_opts = {f"#{int(r['id'])} — {r['day_name']} {r['time_slot']} ({r['subject_name']})": int(r["id"]) for _, r in schedules_df.iterrows()}
            del_sc_sel = st.selectbox("Delete Slot", list(sc_opts.keys()), key="del_sc_sel")
            if st.button("🗑️ Delete", key="btn_del_sc"):
                db.delete_schedule(sc_opts[del_sc_sel], st.session_state.username)
                st.rerun()

elif sec == "attendance":
    st.subheader(f"{T['attendance']} — {selected_year}")
    if not st_df.empty:
        st_map = {f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"]) for _, r in st_df.iterrows()}
        with st.form("att_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            att_st = c1.selectbox(T["students"], list(st_map.keys()))
            att_dt = c2.date_input("Date / التاريخ / بەروار", datetime.today())
            att_status = c3.selectbox(T["attendance"], [T["present"], T["absent"], T["late"]])
            if st.form_submit_button("💾 Save"):
                db.add_academic_record(st_map[att_st], selected_year, att_dt, att_status, "-", "-", st.session_state.username)
                st.rerun()

    if not acad_df.empty:
        st.dataframe(acad_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Attendance": acad_df}),
            file_name=f"legends_attendance_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

elif sec == "exams":
    st.subheader(f"{T['exams']} — {selected_year}")
    if not st_df.empty:
        st_map = {f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"]) for _, r in st_df.iterrows()}
        with st.form("exam_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            ex_st = c1.selectbox(T["students"], list(st_map.keys()))
            ex_dt = c2.date_input("Date / التاريخ / بەروار", datetime.today())
            ex_subj = c3.text_input("Subject / المادة / وانە", value="Mathematics")
            ex_score = c4.text_input("Score / الدرجة / نمرە", value="95 / 100")
            if st.form_submit_button("💾 Save") and ex_subj.strip() and ex_score.strip():
                db.add_academic_record(st_map[ex_st], selected_year, ex_dt, T["present"], ex_subj, ex_score, st.session_state.username)
                st.rerun()

    if not acad_df.empty:
        st.dataframe(acad_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Exams": acad_df}),
            file_name=f"legends_exams_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

elif sec == "certificates":
    st.subheader(f"{T['certificates']} — {selected_year}")
    if not st_df.empty:
        cert_map = {f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"]) for _, r in st_df.iterrows()}
        cert_sel = st.selectbox(T["students"], list(cert_map.keys()), key="cert_sel")
        cid = cert_map[cert_sel]
        c_row = st_df[st_df["id"] == cid].iloc[0]
        c_acad = db.get_student_academic(cid)

        st.markdown(
            f"""
            <div class="panel-box" style="border: 2px solid #1d4ed8;">
                <h3>{T['school_name']}</h3>
                <p>{T['school_sub']}</p>
                <hr>
                <p><strong>{T.get('full_name', 'Student')}:</strong> {c_row['full_name']}</p>
                <p><strong>{T['year']}:</strong> {c_row['academic_year']} | <strong>{T['kpi_stages']}:</strong> {stage_labels.get(c_row['stage'], c_row['stage'])} — {c_row['grade']} / {c_row['section']}</p>
                <p><strong>{T.get('parent_name', 'Guardian')}:</strong> {c_row['parent_name']} | <strong>{T.get('phone', 'Phone')}:</strong> {c_row['phone']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(c_acad, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({
                "Certificate_Student": pd.DataFrame([c_row.to_dict()]),
                "Grades_Attendance": c_acad,
            }),
            file_name=f"certificate_student_{cid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(T["section_ready"])

elif sec == "finance":
    st.subheader(T["finance"])
    if not st_df.empty:
        opts = {f"#{r['id']} - {r['full_name']}": int(r["id"]) for _, r in st_df.iterrows()}
        sel = st.selectbox(T["students"], list(opts.keys()))
        with st.form("pay_student_form", clear_on_submit=True):
            amt = st.number_input(f"{T['add_pay_btn']} ({T['currency']})", min_value=0.0, step=50000.0)
            note = st.text_input("Note / ملاحظة / تێبینی", value="Installment")
            p_date = st.date_input("Date / التاريخ / بەروار", datetime.today())
            if st.form_submit_button(T["add_pay_btn"]) and amt > 0:
                rcpt = db.record_student_payment(opts[sel], amt, p_date, note, st.session_state.username)
                st.success(f"Receipt #{rcpt}")
                st.rerun()

    st.markdown("---")
    with st.form("tx_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        t_stage = c1.selectbox(T["kpi_stages"], ["kg", "primary", "high"], format_func=lambda x: stage_labels[x])
        t_type = c2.selectbox("Type / النوع", ["income", "expense"])
        t_cat = c3.text_input("Category / البند", value="رسوم / مصروفات")
        t_amt = c4.number_input(f"Amount ({T['currency']})", min_value=0.0, step=50000.0)
        t_desc = st.text_input("Description / البيان")
        t_date = st.date_input("Date / التاريخ", datetime.today())
        if st.form_submit_button("Save TX") and t_amt > 0:
            db.add_transaction(selected_year, t_stage, t_type, t_cat, t_amt, t_desc, t_date, st.session_state.username)
            st.success("OK")
            st.rerun()

    if not tx_df.empty:
        st.dataframe(tx_df, use_container_width=True, hide_index=True)
        st.download_button(
            label="📥 Excel (.xlsx)",
            data=to_excel_bytes({"Treasury_Transactions": tx_df}),
            file_name=f"legends_transactions_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

elif sec == "reports":
    st.subheader(T["reports"])

    stage_rows = []
    f_tx_year = tx_df[tx_df["academic_year"] == selected_year] if not tx_df.empty else tx_df
    for s_key in ["kg", "primary", "high"]:
        s_inc = float(f_tx_year[(f_tx_year["stage"] == s_key) & (f_tx_year["t_type"] == "income")]["amount"].sum()) if not f_tx_year.empty else 0.0
        s_exp = float(f_tx_year[(f_tx_year["stage"] == s_key) & (f_tx_year["t_type"] == "expense")]["amount"].sum()) if not f_tx_year.empty else 0.0
        stage_rows.append({
            T["kpi_stages"]: stage_labels[s_key],
            T["kpi_income"]: s_inc,
            "Expenses": s_exp,
            "Net Budget": s_inc - s_exp,
        })
    budget_df = pd.DataFrame(stage_rows)
    st.dataframe(budget_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    if not tx_df.empty:
        period = st.selectbox("Period", ["daily", "weekly", "monthly", "yearly"])
        ref_d = st.date_input("Date", datetime.today())
        if period == "daily":
            rep = tx_df[tx_df["t_date"] == ref_d]
        elif period == "weekly":
            sw = ref_d - timedelta(days=ref_d.weekday())
            ew = sw + timedelta(days=6)
            rep = tx_df[(tx_df["t_date"] >= sw) & (tx_df["t_date"] <= ew)]
        elif period == "monthly":
            dt_c = pd.to_datetime(tx_df["t_date"])
            rep = tx_df[(dt_c.dt.month == ref_d.month) & (dt_c.dt.year == ref_d.year)]
        else:
            dt_c = pd.to_datetime(tx_df["t_date"])
            rep = tx_df[dt_c.dt.year == ref_d.year]

        st.dataframe(rep, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({
                "Transactions_Report": rep,
                "Stages_Budget": budget_df,
                "All_Payments": db.get_all_payments(),
                "Audit_Log": db.get_audit_log(),
            }),
            file_name=f"legends_full_report_{period}_{ref_d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")
    st.markdown(f"### {T.get('backup_restore_title', 'Backup & Restore (.db)')}")
    db.init_db()
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        if os.path.exists(db.DB_NAME):
            with open(db.DB_NAME, "rb") as fp:
                db_bytes = fp.read()
            st.download_button(
                label=T.get("backup_btn", "📥 Backup (.db)"),
                data=db_bytes,
                file_name=f"legends_backup_{datetime.today().strftime('%Y%m%d_%H%M')}.db",
                mime="application/octet-stream",
                use_container_width=True,
            )

    with b_col2:
        if st.session_state.role == "admin":
            up_db = st.file_uploader(T.get("restore_label", "Restore (.db)"), type=["db"], key="restore_db_uploader")
            if up_db is not None:
                uploaded_bytes = up_db.getbuffer().tobytes()
                if not is_valid_sqlite_db(uploaded_bytes):
                    st.error(T.get("invalid_db_file", "الملف المرفوع ليس قاعدة بيانات SQLite صالحة."))
                else:
                    if st.button(T.get("confirm_restore_btn", "♻️ تأكيد استعادة قاعدة البيانات"), key="btn_confirm_restore"):
                        safety_copy = f"{db.DB_NAME}.bak"
                        if os.path.exists(db.DB_NAME):
                            with open(db.DB_NAME, "rb") as cur_fp, open(safety_copy, "wb") as bak_fp:
                                bak_fp.write(cur_fp.read())
                        with open(db.DB_NAME, "wb") as out_f:
                            out_f.write(uploaded_bytes)
                        db.init_db()
                        db.log_action(st.session_state.username, "RESTORE_DB", f"Restored database from {up_db.name}")
                        st.success(T.get("restore_success", "تمت استعادة قاعدة البيانات وترقيتها بنجاح."))
                        st.rerun()
        else:
            st.info(T.get("admin_only_restore", "استعادة قاعدة البيانات متاحة لمدير النظام (Admin) فقط."))

    st.markdown("---")
    st.dataframe(db.get_audit_log(), use_container_width=True, hide_index=True)

elif sec == "users":
    st.subheader(T["users"])
    if st.session_state.role != "admin":
        st.warning("Admin only")
    else:
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            new_u = c1.text_input(T["username"])
            new_p = c2.text_input(T["password"], type="password")
            new_r = c3.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("Save User") and new_u.strip() and new_p.strip():
                db.create_user(new_u, new_p, new_r, st.session_state.username)
                st.success("OK")
                st.rerun()
        st.dataframe(db.get_users(), use_container_width=True, hide_index=True)

else:
    st.subheader(T.get(sec, sec))
    st.info(T["section_ready"])
