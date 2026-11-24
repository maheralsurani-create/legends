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


def localize_df(df: pd.DataFrame, T_dict: dict, st_labels: dict = None) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    if st_labels and "stage" in out.columns:
        out["stage"] = out["stage"].map(lambda x: st_labels.get(x, x))
    col_map = {
        "id": T_dict.get("col_id", "ID"),
        "payment_id": T_dict.get("col_id", "ID"),
        "student_id": T_dict.get("col_student_id", "Student ID"),
        "student_name": T_dict.get("col_student_name", "Student Name"),
        "academic_year": T_dict.get("col_academic_year", "Academic Year"),
        "full_name": T_dict.get("col_full_name", "Full Name"),
        "parent_name": T_dict.get("col_parent_name", "Guardian"),
        "phone": T_dict.get("col_phone", "Phone"),
        "stage": T_dict.get("col_stage", "Stage"),
        "grade": T_dict.get("col_grade", "Grade"),
        "section": T_dict.get("col_section", "Section"),
        "tuition_fee": T_dict.get("col_tuition_fee", "Annual Tuition"),
        "paid_amount": T_dict.get("col_paid_amount", "Paid"),
        "remaining": T_dict.get("col_remaining", "Remaining"),
        "remaining_IQD": T_dict.get("col_remaining", "Remaining"),
        "receipt_no": T_dict.get("col_receipt_no", "Receipt No."),
        "amount": T_dict.get("col_amount", "Amount"),
        "pay_date": T_dict.get("col_pay_date", "Payment Date"),
        "note": T_dict.get("col_note", "Note"),
        "created_by": T_dict.get("col_created_by", "Created By"),
        "rec_date": T_dict.get("col_rec_date", "Date"),
        "attendance": T_dict.get("col_attendance", "Attendance"),
        "subject": T_dict.get("col_subject", "Subject"),
        "score": T_dict.get("col_score", "Score"),
        "specialty": T_dict.get("col_specialty", "Specialty"),
        "subject_name": T_dict.get("col_subject_name", "Subject Name"),
        "teacher_name": T_dict.get("col_teacher_name", "Teacher"),
        "day_name": T_dict.get("col_day_name", "Day"),
        "time_slot": T_dict.get("col_time_slot", "Time Slot"),
        "room": T_dict.get("col_room", "Room"),
        "t_type": T_dict.get("col_t_type", "Type"),
        "category": T_dict.get("col_category", "Category"),
        "description": T_dict.get("col_description", "Description"),
        "t_date": T_dict.get("col_t_date", "Date"),
        "timestamp": T_dict.get("col_timestamp", "Timestamp"),
        "username": T_dict.get("col_username", "Username"),
        "action": T_dict.get("col_action", "Action"),
        "details": T_dict.get("col_details", "Details"),
        "role": T_dict.get("col_role", "Role"),
    }
    return out.rename(columns={k: v for k, v in col_map.items() if k in out.columns})


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
page_dir = T.get("dir", "rtl")
page_align = T.get("align", "right")

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

        @media (max-width: 768px) {{
            .login-card {{
                margin: 12px auto 10px auto;
                padding: 18px 16px;
            }}
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
                <div class="login-title">{T.get('school_name', 'Legends School & Kindergarten')}</div>
                <div class="login-sub">{T.get('school_sub', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(f"#### {T.get('login', 'Sign In')}")
            with st.form("login_form"):
                u = st.text_input(T.get("username", "Username"), placeholder=T.get("username", "Username"))
                p = st.text_input(T.get("password", "Password"), type="password", placeholder=T.get("password", "Password"))
                if st.form_submit_button(T.get("login_btn", "Login"), use_container_width=True):
                    role = db.verify_user(u.strip(), p)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.username = u.strip()
                        st.session_state.role = role
                        db.log_action(u.strip(), "LOGIN", "Logged into Legends SMS")
                        st.rerun()
                    else:
                        st.error(T.get("wrong_creds", "Invalid credentials"))
    st.stop()

st.markdown('<div class="top-header-card">', unsafe_allow_html=True)
top_l, top_m, top_r = st.columns([2.3, 3.8, 3.1])
with top_l:
    role_label = T.get("role_admin", "Admin") if st.session_state.role == "admin" else T.get("role_user", "Staff")
    st.markdown(f"**👤 {st.session_state.username}**  \n<span style='color:#64748b;font-size:13px;'>{role_label}</span>", unsafe_allow_html=True)
    if st.button(T.get("logout", "Logout"), key="top_logout"):
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
        st.markdown(f"### {T.get('school_name', 'Legends School')}\n<span style='color:#64748b;font-size:13px;'>{T.get('school_sub', '')}</span>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

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
st.sidebar.markdown(f"### LEGENDS\n**{T.get('nav_title', 'Navigation')}**")
for key in section_keys:
    is_active = st.session_state.active_section == key
    label_txt = T.get(key, key.capitalize())
    btn_label = f"▶ {label_txt}" if is_active else label_txt
    if st.sidebar.button(btn_label, key=f"nav_{key}", use_container_width=True):
        st.session_state.active_section = key
        st.rerun()

st.sidebar.markdown("---")
selected_year = st.sidebar.selectbox(T.get("year", "Academic Year"), ["2026-2027", "2025-2026", "2027-2028"], index=0)

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
    "kg": T.get("stage_kg", "KG"),
    "primary": T.get("stage_pri", "Basic"),
    "high": T.get("stage_high", "High"),
}

sec = st.session_state.active_section

if sec == "dashboard":
    st.subheader(T.get("dashboard", "Dashboard"))

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
        ("linear-gradient(135deg, #1d4ed8, #2563eb)", T.get("kpi_students", "Students"), f"{total_students:,}", T.get("kpi_students_sub", "")),
        ("linear-gradient(135deg, #047857, #10b981)", T.get("kpi_teachers", "Teachers"), f"{len(teachers_df):,}", T.get("kpi_teachers_sub", "")),
        ("linear-gradient(135deg, #6d28d9, #8b5cf6)", T.get("kpi_stages", "Stages"), "3", T.get("kpi_stages_sub", "")),
        ("linear-gradient(135deg, #b45309, #f59e0b)", T.get("kpi_absent", "Absent"), f"{absent_today:,}", T.get("kpi_absent_sub", "")),
        ("linear-gradient(135deg, #15803d, #22c55e)", T.get("kpi_income", "Income"), f"{income_val:,.0f}", T.get("currency", "IQD")),
        ("linear-gradient(135deg, #be123c, #f43f5e)", T.get("kpi_rem", "Remaining"), f"{remaining_val:,.0f}", T.get("currency", "IQD")),
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
        st.markdown(f"**{T.get('chart_stages', 'Students by Stage')}**")
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=[T.get("stage_kg", "KG"), T.get("stage_pri", "Basic"), T.get("stage_high", "High")],
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
        st.markdown(f"**{T.get('chart_att', 'Attendance')}**")
        donut_vals = [present_cnt, absent_today, late_cnt] if (present_cnt + absent_today + late_cnt) > 0 else [0, 0, 1]
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=[T.get("present", "Present"), T.get("absent", "Absent"), T.get("late", "Late")],
                    values=donut_vals,
                    hole=0.68,
                    marker_colors=["#10b981", "#ef4444", "#f59e0b"],
                    textinfo="none",
                )
            ]
        )
        fig_donut.add_annotation(text=f"{total_students}<br>{T.get('kpi_students', 'Students')}", x=0.5, y=0.5, showarrow=False, font=dict(size=12))
        fig_donut.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10), showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T.get('alerts', 'Alerts')}**")
        rem_students = len(st_df[(st_df["tuition_fee"] - st_df["paid_amount"]) > 0]) if not st_df.empty else 0
        st.write(f"• {total_students} — {T.get('students', 'Students')}")
        st.write(f"• {rem_students} — {T.get('kpi_rem', 'Remaining')}")
        st.write(f"• {len(acad_df)} — {T.get('exams', 'Exams')}")
        st.markdown("</div>", unsafe_allow_html=True)

    b_left, b_mid, b_right = st.columns([1.3, 1.1, 1.0])
    with b_left:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T.get('recent_activity', 'Recent Activity')}**")
        if not acad_df.empty:
            st.dataframe(localize_df(acad_df[["rec_date", "student_name", "subject", "score"]].head(5), T, stage_labels), use_container_width=True, hide_index=True)
        else:
            st.caption(T.get("section_ready", ""))
        st.markdown("</div>", unsafe_allow_html=True)

    with b_mid:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T.get('today_schedule', 'Today Schedule')}**")
        if not schedules_df.empty:
            st.dataframe(localize_df(schedules_df[["day_name", "time_slot", "grade", "subject_name", "room"]].head(5), T, stage_labels), use_container_width=True, hide_index=True)
        else:
            col_time_lbl = T.get("time", T.get("col_time_slot", "Time"))
            col_grade_lbl = T.get("grade", T.get("col_grade", "Grade"))
            col_subj_lbl = T.get("subject", T.get("col_subject", "Subject"))
            col_room_lbl = T.get("room", T.get("col_room", "Room"))
            st.dataframe(
                pd.DataFrame([
                    {col_time_lbl: "08:00 - 08:45", col_grade_lbl: "KG-1 / A", col_subj_lbl: "Quran & Language", col_room_lbl: "R-101"},
                    {col_time_lbl: "08:50 - 09:35", col_grade_lbl: "Grade 5 / A", col_subj_lbl: "Mathematics", col_room_lbl: "R-204"},
                ]),
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with b_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T.get('quick_actions', 'Quick Actions')}**")
        if st.button(T.get("add_student_btn", "+ Add Student"), use_container_width=True):
            st.session_state.active_section = "students"
            st.rerun()
        if st.button(T.get("add_pay_btn", "+ Record Payment"), use_container_width=True):
            st.session_state.active_section = "finance"
            st.rerun()
        if st.button(T.get("open_reports_btn", "Reports"), use_container_width=True):
            st.session_state.active_section = "reports"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif sec == "students":
    st.subheader(f"{T.get('students', 'Students')} — {selected_year}")

    tab_add, tab_manage, tab_profile = st.tabs([
        T.get("add_student_btn", "+ Add Student"),
        f"{T.get('students', 'Students')} ({T.get('kpi_students', 'Total')})",
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
                T.get("kpi_stages", "Stage"),
                ["kg", "primary", "high"],
                format_func=lambda x: stage_labels[x],
            )
            st_grade = s2.text_input(T.get("grade", "Grade"), value="KG-1")
            st_sec = s3.text_input(T.get("section", "Section"), value="A")
            fee = s4.number_input(
                f"{T.get('tuition_fee', 'Tuition')} ({T.get('currency', 'IQD')})",
                min_value=0.0,
                step=100000.0,
                value=1500000.0,
            )

            if st.form_submit_button(T.get("add_student_btn", "+ Add Student")) and full_name.strip():
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
                st.success(T.get("add_student_btn", "Saved"))
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
            st.dataframe(localize_df(view_students, T, stage_labels), use_container_width=True, hide_index=True)

            st.download_button(
                label=T.get("export_students_xl", "📥 Export Students (.xlsx)"),
                data=to_excel_bytes({"Students": localize_df(view_students, T, stage_labels)}),
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
                        T.get("kpi_stages", "Stage"),
                        stage_keys,
                        index=cur_st_idx,
                        format_func=lambda x: stage_labels[x],
                    )
                    e_grade = e5.text_input(T.get("grade", "Grade"), value=str(target_row["grade"]))
                    e_sec = e6.text_input(T.get("section", "Section"), value=str(target_row["section"]))
                    e_fee = e7.number_input(
                        f"{T.get('tuition_fee', 'Tuition')} ({T.get('currency', 'IQD')})",
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
                curr_lbl = T.get("currency", "IQD")

                m1, m2, m3 = st.columns(3)
                m1.metric(T.get("total_fees", "Total Fees"), f"{total_f:,.0f} {curr_lbl}")
                m2.metric(T.get("paid_amount", "Paid"), f"{paid_f:,.0f} {curr_lbl}")
                m3.metric(T.get("kpi_rem", "Remaining"), f"{rem_f:,.0f} {curr_lbl}")

                col_pay, col_acad = st.columns(2)
                with col_pay:
                    st.markdown(f"#### {T.get('pay_box_title', 'Payments')}")
                    with st.form("unified_pay_form", clear_on_submit=True):
                        rcpt_input = st.text_input(
                            T.get("receipt_no", "Receipt No."),
                            placeholder=T.get("receipt_no_ph", "REC-1001"),
                        )
                        pay_val = st.number_input(f"{T.get('pay_amount', 'Amount')} ({curr_lbl})", min_value=0.0, step=50000.0)
                        pay_dt = st.date_input(T.get("pay_date", "Date"), datetime.today())
                        pay_nt = st.text_input(T.get("pay_note", "Note"), value="Installment")
                        if st.form_submit_button(T.get("pay_receipt_btn", "Pay")) and pay_val > 0:
                            saved_rcpt = db.record_student_payment(
                                sid,
                                pay_val,
                                pay_dt,
                                pay_nt,
                                st.session_state.username,
                                receipt_no=rcpt_input,
                            )
                            st.session_state["last_receipt"] = {
                                "receipt_no": saved_rcpt,
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
                                <h4>{T.get('school_name', 'Legends School')}</h4>
                                <p><strong>{T.get('receipt_no', 'Receipt No.')}:</strong> {lr['receipt_no']} | <strong>{T.get('pay_date', 'Date')}:</strong> {lr['date']}</p>
                                <p><strong>{T.get('full_name', 'Student')}:</strong> {lr['student']} ({lr['grade']})</p>
                                <p><strong>{T.get('pay_amount', 'Amount')}:</strong> {lr['amount']:,.0f} {curr_lbl}</p>
                                <p><strong>{T.get('kpi_rem', 'Remaining')}:</strong> {lr['remaining_after']:,.0f} {curr_lbl}</p>
                                <p><strong>{T.get('pay_note', 'Note')}:</strong> {lr['note']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st_pay_df = db.get_student_payments(sid)
                    st.dataframe(localize_df(st_pay_df, T, stage_labels), use_container_width=True, hide_index=True)

                with col_acad:
                    st.markdown(f"#### {T.get('acad_history_title', 'Academic History')}")
                    st_acad_df = db.get_student_academic(sid)
                    st.dataframe(localize_df(st_acad_df, T, stage_labels), use_container_width=True, hide_index=True)

                st.download_button(
                    label=T.get("export_profile_xl", "📥 Export Profile (.xlsx)"),
                    data=to_excel_bytes({
                        "Student_Info": localize_df(pd.DataFrame([s_info.to_dict()]), T, stage_labels),
                        "Payments": localize_df(st_pay_df, T, stage_labels),
                        "Academic": localize_df(st_acad_df, T, stage_labels),
                    }),
                    file_name=f"student_{sid}_profile.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

elif sec == "teachers":
    st.subheader(f"{T.get('teachers', 'Teachers')} — {selected_year}")
    with st.form("add_teacher_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        t_name = c1.text_input(T.get("full_name", "Full Name"))
        t_spec = c2.text_input(T.get("specialty", "Specialty"))
        t_phone = c3.text_input(T.get("phone", "Phone"))
        c4, c5 = st.columns(2)
        t_stage = c4.selectbox(T.get("kpi_stages", "Stage"), ["kg", "primary", "high"], format_func=lambda x: stage_labels[x])
        t_grade = c5.text_input(T.get("grade", "Grade"), value="All Grades")
        if st.form_submit_button(f"+ {T.get('teachers', 'Teacher')}") and t_name.strip():
            db.add_teacher(selected_year, t_name, t_spec, t_phone, t_stage, t_grade, st.session_state.username)
            st.rerun()

    if not teachers_df.empty:
        st.dataframe(localize_df(teachers_df, T, stage_labels), use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Teachers": localize_df(teachers_df, T, stage_labels)}),
            file_name=f"legends_teachers_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if st.session_state.role == "admin":
            t_opts = {f"#{int(r['id'])} — {r['full_name']}": int(r["id"]) for _, r in teachers_df.iterrows()}
            del_t_sel = st.selectbox(T.get("teachers", "Teachers"), list(t_opts.keys()), key="del_t_sel")
            if st.button(T.get("delete_btn", "🗑️ Delete"), key="btn_del_t"):
                db.delete_teacher(t_opts[del_t_sel], st.session_state.username)
                st.rerun()

elif sec == "parents":
    st.subheader(f"{T.get('parents', 'Parents')} — {selected_year}")
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
        st.dataframe(localize_df(p_view, T, stage_labels), use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Excel (.xlsx)",
            data=to_excel_bytes({"Parents": localize_df(p_view, T, stage_labels)}),
            file_name=f"legends_parents_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(T.get("section_ready", ""))
