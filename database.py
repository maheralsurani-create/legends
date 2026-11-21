import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

DB_NAME = "school_finance.db"


def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT
                )""")

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_pass("admin123"), "admin"))
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("user", hash_pass("user123"), "user"))

    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    academic_year TEXT,
                    full_name TEXT,
                    parent_name TEXT,
                    phone TEXT,
                    stage TEXT,
                    grade TEXT,
                    section TEXT,
                    tuition_fee REAL,
                    paid_amount REAL DEFAULT 0.0
                )""")

    c.execute("PRAGMA table_info(students)")
    st_cols = [row[1] for row in c.fetchall()]
    if "paid_amount" not in st_cols:
        c.execute("ALTER TABLE students ADD COLUMN paid_amount REAL DEFAULT 0.0")

    c.execute("""CREATE TABLE IF NOT EXISTS student_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    amount REAL,
                    pay_date DATE,
                    note TEXT,
                    created_by TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS academic_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    academic_year TEXT,
                    rec_date DATE,
                    attendance TEXT,
                    subject TEXT,
                    score TEXT,
                    created_by TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    academic_year TEXT,
                    stage TEXT,
                    t_type TEXT,
                    category TEXT,
                    amount REAL,
                    description TEXT,
                    t_date DATE,
                    student_id INTEGER,
                    created_by TEXT
                )""")

    c.execute("PRAGMA table_info(transactions)")
    tx_cols = [row[1] for row in c.fetchall()]
    for col_name, col_def in [
        ("academic_year", "TEXT"),
        ("stage", "TEXT"),
        ("t_type", "TEXT"),
        ("category", "TEXT"),
        ("amount", "REAL"),
        ("description", "TEXT"),
        ("t_date", "DATE"),
        ("student_id", "INTEGER"),
        ("created_by", "TEXT"),
    ]:
        if col_name not in tx_cols:
            c.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")

    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    username TEXT,
                    action TEXT,
                    details TEXT
                )""")

    conn.commit()
    conn.close()


def log_action(username: str, action: str, details: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO audit_log (timestamp, username, action, details) VALUES (?, ?, ?, ?)",
              (ts, username, action, details))
    conn.commit()
    conn.close()


def verify_user(username: str, password: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_pass(password)))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def add_student(academic_year, full_name, parent_name, phone, stage, grade, section, tuition_fee, username):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("""INSERT INTO students
                 (academic_year, full_name, parent_name, phone, stage, grade, section, tuition_fee, paid_amount)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0)""",
              (academic_year, full_name, parent_name, phone, stage, grade, section, float(tuition_fee)))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    log_action(username, "ADD_STUDENT", f"Student #{sid} ({full_name}) - {stage}/{grade}/{section} - Fee: {tuition_fee:,.0f} IQD")


def update_student(student_id: int, full_name: str, parent_name: str, phone: str,
                   stage: str, grade: str, section: str, tuition_fee: float, username: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("""UPDATE students
                 SET full_name=?, parent_name=?, phone=?, stage=?, grade=?, section=?, tuition_fee=?
                 WHERE id=?""",
              (full_name.strip(), parent_name.strip(), phone.strip(),
               stage, grade.strip(), section.strip(), float(tuition_fee), int(student_id)))
    conn.commit()
    conn.close()
    log_action(username, "UPDATE_STUDENT", f"Updated student #{student_id} ({full_name.strip()}) - Fee: {float(tuition_fee):,.0f} IQD")


def delete_student(student_id: int, username: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (int(student_id),))
    row = c.fetchone()
    st_name = row[0] if row else f"ID {student_id}"
    c.execute("DELETE FROM student_payments WHERE student_id=?", (int(student_id),))
    c.execute("DELETE FROM academic_records WHERE student_id=?", (int(student_id),))
    c.execute("DELETE FROM students WHERE id=?", (int(student_id),))
    conn.commit()
    conn.close()
    log_action(username, "DELETE_STUDENT", f"Deleted student #{student_id} ({st_name}) and related records")


def get_students(academic_year=None):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    if academic_year and academic_year != "ALL":
        df = pd.read_sql_query("SELECT * FROM students WHERE academic_year=? ORDER BY id DESC", conn, params=(academic_year,))
    else:
        df = pd.read_sql_query("SELECT * FROM students ORDER BY id DESC", conn)
    conn.close()
    if not df.empty and "paid_amount" not in df.columns:
        df["paid_amount"] = 0.0
    return df
def record_student_payment(student_id: int, amount: float, pay_date, note: str, username: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute(
        "SELECT full_name, stage, academic_year, COALESCE(paid_amount, 0.0) FROM students WHERE id=?",
        (int(student_id),),
    )
    st = c.fetchone()
    if not st:
        conn.close()
        return None

    full_name, stage, yr, cur_paid = st
    amt = float(amount)
    new_paid = float(cur_paid) + amt

    c.execute("UPDATE students SET paid_amount=? WHERE id=?", (new_paid, int(student_id)))
    c.execute(
        "INSERT INTO student_payments (student_id, amount, pay_date, note, created_by) VALUES (?, ?, ?, ?, ?)",
        (int(student_id), amt, str(pay_date), note, username),
    )
    receipt_id = c.lastrowid
    c.execute(
        """INSERT INTO transactions
           (academic_year, stage, t_type, category, amount, description, t_date, student_id, created_by)
           VALUES (?, ?, 'income', 'Tuition / رسوم دراسية', ?, ?, ?, ?, ?)""",
        (yr, stage, amt, f"Receipt #{receipt_id} - {full_name} ({note})", str(pay_date), int(student_id), username),
    )
    conn.commit()
    conn.close()
    log_action(username, "PAYMENT_RECEIPT", f"Receipt #{receipt_id} for {full_name} (#{student_id}): {amt:,.0f} IQD")
    return receipt_id


def get_student_payments(student_id: int):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("SELECT * FROM student_payments WHERE student_id=? ORDER BY id DESC", conn, params=(int(student_id),))
    conn.close()
    return df


def get_all_payments():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("""SELECT p.id AS receipt_id, p.student_id, s.full_name AS student_name,
                                     s.stage, s.grade, s.section, p.amount, p.pay_date, p.note, p.created_by
                              FROM student_payments p
                              LEFT JOIN students s ON p.student_id = s.id
                              ORDER BY p.id DESC""", conn)
    conn.close()
    return df


def add_academic_record(student_id: int, academic_year: str, rec_date, attendance: str, subject: str, score: str, username: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("""INSERT INTO academic_records
                 (student_id, academic_year, rec_date, attendance, subject, score, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (int(student_id), academic_year, str(rec_date), attendance, subject, score, username))
    conn.commit()
    conn.close()
    log_action(username, "ACADEMIC_RECORD", f"Student #{student_id} ({academic_year}): {attendance}, {subject}={score}")


