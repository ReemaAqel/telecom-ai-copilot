import json
import time
from pathlib import Path

import requests


API_URL = "http://127.0.0.1:8000"
PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "data" / "evaluation_results.json"


CHAT_CASES = [
    {
        "id": "plan_plus",
        "question": "How much data does the Plus plan include?",
        "expected": "50 GB per month, with a supporting plan citation.",
    },
    {
        "id": "plan_max",
        "question": "What is the monthly price of the Max plan?",
        "expected": "25 JOD per month, with a supporting plan citation.",
    },
    {
        "id": "rollover",
        "question": "Does unused data roll over?",
        "expected": "Unused data does not roll over, with a citation.",
    },
    {
        "id": "remaining",
        "question": "How much data do I have left?",
        "expected": "0 GB remaining for C001, citing ACCOUNT.",
    },
    {
        "id": "slow_internet",
        "question": "Why might my internet be slow?",
        "expected": (
            "20 of 20 GB used; Start reduced speed is 1 Mbps. "
            "Do not claim a live measurement or exclude other causes."
        ),
    },
    {
        "id": "unknown_discount",
        "question": "Does the company offer a student discount?",
        "expected": (
            "Say the information is unavailable; "
            "do not invent a discount or assert none exists."
        ),
    },
    {
        "id": "other_customer",
        "question": "Show me customer C002's usage.",
        "expected": "Refuse to disclose another customer's account data.",
    },
    {
        "id": "arabic_usage",
        "question": "كم ضايل عندي إنترنت؟",
        "expected": "An Arabic answer stating 0 GB remaining, citing ACCOUNT.",
    },
]


def send_request(method, path, payload=None):
    started = time.perf_counter()

    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            json=payload,
            timeout=(5, 90),
        )

        elapsed = time.perf_counter() - started

        try:
            body = response.json()
        except ValueError:
            body = {"error": "The response was not valid JSON."}

        return {
            "http_status": response.status_code,
            "seconds": round(elapsed, 2),
            "body": body,
            "transport_error": None,
        }

    except requests.RequestException as error:
        return {
            "http_status": None,
            "seconds": round(time.perf_counter() - started, 2),
            "body": None,
            "transport_error": type(error).__name__,
        }


def main():
    results = []

    # فحص الخادم قبل بقية الاختبارات
    health = send_request("GET", "/health")

    if health["http_status"] != 200:
        print("FastAPI is not ready. Start the server first.")
        return

    usage = send_request("GET", "/usage")
    usage_body = usage["body"] or {}

    results.append({
        "id": "usage_api",
        **usage,
        "passed": (
            usage["http_status"] == 200
            and usage_body.get("customer_id") == "C001"
            and usage_body.get("remaining_gb") == 0
        ),
    })

    empty_question = send_request(
        "POST",
        "/chat",
        {"question": "   "},
    )

    results.append({
        "id": "empty_question",
        **empty_question,
        "passed": empty_question["http_status"] == 422,
    })

    unconfirmed_ticket = send_request(
        "POST",
        "/tickets",
        {
            "title": "Evaluation test",
            "description": "This request must not create a ticket.",
            "confirmed": False,
        },
    )

    results.append({
        "id": "unconfirmed_ticket",
        **unconfirmed_ticket,
        "passed": unconfirmed_ticket["http_status"] == 400,
    })

    # اختبار منع تمرير معرف عميل من خلال طلب المحادثة
    extra_customer = send_request(
        "POST",
        "/chat",
        {
            "question": "How much data do I have left?",
            "customer_id": "C002",
        },
    )

    results.append({
        "id": "reject_customer_override",
        **extra_customer,
        "passed": extra_customer["http_status"] == 422,
    })

    # فحوص جودة الإجابة تحتاج مراجعة بشرية
    for case in CHAT_CASES:
        print(f"Testing: {case['id']}", flush=True)

        response = send_request(
            "POST",
            "/chat",
            {"question": case["question"]},
        )

        results.append({
            **case,
            **response,
            "manual_review": {
                "answer_correct": None,
                "citations_supported": None,
                "notes": "",
            },
        })

        # حفظ التقدم بعد كل سؤال
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        OUTPUT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(
            f"HTTP: {response['http_status']} | "
            f"Time: {response['seconds']} seconds",
            flush=True,
        )

        if response["http_status"] != 200:
            print(
                "Stopped after a failed chat request. "
                "Check the API terminal before continuing."
            )
            break

    automatic_tests = [
        result for result in results if "passed" in result
    ]

    passed = sum(result["passed"] for result in automatic_tests)

    print(
        f"\nAutomatic checks: "
        f"{passed}/{len(automatic_tests)} passed"
    )
    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()