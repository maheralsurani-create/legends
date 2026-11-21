import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from translations import LANG
import database as db

# تهيئة قاعدة البيانات
db.init_db()

st.set_page_config(page_title="School Accounting", layout="wide")

# اختيار اللغة في الشريط الجانبي
lang_choice = st.sidebar.selectbox("🌐 Language / اللغة / زمان", ["ar", "ku", "en"], 
                                   format_func=lambda x: {"ar": "العربية", "ku": "کوردی", "en": "English"}[x])
T = LANG[lang_choice]

# ضبط اتجاه الصفحة (يمين لليسار أو يسار لليمين)
st.markdown(f"""
    <style>
        .main, .stSidebar {{ direction: {T['dir']}; text-align: {'right' if T['dir']=='rtl' else 'left'}; }}
    </style>
""", unsafe_allow_html=True)

# إدارة جلسة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.title(f"🏫 {T['title']}")
    st.subheader(T["login"])
    with st.form("login_form"):
        user_in = st.text_input(T["username"])
        pass_in = st.text_input(T["password"], type="password")
        submit = st.form_submit_button(T["login_btn"])
        
        if submit:
            role = db.verify_user(user_in, pass_in)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = user_in
                st.session_state.role = role
                st.rerun()
            else:
                st.error(T["wrong_creds"])
    st.info("Default Logins -> Admin: `admin` / `admin123` | User: `user` / `user123`")
    st.stop()

# --- بعد تسجيل الدخول ---
st.sidebar.markdown("---")
role_label = T["role_admin"] if st.session_state.role == "admin" else T["role_user"]
st.sidebar.write(f"**{T['welcome']} {st.session_state.username}**")
st.sidebar.caption(role_label)

if st.sidebar.button("🚪 Logout / خروج"):
    st.session_state.logged_in = False
    st.rerun()

# القائمة الرئيسية
menu = st.sidebar.radio("Menu", [T["menu_dashboard"], T["menu_transactions"], T["menu_reports"], T["menu_backup"]])

# جلب البيانات
df = db.get_transactions()
if not df.empty:
    df['t_date'] = pd.to_datetime(df['t_date']).dt.date

# 1. لوحة التحكم والميزانية
if menu == T["menu_dashboard"]:
    st.title(f"📊 {T['menu_dashboard']}")
    
    stage_filter = st.selectbox(T["stage"], ["all", "kg", "primary", "high"],
                                format_func=lambda x: {"all": T["all_stages"], "kg": T["kg"], "primary": T["primary"], "high": T["high"]}[x])
    
    filtered_df = df if stage_filter == "all" else df[df["stage"] == stage_filter] if not df.empty else df
    
    inc = filtered_df[filtered_df["t_type"] == "income"]["amount"].sum() if not filtered_df.empty else 0.0
    exp = filtered_df[filtered_df["t_type"] == "expense"]["amount"].sum() if not filtered_df.empty else 0.0
    net = inc - exp
    
    col1, col2, col3 = st.columns(3)
    col1.metric(T["total_income"], f"{inc:,.2f}")
    col2.metric(T["total_expense"], f"{exp:,.2f}")
    col3.metric(T["net_balance"], f"{net:,.2f}")
    
    st.markdown("---")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
        # صلاحية الحذف للأدمن فقط
        if st.session_state.role == "admin":
            st.subheader(f"🗑️ {T['delete_record']}")
            del_id = st.number_input("ID", min_value=1, step=1)
            if st.button("Delete"):
                db.delete_transaction(del_id)
                st.rerun()

# 2. تسجيل حركة مالية
elif menu == T["menu_transactions"]:
    st.title(f"💳 {T['menu_transactions']}")
    with st.form("tx_form", clear_on_submit=True):
        stage = st.selectbox(T["stage"], ["kg", "primary", "high"],
                             format_func=lambda x: {"kg": T["kg"], "primary": T["primary"], "high": T["high"]}[x])
        t_type = st.radio(T["type"], ["income", "expense"],
                          format_func=lambda x: {"income": T["income"], "expense": T["expense"]}[x], horizontal=True)
        amount = st.number_input(T["amount"], min_value=0.0, step=1000.0)
        desc = st.text_input(T["desc"])
        t_date = st.date_input(T["date"], datetime.today())
        
        if st.form_submit_button(T["save_btn"]):
            if amount > 0:
                db.add_transaction(stage, t_type, amount, desc, t_date, st.session_state.username)
                st.success(T["saved_msg"])

# 3. التقارير وتصدير Excel
elif menu == T["menu_reports"]:
    st.title(f"📑 {T['menu_reports']}")
    if df.empty:
        st.warning("No data available.")
    else:
        col1, col2 = st.columns(2)
        period = col1.selectbox(T["report_period"], ["daily", "weekly", "monthly", "yearly"],
                                format_func=lambda x: T[x])
        ref_date = col2.date_input(T["date"], datetime.today())
        
        if period == "daily":
            rep_df = df[df['t_date'] == ref_date]
        elif period == "weekly":
            start_week = ref_date - timedelta(days=ref_date.weekday())
            end_week = start_week + timedelta(days=6)
            rep_df = df[(df['t_date'] >= start_week) & (df['t_date'] <= end_week)]
        elif period == "monthly":
            rep_df = df[(pd.to_datetime(df['t_date']).dt.month == ref_date.month) & 
                        (pd.to_datetime(df['t_date']).dt.year == ref_date.year)]
        elif period == "yearly":
            rep_df = df[pd.to_datetime(df['t_date']).dt.year == ref_date.year]
            
        st.dataframe(rep_df, use_container_width=True)
        
        # تحويل البيانات إلى ملف Excel في الذاكرة للتحميل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            rep_df.to_excel(writer, index=False, sheet_name='Report')
            
        st.download_button(
            label=f"📥 {T['export_excel']}",
            data=buffer.getvalue(),
            file_name=f"School_Report_{period}_{ref_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 4. النسخ الاحتياطي والاستعادة
elif menu == T["menu_backup"]:
    st.title(f"💾 {T['menu_backup']}")
    
    # تحميل نسخة احتياطية
    with open(db.DB_NAME, "rb") as fp:
        st.download_button(
            label=f"⬇️ {T['download_db']}",
            data=fp,
            file_name=f"school_backup_{datetime.today().strftime('%Y%m%d')}.db",
            mime="application/octet-stream"
        )
        
    st.markdown("---")
    # استعادة نسخة احتياطية (متاحة للأدمن)
    if st.session_state.role == "admin":
        st.warning(T["restore_warn"])
        uploaded_file = st.file_uploader(T["restore_db"], type=["db"])
        if uploaded_file is not None:
            with open(db.DB_NAME, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(T["restore_success"])