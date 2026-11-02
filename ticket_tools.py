import json
import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "telecom.db"


def get_connection():
    """فتح القاعدة الموجودة وتفعيل العلاقات."""

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "Database not found. Run setup_database.py first."
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def setup_tickets_table():
    """إضافة جدول التذاكر بدون حذف البيانات الموجودة."""

    with closing(get_connection()) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,

                    customer_id TEXT NOT NULL,

                    title TEXT NOT NULL
                        CHECK (
                            length(trim(title)) BETWEEN 1 AND 120
                        ),

                    description TEXT NOT NULL
                        CHECK (
                            length(trim(description)) BETWEEN 1 AND 2000
                        ),

                    status TEXT NOT NULL DEFAULT 'Open'
                        CHECK (
                            status IN ('Open', 'In Progress', 'Closed')
                        ),

                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (customer_id)
                        REFERENCES customers(customer_id)
                )
            """)


def create_ticket(
    customer_id: str,
    title: str,
    description: str,
    *,
    confirmed: bool = False,
) -> dict:
    """حفظ تذكرة بعد تأكيد التطبيق أن المستخدم وافق."""

    if confirmed is not True:
        return {
            "status": "confirmation_required",
            "message": "The ticket was not created. Confirmation is required.",
        }

    title = title.strip()
    description = description.strip()

    if not 1 <= len(title) <= 120:
        raise ValueError(
            "The title must contain 1 to 120 characters."
        )

    if not 1 <= len(description) <= 2000:
        raise ValueError(
            "The description must contain 1 to 2000 characters."
        )

    with closing(get_connection()) as connection:
        with connection:
            customer = connection.execute(
                """
                SELECT customer_id
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

            if customer is None:
                return {
                    "status": "not_found",
                    "message": "Customer not found. No ticket was created.",
                }

            cursor = connection.execute(
                """
                INSERT INTO tickets (
                    customer_id,
                    title,
                    description
                )
                VALUES (?, ?, ?)
                """,
                (customer_id, title, description),
            )

            ticket_id = cursor.lastrowid

        # وصلنا هنا بعد نجاح حفظ المعاملة.
        saved_ticket = connection.execute(
            """
            SELECT
                ticket_id,
                customer_id,
                title,
                description,
                status,
                created_at
            FROM tickets
            WHERE ticket_id = ?
                AND customer_id = ?
            """,
            (ticket_id, customer_id),
        ).fetchone()

        if saved_ticket is None:
            raise RuntimeError(
                "Could not retrieve the saved ticket."
            )

        return {
            "status": "success",
            "ticket": dict(saved_ticket),
        }


def main():
    setup_tickets_table()

    # حساب ثابت للتجربة، وليس نظام تسجيل دخول.
    current_customer_id = "C001"

    print("\nCreate a support ticket")
    print(f"Demo customer: {current_customer_id}")

    title = input("\nIssue title: ").strip()
    description = input("Issue description: ").strip()

    # نفحص البيانات قبل طلب التأكيد.
    if not 1 <= len(title) <= 120:
        print("Title must contain 1 to 120 characters.")
        return

    if not 1 <= len(description) <= 2000:
        print("Description must contain 1 to 2000 characters.")
        return

    print("\nTicket summary:")
    print(f"Customer: {current_customer_id}")
    print(f"Title: {title}")
    print(f"Description: {description}")

    confirmation = input(
        "\nType yes to create this ticket: "
    ).strip().lower()

    if confirmation != "yes":
        print("Cancelled. No ticket was created.")
        return

    result = create_ticket(
        customer_id=current_customer_id,
        title=title,
        description=description,
        confirmed=True,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()