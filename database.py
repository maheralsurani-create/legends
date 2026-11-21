import sqlite3
import pandas as pd
import hashlib

DB_NAME = "school_finance.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT
                )''')
    
    # إضافة حساب أدمن وحساب مستخدم افتراضي إذا لم يكونا موجودين
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_pass("admin123"), "admin"))
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("user", hash_pass("user123"), "user"))
    
    # جدول الحركات المالية
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT,
                    t_type TEXT,
                    amount REAL,
                    description TEXT,
                    t_date DATE,
                    created_by TEXT
                )''')
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_pass(password)))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def add_transaction(stage, t_type, amount, description, t_date, created_by):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (stage, t_type, amount, description, t_date, created_by) VALUES (?, ?, ?, ?, ?, ?)",
              (stage, t_type, amount, description, str(t_date), created_by))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY t_date DESC, id DESC", conn)
    conn.close()
    return df

def delete_transaction(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id=?", (record_id,))
    conn.commit()
    conn.close()