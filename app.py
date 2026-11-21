import io
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from translations import LANG
import database as db

db.init_db()
st.set_page_config(page_title="LEGENDS School System", layout="wide")

lang_choice = st.sidebar.selectbox(
    "🌐 Language / کوردی / اللغة",
    ["ar", "ku", "en"],
    format_func=lambda x: {"ar": "العربية", "ku": "کوردی", "en": "English"}[x],
)
T = LANG[lang_choice]

st.markdown(
    f"""
    <style>
        .main, .stSidebar {{
            direction: {T['dir']};
            text-align: {T['align']};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.title(f"🏫 {T['brand']}")
    st.subheader(T["login"])
    with st.form("login_form"):
        u = st.text_input(T["username"])
        p = st.text_input(T["password"], type="password")
        if st.form_submit_button(T["login_btn"]):
            role = db.verify_user(u.strip(), p)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = u.strip()
                st.session_state.role = role
                db.log_action(u.strip(), "LOGIN", "Logged into system")
                st.rerun()
            else:
                st.error(T["wrong_creds"])
    st.info("Default Logins -> Admin: `admin` / `admin123` | Staff: `user` / `user123`")
    st.stop()

role_text = T["role_admin"] if st.session_state.role == "admin" else T["role_user"]
st.sidebar.markdown(f"**{T['welcome']} {st.session_state.username}**")
st.sidebar.caption(role_text)

year_options = ["2026-2027", "2025-2026", "2027-2028"]
selected_year = st.sidebar.selectbox(T["year"], year_options, index=0)

if st.sidebar.button(T["logout"]):
    st.session_state.logged_in = False
    st.rerun()

nav_items = [
    T["nav_dash"],
    T["nav_students"],
    T["nav_academic"],
    T["nav_finance"],
    T["nav_reports"],
    T["nav_backup"],
]
nav = st.sidebar.radio("Navigation", nav_items)

stage_map = {"kg": T["kg"], "primary": T["primary"], "high": T["high"]}
grades_by_stage = {
    "kg": ["KG-1", "KG-2"],
    "primary": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9"],
    "high": ["Grade 10", "Grade 11", "Grade 12"],
}
sections = ["A", "B", "C"]

tx_df = db.get_transactions()
if not tx_df.empty:
    tx_df["t_date"] = pd.to_datetime(tx_df["t_date"]).dt.date

st_df = db.get_students(selected_year)

# 1. لوحة القيادة والخزينة
if nav == T["nav_dash"]:
    st.title(f"📊 {T['nav_dash']} ({selected_year})")
    stage_f = st.selectbox(
        T["stage"],
        ["all", "kg", "primary", "high"],
        format_func=lambda x: T["all"] if x == "all" else stage_map[x],
    )

    f_tx = tx_df[tx_df["academic_year"] == selected_year] if not tx_df.empty else tx_df
    if stage_f != "all" and not f_tx.empty:
        f_tx = f_tx[f_tx["stage"] == stage_f]

    inc = f_tx[f_tx["t_type"] == "income"]["amount"].sum() if not f_tx.empty else 0.0
    exp = f_tx[f_tx["t_type"] == "expense"]["amount"].sum() if not f_tx.empty else 0.0
    net = inc - exp

    f_st = st_df if stage_f == "all" else st_df[st_df["stage"] == stage_f] if not st_df.empty else st_df
    total_fees = f_st["tuition_fee"].sum() if not f_st.empty else 0.0
    total_paid = f_st["paid_amount"].sum() if not f_st.empty else 0.0
    total_rem = total_fees - total_paid

    c1, c2, c3 = st.columns(3)
    c1.metric(T["income"], f"{inc:,.0f} IQD")
    c2.metric(T["expense"], f"{exp:,.0f} IQD")
    c3.metric("Treasury Net / صافي الخزينة", f"{net:,.0f} IQD")

    k1, k2, k3 = st.columns(3)
    k1.metric(T["total_fee"], f"{total_fees:,.0f} IQD")
    k2.metric(T["paid_amt"], f"{total_paid:,.0f} IQD")
    k3.metric(T["rem_amt"], f"{total_rem:,.0f} IQD")

    st.markdown("---")
    if not f_tx.empty:
        st.dataframe(f_tx, use_container_width=True)

# 2. إدارة الطلاب والملف الموحد
elif nav == T["nav_students"]:
    st.title(f"🎓 {T['nav_students']} ({selected_year})")
    tab1, tab2 = st.tabs([T["add_student"], T["search_student"]])

    with tab1:
        with st.form("new_student_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            full_name = c1.text_input(T["student_name"])
            parent_name = c2.text_input(T["parent_name"])
            phone = c3.text_input(T["phone"])

            s1, s2, s3, s4 = st.columns(4)
            st_stage = s1.selectbox(T["stage"], ["kg", "primary", "high"], format_func=lambda x: stage_map[x])
            st_grade = s2.selectbox(T["grade"], grades_by_stage[st_stage])
            st_sec = s3.selectbox(T["section"], sections)
            tuition_fee = s4.number_input(T["tuition_fee"], min_value=0.0, step=100000.0, value=2000000.0)

            if st.form_submit_button(T["add_student"]):
                if full_name.strip():
                    db.add_student(
                        selected_year, full_name.strip(), parent_name.strip(),
                        phone.strip(), st_stage, st_grade, st_sec, tuition_fee,
                        st.session_state.username,
                    )
                    st.success(T["student_saved"])
                    st.rerun()

    with tab2:
        q = st.text_input(T["search_student"]).strip().lower()
        view_df = st_df.copy()
        if not view_df.empty and q:
            view_df = view_df[
                view_df["full_name"].str.lower().str.contains(q, na=False)
                | view_df["phone"].str.lower().str.contains(q, na=False)
                | view_df["id"].astype(str).str.contains(q, na=False)
            ]
        if not view_df.empty:
            view_df["remaining_IQD"] = view_df["tuition_fee"] - view_df["paid_amount"]
            st.dataframe(view_df, use_container_width=True)

            options = {
                f"#{row['id']} - {row['full_name']} ({stage_map.get(row['stage'], row['stage'])} | {row['grade']} | {row['section']})": int(row["id"])
                for _, row in view_df.iterrows()
            }
            chosen_label = st.selectbox("Unified Student Profile / الملف الموحد", list(options.keys()))
            sid = options[chosen_label]
            s_row = st_df[st_df["id"] == sid].iloc[0]
            rem = float(s_row["tuition_fee"]) - float(s_row["paid_amount"])

            m1, m2, m3 = st.columns(3)
            m1.metric(T["total_fee"], f"{float(s_row['tuition_fee']):,.0f} IQD")
            m2.metric(T["paid_amt"], f"{float(s_row['paid_amount']):,.0f} IQD")
            m3.metric(T["rem_amt"], f"{rem:,.0f} IQD")

            p_col, a_col = st.columns(2)
            with p_col:
                st.subheader(T["pay_btn"])
                with st.form("pay_form", clear_on_submit=True):
                    p_amt = st.number_input(T["pay_amt"], min_value=0.0, step=50000.0)
                    p_date = st.date_input(T["date"], datetime.today())
                    p_note = st.text_input(T["pay_note"], value="Installment / قسط")
                    if st.form_submit_button(T["pay_btn"]) and p_amt > 0:
                        rcpt = db.record_student_payment(sid, p_amt, p_date, p_note, st.session_state.username)
                        st.success(f"{T['receipt_title']} #{rcpt} — {p_amt:,.0f} IQD — {s_row['full_name']}")
                        st.rerun()
                st.dataframe(db.get_student_payments(sid), use_container_width=True)

            with a_col:
                st.subheader(T["nav_academic"])
                st.dataframe(db.get_student_academic(sid), use_container_width=True)

# 3. العمل الأكاديمي (الحضور والدرجات)
elif nav == T["nav_academic"]:
    st.title(f"📚 {T['nav_academic']} ({selected_year})")
    if st_df.empty:
        st.info("No students registered for this year yet.")
    else:
        st_opts = {f"#{r['id']} - {r['full_name']} ({r['grade']} - {r['section']})": int(r["id"]) for _, r in st_df.iterrows()}
        with st.form("acad_form", clear_on_submit=True):
            sel_s = st.selectbox(T["student_name"], list(st_opts.keys()))
            c1, c2, c3, c4 = st.columns(4)
            r_date = c1.date_input(T["date"], datetime.today())
            att = c2.selectbox(T["attendance_status"], [T["present"], T["absent"], T["excused"]])
            subj = c3.text_input(T["subject"], value="Mathematics / الرياضيات")
            scr = c4.text_input(T["score"], value="90 / 100")
            if st.form_submit_button(T["save_acad"]):
                db.add_academic_record(st_opts[sel_s], selected_year, r_date, att, subj, scr, st.session_state.username)
                st.success(T["tx_saved"])

# 4. المالية، الدفعات والإيصالات
elif nav == T["nav_finance"]:
    st.title(f"💳 {T['nav_finance']} ({selected_year})")
    categories = [
        "Tuition / رسوم دراسية",
        "Registration / تسجيل",
        "Transport / نقل",
        "Salaries / رواتب",
        "Electricity / كهرباء",
        "Internet / إنترنت",
        "Maintenance / صيانة",
        "Supplies / مستلزمات",
    ]
    with st.form("fin_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        f_stage = c1.selectbox(T["stage"], ["kg", "primary", "high"], format_func=lambda x: stage_map[x])
        f_type = c2.radio(T["tx_type"], ["income", "expense"], format_func=lambda x: T[x], horizontal=True)
        f_cat = c3.selectbox(T["category"], categories)

        d1, d2, d3 = st.columns(3)
        f_amt = d1.number_input(T["amount"], min_value=0.0, step=25000.0)
        f_desc = d2.text_input(T["desc"])
        f_date = d3.date_input(T["date"], datetime.today())

        if st.form_submit_button(T["save_tx"]) and f_amt > 0:
            db.add_transaction(
                selected_year, f_stage, f_type, f_cat, f_amt, f_desc.strip(), f_date, st.session_state.username
            )
            st.success(T["tx_saved"])
            st.rerun()

# 5. التقارير و Excel وسجل التدقيق
elif nav == T["nav_reports"]:
    st.title(f"📑 {T['nav_reports']}")
    if tx_df.empty:
        st.warning("No treasury transactions available.")
    else:
        c1, c2 = st.columns(2)
        period = c1.selectbox(T["period"], ["daily", "weekly", "monthly", "yearly"], format_func=lambda x: T[x])
        ref_d = c2.date_input(T["date"], datetime.today())

        if period == "daily":
            rep = tx_df[tx_df["t_date"] == ref_d]
        elif period == "weekly":
            start_w = ref_d - timedelta(days=ref_d.weekday())
            end_w = start_w + timedelta(days=6)
            rep = tx_df[(tx_df["t_date"] >= start_w) & (tx_df["t_date"] <= end_w)]
        elif period == "monthly":
            dt_col = pd.to_datetime(tx_df["t_date"])
            rep = tx_df[(dt_col.dt.month == ref_d.month) & (dt_col.dt.year == ref_d.year)]
        else:
            dt_col = pd.to_datetime(tx_df["t_date"])
            rep = tx_df[dt_col.dt.year == ref_d.year]

        st.dataframe(rep, use_container_width=True)

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            rep.to_excel(writer, index=False, sheet_name="Treasury_Report")
        st.download_button(
            label=f"📥 {T['export_excel']}",
            data=buf.getvalue(),
            file_name=f"LEGENDS_{period}_{ref_d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        if st.session_state.role == "admin":
            st.markdown("---")
            del_id = st.number_input("Delete Transaction ID", min_value=1, step=1)
            if st.button("Delete TX"):
                db.delete_transaction(del_id, st.session_state.username)
                st.rerun()

    st.markdown("---")
    st.subheader(T["audit_log"])
    st.dataframe(db.get_audit_log(), use_container_width=True)

# 6. النسخ الاحتياطي والاستعادة
elif nav == T["nav_backup"]:
    st.title(f"💾 {T['nav_backup']}")
    with open(db.DB_NAME, "rb") as fp:
        st.download_button(
            label=f"⬇️ {T['backup_btn']}",
            data=fp.read(),
            file_name=f"legends_backup_{datetime.today().strftime('%Y%m%d')}.db",
            mime="application/octet-stream",
        )

    st.markdown("---")
    if st.session_state.role == "admin":
        st.warning(T["restore_warn"])
        up = st.file_uploader(T["restore_btn"], type=["db"])
        if up is not None:
            with open(db.DB_NAME, "wb") as out_f:
                out_f.write(up.getbuffer())
            db.log_action(st.session_state.username, "RESTORE_DB", f"Restored from {up.name}")
            st.success(T["restore_done"])
    else:
        st.info(T["admin_only"])