def get_student_academic(student_id: int):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("SELECT * FROM academic_records WHERE student_id=? ORDER BY rec_date DESC, id DESC", conn, params=(int(student_id),))
    conn.close()
    return df


def add_transaction(academic_year, stage, t_type, category, amount, description, t_date, username):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("""INSERT INTO transactions
                 (academic_year, stage, t_type, category, amount, description, t_date, student_id, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)""",
              (academic_year, stage, t_type, category, float(amount), description, str(t_date), username))
    tx_id = c.lastrowid
    conn.commit()
    conn.close()
    log_action(username, "TREASURY_TX", f"TX #{tx_id} [{t_type}] {category}: {float(amount):,.0f} IQD - {description}")


def get_transactions():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY t_date DESC, id DESC", conn)
    conn.close()
    return df


def delete_transaction(record_id: int, username: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id=?", (int(record_id),))
    conn.commit()
    conn.close()
    log_action(username, "DELETE_TX", f"Deleted transaction #{record_id}")


def get_audit_log():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200", conn)
    conn.close()
    return df


def create_user(new_username: str, new_password: str, role: str, admin_user: str):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
        (new_username.strip(), hash_pass(new_password), role),
    )
    conn.commit()
    conn.close()
    log_action(admin_user, "MANAGE_USER", f"Saved user '{new_username.strip()}' with role '{role}'")


def get_users():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    df = pd.read_sql_query("SELECT username, role FROM users ORDER BY username ASC", conn)
    conn.close()
    return df
