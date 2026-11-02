# Telecom AI Copilot

A fictional telecom support assistant combining document retrieval,
a language model, SQL account data, REST APIs, and a web interface.

Built as an educational AI engineering project using synthetic data.
It does not represent any real telecom company.

## Features

- Answer questions about telecom plans and support policies.
- Retrieve relevant document sections using multilingual embeddings.
- Include source references in generated answers.
- Read the current demo account's usage from SQLite.
- Display allowance, consumption, and remaining data.
- Review and confirm support tickets before saving them.
- Access the application through FastAPI and Streamlit.
- Evaluate API behavior and selected answer scenarios.

## Technology Stack

- Python
- SQLite
- Sentence Transformers
- NumPy
- Google Gemini API
- FastAPI and Uvicorn
- Streamlit
- Requests
- Pydantic
- python-dotenv

## How It Works

1. Markdown documents are split into sections.
2. Each section is converted into an embedding.
3. A question is compared with the document embeddings.
4. Relevant sections and the current demo account's usage are
   supplied to Gemini.
5. Gemini generates an answer with source references.
6. Streamlit communicates with the backend through HTTP requests.

Support tickets use a separate workflow: enter details,
review the summary, confirm, and save to SQLite.

## Project Files

| File | Purpose |
|---|---|
| inspect_data.py | Inspect document contents and basic statistics |
| setup_database.py | Create and seed the demo database |
| customer_tools.py | Query account usage and calculate remaining data |
| prepare_documents.py | Split Markdown documents into chunks |
| semantic_search.py | Encode chunks and retrieve relevant sections |
| rag_assistant.py | Prepare document context and RAG instructions |
| chat.py | Combine retrieval, account context, and Gemini generation |
| ticket_tools.py | Validate and save confirmed support tickets |
| main.py | Expose the backend through FastAPI |
| streamlit_app.py | Provide the web interface |
| evaluate_api.py | Run API checks and collect answer evaluation results |
| test_gemini.py | Test a minimal Gemini request |
| list_models.py | List available generation models |

## Demo Data

The application uses customer C001 and the fixed billing cycle 2026-10.

- Plan: Start
- Monthly allowance: 20 GB
- Used: 20 GB
- Remaining: 0 GB
- Reduced speed policy: 1 Mbps after allowance exhaustion

The reduced speed is a plan policy, not a live speed measurement.

## Configuration

Create a local .env file:

    GEMINI_API_KEY=your_api_key
    GEMINI_MODEL=gemini-3.5-flash-lite

Keep the API key private and exclude .env from version control.

## Run Locally

Run these commands from the project folder in the telecom_ai environment.

Prepare the data:

    python setup_database.py
    python prepare_documents.py

Start the API:

    python -m uvicorn main:app

In a separate terminal, start the interface:

    python -m streamlit run streamlit_app.py

API documentation: http://127.0.0.1:8000/docs

## Evaluation

Run while the API is running:

    python evaluate_api.py

Results are saved to data/evaluation_results.json.

Observed results from one local evaluation run:

- Automated API checks: 4/4 passed.
- Manually reviewed answer scenarios: 7/8 passed.
- Chat response times: 0.63–1.20 seconds.

These results describe a small local test set, not general accuracy
or guaranteed performance.

## Known Limitations

- The application uses one fixed demo account without authentication.
- A tested cross-customer request failed: the assistant presented
  C001's data as if it belonged to C002 instead of refusing.
- Prompt instructions do not reliably enforce account boundaries.
- The chat sends each question independently without conversation history.
- Document embeddings are recomputed at backend startup.
- Retrieval returns the top sections even when they are not relevant.
- Ticket creation does not implement idempotency.
- Gemini availability and response times depend on the external service.

This is a local educational prototype and is not suitable for use
with real customer data in its current form.

## Installation

Use Python 3.11.

Create and activate an environment:

    conda create -n telecom_ai python=3.11 -y
    conda activate telecom_ai

Install dependencies:

    python -m pip install -r requirements.txt

Copy the example configuration on Windows:

    copy .env.example .env

Open .env and replace the placeholder with your own Gemini API key.

The first embedding model load requires an internet connection
to download the model files.