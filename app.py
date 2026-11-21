import io
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from translations import UI_TEXT
import database as db

db.init_db()
st.set_page_config(page_title="Legends School & Kindergarten — SMS", layout="wide")

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
        .main, .stSidebar, .stMarkdown, .stButton, .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {{
            direction: {page_dir};
            text-align: {page_align};
        }}
        .kpi-card {{
            border-radius: 10px;
            padding: 14px 16px;
            color: #ffffff;
            min-height: 108px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            margin-bottom: 10px;
        }}
        .kpi-title {{ font-size: 13px; opacity: 0.95; font-weight: 600; }}
        .kpi-val {{ font-size: 26px; font-weight: 800; margin: 4px 0; }}
        .kpi-sub {{ font-size: 12px; opacity: 0.9; }}
        .panel-box {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.logged_in:
    st.title(f"🏫 {T['school_name']}")
    st.caption(T["school_sub"])
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
                db.log_action(u.strip(), "LOGIN", "Logged into Legends SMS")
                st.rerun()
            else:
                st.error(T["wrong_creds"])
    st.info("Default Logins -> Admin: `admin` / `admin123` | Staff: `user` / `user123`")
    st.stop()

# الشريط العلوي
top_l, top_m, top_r = st.columns([2.2, 4.2, 2.8])
with top_l:
    role_label = T["role_admin"] if st.session_state.role == "admin" else T["role_user"]
    st.markdown(f"**{st.session_state.username}** • {role_label}")
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
    st.markdown(f"### {T['school_name']}\n**{T['school_sub']}**")

st.markdown("---")

# القائمة الجانبية المترجمة بالكامل
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

    acad_all = []
    if not st_df.empty:
        for sid in st_df["id"].tolist():
            adf = db.get_student_academic(int(sid))
            if not adf.empty:
                acad_all.append(adf)
    acad_df = pd.concat(acad_all, ignore_index=True) if acad_all else pd.DataFrame(columns=["rec_date", "attendance", "subject", "score", "student_id"])

    today_str = str(datetime.today().date())
    absent_today = len(acad_df[(acad_df["rec_date"].astype(str) == today_str) & (acad_df["attendance"].astype(str).str.contains("غائب|نەبوو|Absent", case=False, na=False))]) if not acad_df.empty else 0
    present_cnt = len(acad_df[acad_df["attendance"].astype(str).str.contains("حاضر|ئامادە|Present", case=False, na=False)]) if not acad_df.empty else 0
    late_cnt = len(acad_df[acad_df["attendance"].astype(str).str.contains("متأخر|دواکەوتوو|Late", case=False, na=False)]) if not acad_df.empty else 0

    cards = [
        ("#1d4ed8", T["kpi_students"], f"{total_students:,}", T["kpi_students_sub"]),
        ("#059669", T["kpi_teachers"], "1", T["kpi_teachers_sub"]),
        ("#7c3aed", T["kpi_stages"], "2", T["kpi_stages_sub"]),
        ("#d97706", T["kpi_absent"], f"{absent_today:,}", T["kpi_absent_sub"]),
        ("#16a34a", T["kpi_income"], f"{income_val:,.0f}", T["currency"]),
        ("#e11d48", T["kpi_rem"], f"{remaining_val:,.0f}", T["currency"]),
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
            st.dataframe(acad_df[["rec_date", "student_id", "subject", "score"]].head(5), use_container_width=True, hide_index=True)
        else:
            st.caption(T["section_ready"])
        st.markdown("</div>", unsafe_allow_html=True)

    with b_mid:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown(f"**{T['today_schedule']}**")
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
        "الملف الموحد والإيصالات / Unified Profile & Receipts",
    ])

    with tab_add:
        with st.form("add_st_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            full_name = c1.text_input("الاسم الثلاثي / Full Name / ناوی سیانی")
            parent_name = c2.text_input("ولي الأمر / Guardian / بەخێوکەر")
            phone = c3.text_input("رقم الهاتف / Phone / مۆبایل")

            s1, s2, s3, s4 = st.columns(4)
            st_stage = s1.selectbox(
                T["kpi_stages"],
                ["kg", "primary", "high"],
                format_func=lambda x: {"kg": T["stage_kg"], "primary": T["stage_pri"], "high": T["stage_high"]}[x],
            )
            st_grade = s2.text_input("الصف / Grade / پۆل", value="KG-1")
            st_sec = s3.text_input("الشعبة / Section / هۆبە", value="A")
            fee = s4.number_input(
                f"الرسوم السنوية ({T['currency']})",
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
                st.success("تم تسجيل الطالب بنجاح / Student registered successfully.")
                st.rerun()

    with tab_manage:
        search_q = st.text_input("بحث بالاسم أو الهاتف أو الرقم / Search by name, phone or ID").strip().lower()
        stage_filter = st.selectbox(
            T["kpi_stages"],
            ["all", "kg", "primary", "high"],
            format_func=lambda x: "الكل / All / هەمووی" if x == "all" else {"kg": T["stage_kg"], "primary": T["stage_pri"], "high": T["stage_high"]}[x],
            key="st_stage_filter",
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
                label="📥 تصدير سجل الطلاب إلى Excel (.xlsx)",
                data=to_excel_bytes({"Students": view_students}),
                file_name=f"legends_students_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.markdown("---")
            st.markdown("### تعديل أو حذف بيانات طالب")
            st_choices = {
                f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"])
                for _, r in view_students.iterrows()
            }
            if st_choices:
                target_label = st.selectbox("اختر الطالب للتعديل أو الحذف", list(st_choices.keys()), key="edit_del_sel")
                target_id = st_choices[target_label]
                target_row = st_df[st_df["id"] == target_id].iloc[0]

                with st.form("edit_student_form"):
                    e1, e2, e3 = st.columns(3)
                    e_name = e1.text_input("الاسم الثلاثي", value=str(target_row["full_name"]))
                    e_parent = e2.text_input("ولي الأمر", value=str(target_row["parent_name"] or ""))
                    e_phone = e3.text_input("رقم الهاتف", value=str(target_row["phone"] or ""))

                    e4, e5, e6, e7 = st.columns(4)
                    stage_keys = ["kg", "primary", "high"]
                    cur_st_idx = stage_keys.index(target_row["stage"]) if target_row["stage"] in stage_keys else 0
                    e_stage = e4.selectbox(
                        T["kpi_stages"],
                        stage_keys,
                        index=cur_st_idx,
                        format_func=lambda x: {"kg": T["stage_kg"], "primary": T["stage_pri"], "high": T["stage_high"]}[x],
                    )
                    e_grade = e5.text_input("الصف", value=str(target_row["grade"]))
                    e_sec = e6.text_input("الشعبة", value=str(target_row["section"]))
                    e_fee = e7.number_input(
                        f"الرسوم السنوية ({T['currency']})",
                        min_value=0.0,
                        step=100000.0,
                        value=float(target_row["tuition_fee"]),
                    )

                    if st.form_submit_button("💾 حفظ التعديلات") and e_name.strip():
                        db.update_student(
                            target_id, e_name, e_parent, e_phone,
                            e_stage, e_grade, e_sec, e_fee, st.session_state.username,
                        )
                        st.success("تم تحديث بيانات الطالب بنجاح.")
                        st.rerun()

                if st.session_state.role == "admin":
                    confirm_del = st.checkbox("أؤكد حذف هذا الطالب وجميع دفعاته وسجلاته نهائياً", key="confirm_del_st")
                    if st.button("🗑️ حذف الطالب نهائياً", key="btn_del_st") and confirm_del:
                        db.delete_student(target_id, st.session_state.username)
                        st.success("تم حذف الطالب وسجلاته المرتبطة.")
                        st.rerun()
                else:
                    st.caption("حذف الطالب متاح لمدير النظام (Admin) فقط.")
        else:
            st.info("لا توجد سجلات طلاب مطابقة.")

    with tab_profile:
        if st_df.empty:
            st.info("سجل طالباً أولاً لعرض الملف الموحد وإصدار الإيصالات.")
        else:
            prof_opts = {
                f"#{int(r['id'])} — {r['full_name']} ({r['grade']} / {r['section']})": int(r["id"])
                for _, r in st_df.iterrows()
            }
            prof_label = st.selectbox("اختر الطالب لفتح الملف الموحد", list(prof_opts.keys()), key="prof_sel")
            sid = prof_opts[prof_label]
            s_info = st_df[st_df["id"] == sid].iloc[0]

            total_f = float(s_info["tuition_fee"])
            paid_f = float(s_info["paid_amount"])
            rem_f = max(0.0, total_f - paid_f)

            m1, m2, m3 = st.columns(3)
            m1.metric("إجمالي الرسوم", f"{total_f:,.0f} {T['currency']}")
            m2.metric("المدفوع", f"{paid_f:,.0f} {T['currency']}")
            m3.metric(T["kpi_rem"], f"{rem_f:,.0f} {T['currency']}")

            st.markdown(
                f"""
                <div class="panel-box">
                    <strong>الطالب:</strong> {s_info['full_name']} |
                    <strong>ولي الأمر:</strong> {s_info['parent_name']} |
                    <strong>الهاتف:</strong> {s_info['phone']}<br>
                    <strong>العام الدراسي:</strong> {s_info['academic_year']} |
                    <strong>المرحلة والصف والشعبة:</strong> {s_info['stage']} — {s_info['grade']} — {s_info['section']}
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_pay, col_acad = st.columns(2)
            with col_pay:
                st.markdown("#### تسجيل دفعة وإصدار إيصال")
                with st.form("unified_pay_form", clear_on_submit=True):
                    pay_val = st.number_input(f"مبلغ الدفعة ({T['currency']})", min_value=0.0, step=50000.0)
                    pay_dt = st.date_input("تاريخ الدفعة", datetime.today())
                    pay_nt = st.text_input("ملاحظات الدفعة", value="قسط دراسي / Installment")
                    if st.form_submit_button("🧾 تسجيل الدفعة وإصدار إيصال") and pay_val > 0:
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
                        st.success(f"تم تسجيل الدفعة وإصدار الإيصال رقم #{rcpt_no}")
                        st.rerun()

                if "last_receipt" in st.session_state and st.session_state["last_receipt"]["student"] == s_info["full_name"]:
                    lr = st.session_state["last_receipt"]
                    st.markdown(
                        f"""
                        <div class="panel-box" style="border: 2px solid #059669;">
                            <h4>إيصال قبض رسمي — {T['school_name']}</h4>
                            <p><strong>رقم الإيصال:</strong> #{lr['receipt_no']} | <strong>التاريخ:</strong> {lr['date']}</p>
                            <p><strong>اسم الطالب:</strong> {lr['student']} ({lr['grade']})</p>
                            <p><strong>المبلغ المستلم:</strong> {lr['amount']:,.0f} {T['currency']}</p>
                            <p><strong>المتبقي بعد الدفعة:</strong> {lr['remaining_after']:,.0f} {T['currency']}</p>
                            <p><strong>ملاحظات:</strong> {lr['note']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st_pays = db.get_student_payments(sid)
                st.dataframe(st_pays, use_container_width=True, hide_index=True)

            with col_acad:
                st.markdown("#### السجل الأكاديمي (الحضور والدرجات)")
                st_acad = db.get_student_academic(sid)
                st.dataframe(st_acad, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 تصدير الملف الموحد للطالب إلى Excel (.xlsx)",
                data=to_excel_bytes({
                    "Student_Info": pd.DataFrame([s_info.to_dict()]),
                    "Payments": db.get_student_payments(sid),
                    "Academic": db.get_student_academic(sid),
                }),
                file_name=f"student_{sid}_profile.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

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
    if not tx_df.empty:
        st.dataframe(tx_df, use_container_width=True)

elif sec == "reports":
    st.subheader(T["reports"])

    # جدول ميزانية المراحل الثلاث للعام الدراسي المحدد
    stage_rows = []
    f_tx_year = tx_df[tx_df["academic_year"] == selected_year] if not tx_df.empty else tx_df
    for s_key, s_label in [("kg", T["stage_kg"]), ("primary", T["stage_pri"]), ("high", T["stage_high"])]:
        s_inc = float(f_tx_year[(f_tx_year["stage"] == s_key) & (f_tx_year["t_type"] == "income")]["amount"].sum()) if not f_tx_year.empty else 0.0
        s_exp = float(f_tx_year[(f_tx_year["stage"] == s_key) & (f_tx_year["t_type"] == "expense")]["amount"].sum()) if not f_tx_year.empty else 0.0
        stage_rows.append({
            T["kpi_stages"]: s_label,
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

        st.dataframe(rep, use_container_width=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            rep.to_excel(writer, index=False, sheet_name="Transactions_Report")
            budget_df.to_excel(writer, index=False, sheet_name="Stages_Budget")
        st.download_button(
            "Excel",
            data=buf.getvalue(),
            file_name=f"legends_{period}_{ref_d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")
    with open(db.DB_NAME, "rb") as fp:
        st.download_button(
            "Backup (.db)",
            data=fp.read(),
            file_name=f"legends_backup_{datetime.today().strftime('%Y%m%d')}.db",
            mime="application/octet-stream",
        )
    if st.session_state.role == "admin":
        up = st.file_uploader("Restore (.db)", type=["db"])
        if up is not None:
            with open(db.DB_NAME, "wb") as out_f:
                out_f.write(up.getbuffer())
            db.log_action(st.session_state.username, "RESTORE_DB", f"Restored from {up.name}")
            st.success("Restored.")
            st.rerun()

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
