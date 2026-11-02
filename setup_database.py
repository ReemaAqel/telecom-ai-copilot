import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "telecom.db"


def setup_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    try:
        # تفعيل التحقق من العلاقات بين الجداول
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            # جدول الباقات
            connection.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id TEXT PRIMARY KEY,
                    plan_name TEXT NOT NULL,
                    monthly_price_jod REAL NOT NULL
                        CHECK (monthly_price_jod >= 0),
                    data_limit_gb REAL NOT NULL
                        CHECK (data_limit_gb > 0),
                    reduced_speed_mbps REAL NOT NULL
                        CHECK (reduced_speed_mbps > 0)
                )
            """)

            # جدول العملاء التجريبيين
            connection.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            """)

            # استهلاك كل عميل في دورة فوترة محددة
            connection.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    customer_id TEXT NOT NULL,
                    billing_cycle TEXT NOT NULL,
                    used_gb REAL NOT NULL CHECK (used_gb >= 0),
                    PRIMARY KEY (customer_id, billing_cycle),
                    FOREIGN KEY (customer_id)
                        REFERENCES customers(customer_id)
                )
            """)

            # جميع البيانات التالية وهمية للتجربة
            plans = [
                ("START", "Start", 10, 20, 1),
                ("PLUS", "Plus", 15, 50, 2),
                ("MAX", "Max", 25, 100, 5),
            ]

            customers = [
                ("C001", "Demo Customer 1", "START"),
                ("C002", "Demo Customer 2", "PLUS"),
                ("C003", "Demo Customer 3", "MAX"),
            ]

            usage_records = [
                ("C001", "2026-10", 20),
                ("C002", "2026-10", 35),
                ("C003", "2026-10", 10),
            ]

            # إضافة البيانات دون تكرارها عند إعادة تشغيل السكربت
            connection.executemany("""
                INSERT INTO plans (
                    plan_id,
                    plan_name,
                    monthly_price_jod,
                    data_limit_gb,
                    reduced_speed_mbps
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(plan_id) DO NOTHING
            """, plans)

            connection.executemany("""
                INSERT INTO customers (
                    customer_id,
                    customer_name,
                    plan_id
                )
                VALUES (?, ?, ?)
                ON CONFLICT(customer_id) DO NOTHING
            """, customers)

            connection.executemany("""
                INSERT INTO usage (
                    customer_id,
                    billing_cycle,
                    used_gb
                )
                VALUES (?, ?, ?)
                ON CONFLICT(customer_id, billing_cycle) DO NOTHING
            """, usage_records)

        # فحص البيانات باستخدام JOIN
        rows = connection.execute("""
            SELECT
                c.customer_id,
                p.plan_name,
                u.billing_cycle,
                p.data_limit_gb,
                u.used_gb,
                MAX(p.data_limit_gb - u.used_gb, 0) AS remaining_gb
            FROM customers AS c
            JOIN plans AS p
                ON c.plan_id = p.plan_id
            JOIN usage AS u
                ON c.customer_id = u.customer_id
            ORDER BY c.customer_id, u.billing_cycle
        """).fetchall()

        print(f"Database ready: {DB_PATH}")
        print("\nCustomer usage — fictional demo data:")

        for customer_id, plan, cycle, limit, used, remaining in rows:
            print(
                f"{customer_id} | {plan} | {cycle} | "
                f"Limit: {limit:g} GB | Used: {used:g} GB | "
                f"Remaining: {remaining:g} GB"
            )

    finally:
        connection.close()


if __name__ == "__main__":
    setup_database()