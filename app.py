import io
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from translations import LANG
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

T = LANG.get(st.session_state.lang, LANG["ar"])
is_rtl = st.session_state.lang in ("ar", "ku")
page_dir = "rtl" if is_rtl else "ltr"
page_align = "right" if is_rtl else "left"

st.markdown(
    f"""
    <style>
        .main, .stSidebar {{
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
    st.title("Legends School & Kindergarten — SMS")
    st.subheader("Private School & Kindergarten • Erbil - Iraq")
    with st.form("login_form"):
        u = st.text_input(T.get("username", "Username"))
        p = st.text_input(T.get("password", "Password"), type="password")
        if st.form_submit_button(T.get("login_btn", "Login")):
            role = db.verify_user(u.strip(), p)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = u.strip()
                st.session_state.role = role
                db.log_action(u.strip(), "LOGIN", "Logged into Legends SMS")
                st.rerun()
            else:
                st.error(T.get("wrong_creds", "Invalid username or password"))
    st.info("Default Logins -> Admin: `admin` / `admin123` | Staff: `user` / `user123`")
    st.stop()

# الشريط العلوي بهوية الصورة المرفقة
top_l, top_m, top_r = st.columns([2.2, 4.2, 2.6])
with top_l:
    st.markdown(f"**{st.session_state.username}** • {T.get('role_admin' if st.session_state.role == 'admin' else 'role_user', st.session_state.role)}")
    if st.button(T.get("logout", "تسجيل الخروج"), key="top_logout"):
        st.session_state.logged_in = False
        st.rerun()

with top_m:
    b1, b2, b3 = st.columns(3)
    if b1.button("English", use_container_width=True):
        st.session_state.lang = "en"
        st.rerun()
    if b2.button("عربي", use_container_width=True):
        st.session_state.lang = "ar"
        st.rerun()
    if b3.button("كردي", use_container_width=True):
        st.session_state.lang = "ku"
        st.rerun()

with top_r:
    st.markdown("### Legends School & Kindergarten\n**Private School & Kindergarten • Erbil - Iraq**")

st.markdown("---")

# القائمة الجانبية الكاملة
menu_map = [
    ("dashboard", "لوحة التحكم"),
    ("students", "الطلاب"),
    ("teachers", "المدرسون"),
    ("parents", "أولياء الأمور"),
    ("stages", "المراحل والصفوف"),
    ("subjects", "المواد الدراسية"),
    ("schedule", "الجدول الدراسي"),
    ("attendance", "الحضور والغياب"),
    ("exams", "الامتحانات والدرجات"),
    ("finance", "الرسوم والدفعات"),
    ("reports", "التقارير"),
    ("certificates", "الشهادات"),
    ("users", "المستخدمون والصلاحيات"),
]

st.sidebar.markdown("### LEGENDS\n**PRIVATE SCHOOL & KINDERGARTEN**")
for key, label in menu_map:
    if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
        st.session_state.active_section = key

st.sidebar.markdown("---")
selected_year = st.sidebar.selectbox(T.get("year", "العام الدراسي"), ["2026-2027", "2025-2026", "2027-2028"], index=0)

st_df = db.get_students(selected_year)
tx_df = db.get_transactions()
if not tx_df.empty:
    tx_df["t_date"] = pd.to_datetime(tx_df["t_date"]).dt.date

sec = st.session_state.active_section

if sec == "dashboard":
    st.subheader("لوحة التحكم")

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
    late_cnt = len(acad_df[acad_df["attendance"].astype(str).str.contains("متأخر|Late", case=False, na=False)]) if not acad_df.empty else 0

    cards = [
        ("#1d4ed8", "إجمالي الطلاب", f"{total_students:,}", "طالب وطالبة"),
        ("#059669", "المدرسون", "1", "مدرس ومدرسة"),
        ("#7c3aed", "المراحل والصفوف", "2", "مرحلة وصف"),
        ("#d97706", "الغياب اليوم", f"{absent_today:,}", "طالب غائب"),
        ("#16a34a", "الإيرادات", f"{income_val:,.0f}", "د.ع"),
        ("#e11d48", "المتبقي", f"{remaining_val:,.0f}", "د.ع"),
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
        st.markdown("**عدد الطلاب حسب المرحلة**")
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=["الروضة", "الأساسي", "الإعدادية"],
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
        st.markdown("**الحضور اليومي**")
        donut_vals = [present_cnt, absent_today, late_cnt] if (present_cnt + absent_today + late_cnt) > 0 else [0, 0, 1]
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=["حاضر", "غائب", "متأخر"],
                    values=donut_vals,
                    hole=0.68,
                    marker_colors=["#10b981", "#ef4444", "#f59e0b"],
                    textinfo="none",
                )
            ]
        )
        fig_donut.add_annotation(text=f"{total_students}<br>إجمالي الطلاب", x=0.5, y=0.5, showarrow=False, font=dict(size=13))
        fig_donut.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10), showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown("**التنبيهات**")
        rem_students = len(st_df[(st_df["tuition_fee"] - st_df["paid_amount"]) > 0]) if not st_df.empty else 0
        st.write(f"• {total_students} طالب فعال في النظام — معلومات التسجيل")
        st.write(f"• {rem_students} سجل رسوم لديه متبقي — يتطلب متابعة")
        st.write(f"• {len(acad_df)} سجل أكاديمي / درجة مدخلة — نتائج الطلاب")
        st.markdown("</div>", unsafe_allow_html=True)

    b_left, b_mid, b_right = st.columns([1.3, 1.1, 1.0])
    with b_left:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown("**آخر النشاط**")
        if not acad_df.empty:
            st.dataframe(acad_df[["rec_date", "student_id", "subject", "score"]].head(5), use_container_width=True, hide_index=True)
        else:
            st.caption("لا توجد نشاطات أكاديمية مسجلة بعد.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b_mid:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown("**الجدول الدراسي اليوم**")
        st.dataframe(
            pd.DataFrame([
                {"الوقت": "08:00 - 08:45", "الصف": "KG-1 / A", "المادة": "القرآن واللغة", "القاعة": "R-101"},
                {"الوقت": "08:50 - 09:35", "الصف": "Grade 5 / A", "المادة": "الرياضيات", "القاعة": "R-204"},
            ]),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with b_right:
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        st.markdown("**اختصارات سريعة**")
        if st.button("+ تسجيل طالب", use_container_width=True):
            st.session_state.active_section = "students"
            st.rerun()
        if st.button("+ تسجيل دفعة / رسوم", use_container_width=True):
            st.session_state.active_section = "finance"
            st.rerun()
        if st.button("📊 التقارير و Excel", use_container_width=True):
            st.session_state.active_section = "reports"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif sec == "students":
    st.subheader("الطلاب والملف الموحد")
    with st.form("add_st_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        full_name = c1.text_input("اسم الطالب")
        parent_name = c2.text_input("ولي الأمر")
        phone = c3.text_input("رقم الهاتف")
        s1, s2, s3, s4 = st.columns(4)
        st_stage = s1.selectbox("المرحلة", ["kg", "primary", "high"])
        st_grade = s2.text_input("الصف", value="KG-1")
        st_sec = s3.text_input("الشعبة", value="A")
        fee = s4.number_input("الرسوم السنوية (د.ع)", min_value=0.0, step=100000.0, value=1500000.0)
        if st.form_submit_button("حفظ الطالب") and full_name.strip():
            db.add_student(selected_year, full_name.strip(), parent_name.strip(), phone.strip(), st_stage, st_grade.strip(), st_sec.strip(), fee, st.session_state.username)
            st.success("تم حفظ الطالب.")
            st.rerun()
    if not st_df.empty:
        st.dataframe(st_df, use_container_width=True)

elif sec == "finance":
    st.subheader("الرسوم والدفعات والميزانية")
    if not st_df.empty:
        opts = {f"#{r['id']} - {r['full_name']}": int(r["id"]) for _, r in st_df.iterrows()}
        sel = st.selectbox("اختر الطالب لتسجيل دفعة", list(opts.keys()))
        with st.form("pay_student_form", clear_on_submit=True):
            amt = st.number_input("مبلغ الدفعة (د.ع)", min_value=0.0, step=50000.0)
            note = st.text_input("ملاحظة الدفعة", value="دفعة رسوم")
            p_date = st.date_input("التاريخ", datetime.today())
            if st.form_submit_button("تسجيل الدفعة وإصدار إيصال") and amt > 0:
                rcpt = db.record_student_payment(opts[sel], amt, p_date, note, st.session_state.username)
                st.success(f"تم إصدار الإيصال رقم #{rcpt}")
                st.rerun()

    st.markdown("---")
    with st.form("tx_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        t_stage = c1.selectbox("المرحلة", ["kg", "primary", "high"])
        t_type = c2.selectbox("النوع", ["income", "expense"])
        t_cat = c3.text_input("البند", value="رسوم / مصروفات")
        t_amt = c4.number_input("المبلغ (د.ع)", min_value=0.0, step=50000.0)
        t_desc = st.text_input("البيان")
        t_date = st.date_input("تاريخ الحركة", datetime.today())
        if st.form_submit_button("ترحيل للخزينة") and t_amt > 0:
            db.add_transaction(selected_year, t_stage, t_type, t_cat, t_amt, t_desc, t_date, st.session_state.username)
            st.success("تم الترحيل.")
            st.rerun()
    if not tx_df.empty:
        st.dataframe(tx_df, use_container_width=True)

elif sec == "reports":
    st.subheader("التقارير وتصدير Excel والنسخ الاحتياطي")
    if not tx_df.empty:
        period = st.selectbox("الفترة", ["daily", "weekly", "monthly", "yearly"])
        ref_d = st.date_input("تاريخ المرجع", datetime.today())
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
            rep.to_excel(writer, index=False, sheet_name="Report")
        st.download_button("تصدير التقرير بصيغة Excel", data=buf.getvalue(), file_name=f"legends_{period}_{ref_d}.xlsx")

    with open(db.DB_NAME, "rb") as fp:
        st.download_button("تحميل نسخة احتياطية (.db)", data=fp.read(), file_name=f"legends_backup_{datetime.today().strftime('%Y%m%d')}.db")
    if st.session_state.role == "admin":
        up = st.file_uploader("استعادة نسخة احتياطية (.db)", type=["db"])
        if up is not None:
            with open(db.DB_NAME, "wb") as out_f:
                out_f.write(up.getbuffer())
            st.success("تمت الاستعادة.")

else:
    st.subheader(f"قسم: {sec}")
    st.info("تم تهيئة القسم ضمن هيكلية النظام. أخبرني إن أردت تفعيل شاشات الإدخال التفصيلية لهذا القسم أو نقل الواجهة بالكامل إلى تطبيق ويب مخصص