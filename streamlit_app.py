import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Telecom AI Copilot",
    page_icon="📡",
    layout="wide",
)


def call_api(method, path, payload=None):
    response = requests.request(
        method=method,
        url=f"{API_URL}{path}",
        json=payload,
        timeout=(5, 120),
    )

    response.raise_for_status()
    return response.json()


def show_request_error(error):
    if isinstance(error, requests.Timeout):
        st.error("The request timed out.")

    elif isinstance(error, requests.ConnectionError):
        st.error(
            "Cannot reach FastAPI. "
            "Make sure the API server is running."
        )

    elif isinstance(error, requests.HTTPError):
        st.error(
            f"The API returned an error: "
            f"{error.response.status_code}"
        )

    else:
        st.error("Could not process the server response.")


def show_sources(sources):
    if sources:
        with st.expander("Retrieved sources"):
            for source in sources:
                st.write(
                    f"[{source['source_id']}] "
                    f"{source['file']} — {source['section']}"
                )


# الاحتفاظ بالبيانات بين إعادة تشغيل سكربت الواجهة.
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_ticket" not in st.session_state:
    st.session_state.pending_ticket = None

if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = None

if "ticket_uncertain" not in st.session_state:
    st.session_state.ticket_uncertain = False


st.title("📡 Telecom AI Copilot")
st.caption(
    "Fictional telecom support demo • Customer C001 • Billing cycle 2026-10"
)

with st.sidebar:
    st.header("Navigation")

    page = st.radio(
        "Choose a page",
        ["Assistant", "My Usage", "Support Ticket"],
    )

    if st.button("Check API connection"):
        try:
            result = call_api("GET", "/health")
            st.success(f"API status: {result['status']}")
        except (requests.RequestException, ValueError) as error:
            show_request_error(error)

    st.info("This demo uses one fixed customer account.")


# -------------------------
# صفحة المحادثة
# -------------------------
if page == "Assistant":
    st.subheader("Ask the assistant")
    st.caption(
        "Ask about plans, policies, or your usage. "
        "Each question is answered independently."
    )

    if st.button("Clear displayed conversation"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            show_sources(message.get("sources", []))

    question = st.chat_input("Type your question...")

    if question:
        question = question.strip()

        if not question:
            st.warning("Please enter a question.")

        elif len(question) > 2000:
            st.warning("The question must not exceed 2000 characters.")

        else:
            st.session_state.messages.append({
                "role": "user",
                "content": question,
            })

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("Preparing your answer..."):
                        result = call_api(
                            "POST",
                            "/chat",
                            {"question": question},
                        )

                    st.markdown(result["answer"])
                    show_sources(result["retrieved_sources"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["retrieved_sources"],
                    })

                except (requests.RequestException, ValueError) as error:
                    show_request_error(error)


# -------------------------
# صفحة الاستهلاك
# -------------------------
elif page == "My Usage":
    st.subheader("My data usage")

    try:
        usage = call_api("GET", "/usage")

        st.write(f"**Plan:** {usage['plan_name']}")
        st.write(f"**Billing cycle:** {usage['billing_cycle']}")

        col1, col2, col3 = st.columns(3)

        col1.metric("Allowance", f"{usage['data_limit_gb']:g} GB")
        col2.metric("Used", f"{usage['used_gb']:g} GB")
        col3.metric("Remaining", f"{usage['remaining_gb']:g} GB")

        st.progress(
            min(max(usage["usage_percentage"] / 100, 0.0), 1.0)
        )

        st.write(f"Usage: {usage['usage_percentage']:g}%")

        if usage["allowance_exhausted"]:
            st.warning(
                "Your data allowance is exhausted. "
                f"The plan's reduced speed is "
                f"{usage['reduced_speed_mbps']:g} Mbps. "
                "This is not a live speed measurement."
            )
        else:
            st.success("You still have data available.")

    except (requests.RequestException, ValueError) as error:
        show_request_error(error)


# -------------------------
# صفحة التذاكر
# -------------------------
elif page == "Support Ticket":
    st.subheader("Create a support ticket")

    if st.session_state.last_ticket:
        ticket = st.session_state.last_ticket

        st.success(
            f"Ticket #{ticket['ticket_id']} was created successfully."
        )
        st.write(f"**Status:** {ticket['status']}")
        st.write(f"**Title:** {ticket['title']}")
        st.write(f"**Description:** {ticket['description']}")
        st.write(f"**Created at (UTC):** {ticket['created_at']}")

    if st.session_state.ticket_uncertain:
        st.warning(
            "The last submission could not be confirmed. "
            "It may have been saved. Check the database before "
            "submitting again to avoid a duplicate ticket."
        )

    elif st.session_state.pending_ticket is None:
        with st.form("ticket_form"):
            title = st.text_input(
                "Issue title",
                max_chars=120,
            )

            description = st.text_area(
                "Issue description",
                max_chars=2000,
            )

            submitted = st.form_submit_button("Review ticket")

        if submitted:
            title = title.strip()
            description = description.strip()

            if not title or not description:
                st.warning("Please fill in both fields.")
            else:
                st.session_state.pending_ticket = {
                    "title": title,
                    "description": description,
                }

                st.session_state.last_ticket = None
                st.rerun()

    else:
        draft = st.session_state.pending_ticket

        st.info("Review this ticket before confirming.")
        st.write("**Customer:** C001")
        st.write(f"**Title:** {draft['title']}")
        st.write(f"**Description:** {draft['description']}")

        col1, col2 = st.columns(2)

        if col1.button("Confirm and create", type="primary"):
            try:
                with st.spinner("Saving your ticket..."):
                    result = call_api(
                        "POST",
                        "/tickets",
                        {
                            **draft,
                            "confirmed": True,
                        },
                    )

                st.session_state.last_ticket = result["ticket"]
                st.session_state.pending_ticket = None
                st.rerun()

            except (requests.RequestException, ValueError) as error:
                show_request_error(error)

                # منع إعادة إرسال غير مقصودة بعد فشل اتصال
                # قد يكون حصل بعد حفظ التذكرة في الخادم.
                st.session_state.ticket_uncertain = True
                st.warning(
                    "Do not resubmit yet. The ticket may have been saved. "
                    "Check the database first."
                )

        if col2.button("Cancel"):
            st.session_state.pending_ticket = None
            st.rerun()