import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from chat import answer_question
from customer_tools import get_usage_summary
from semantic_search import DocumentSearch
from ticket_tools import create_ticket, setup_tickets_table

from google.genai import types, errors
# نفس الحساب والدورة المستخدمين حاليًا داخل chat.py.
# هذه إعدادات تجربة وليست تسجيل دخول حقيقيًا.
CURRENT_CUSTOMER_ID = "C001"
BILLING_CYCLE = "2026-10"


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    question: str = Field(min_length=1, max_length=2000)


class TicketRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    confirmed: StrictBool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # chat.py يحمّل إعدادات .env عند استيراده.
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-flash-latest",
    ).strip()

    if not api_key or not model_name:
        raise RuntimeError(
            "Set GEMINI_API_KEY and GEMINI_MODEL in .env."
        )

    setup_tickets_table()

    # التحميل مرة واحدة عند تشغيل الخادم.
    app.state.search_engine = DocumentSearch()
    app.state.model_name = model_name

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(
                attempts=1,
            ),
        ),
    ) as client:
        app.state.client = client
        yield


app = FastAPI(
    title="Telecom AI Copilot API",
    description="Local demo using fictional customer data.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "demo",
    }


@app.get("/usage")
def usage():
    result = get_usage_summary(
        CURRENT_CUSTOMER_ID,
        BILLING_CYCLE,
    )

    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Usage record not found.",
        )

    return result


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        return answer_question(
            question=request.question,
            search_engine=app.state.search_engine,
            client=app.state.client,
            model_name=app.state.model_name,
        )

    except errors.APIError as error:
        # نعرض الرمز فقط، بدون المفتاح أو محتوى الطلب.
        print(
            f"Gemini API failed: "
            f"code={error.code}, "
            f"type={type(error).__name__}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Gemini API failed with code {error.code}. "
                "Please try again later."
            ),
        ) from error

    except Exception as error:
        print(
            f"Chat failed: {type(error).__name__}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail="Could not generate an answer.",
        ) from error


@app.post("/tickets", status_code=201)
def tickets(request: TicketRequest):
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirmation is required. No ticket was created.",
        )

    result = create_ticket(
        customer_id=CURRENT_CUSTOMER_ID,
        title=request.title,
        description=request.description,
        confirmed=request.confirmed,
    )

    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return result