import json
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "telecom.db"


def get_usage_summary(customer_id: str, billing_cycle: str) -> dict:
    # تجنب إنشاء قاعدة فارغة إذا كان المسار خطأ
    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "Database not found. Run setup_database.py first."
        )

    connection = sqlite3.connect(DB_PATH)

    # السماح بقراءة الأعمدة بأسمائها بدل أرقام مواقعها
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute("""
            SELECT
                c.customer_id,
                c.customer_name,
                p.plan_id,
                p.plan_name,
                p.data_limit_gb,
                p.reduced_speed_mbps,
                u.billing_cycle,
                u.used_gb
            FROM customers AS c
            JOIN plans AS p
                ON c.plan_id = p.plan_id
            JOIN usage AS u
                ON c.customer_id = u.customer_id
            WHERE c.customer_id = ?
                AND u.billing_cycle = ?
        """, (customer_id, billing_cycle)).fetchone()

        if row is None:
            return {
                "status": "not_found",
                "message": "No usage record found for this customer and cycle.",
            }

        remaining_gb = max(row["data_limit_gb"] - row["used_gb"], 0)

        usage_percentage = (
            row["used_gb"] / row["data_limit_gb"]
        ) * 100

        allowance_exhausted = row["used_gb"] >= row["data_limit_gb"]

        return {
            "status": "success",
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "plan_id": row["plan_id"],
            "plan_name": row["plan_name"],
            "billing_cycle": row["billing_cycle"],
            "data_limit_gb": row["data_limit_gb"],
            "used_gb": row["used_gb"],
            "remaining_gb": round(remaining_gb, 2),
            "usage_percentage": round(usage_percentage, 2),
            "allowance_exhausted": allowance_exhausted,
            "reduced_speed_mbps": row["reduced_speed_mbps"],
        }

    finally:
        connection.close()


if __name__ == "__main__":
    # أمثلة محلية للاختبار، وليست نظام تسجيل دخول
    for demo_customer_id in ["C001", "C002", "C003", "C999"]:
        result = get_usage_summary(demo_customer_id, "2026-10")

        print(json.dumps(result, indent=2))
        print()