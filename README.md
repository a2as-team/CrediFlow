# CrediFlow

CrediFlow is an intelligent conversational banking assistant powered by **Google Gemini**, **LangChain**, and **Streamlit**.
It enables users to perform banking operations such as transactions, bill payments, EMI management, card services, delivery tracking, and knowledge-based queries using a **Retrieval-Augmented Generation (RAG)** system.

---

## Features

### Core Capabilities

* Secure signup and login using hashed credentials.
* Conversational banking assistant built with `gemini-2.5-flash` and Google ADK.
* RAG-based knowledge querying with FAISS and Google Generative AI embeddings.
* Process transactions, issue refunds, and update billing.
* Create EMIs, track schedules, and pay EMI installments.
* Block or request credit cards.
* Track card delivery status.
* Retrieve customer profiles, bank statements, dues, and bill details.
* Persistent sessions using Google ADK’s `InMemorySessionService`.

### Frontend Interface

* Built using Streamlit with a custom dark theme.
* Chat-style UI for seamless interaction.
* Optional voice-enabled interface using `streamlit-mic-recorder`.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### 4. Prepare databases

Ensure the following SQLite database files exist and follow the expected schema:

* `customers.db`
* `transactions.db`
* `delivery.db`
* `emi.db`

---

## Running the Application

### Standard UI

```bash
streamlit run app.py
```

### Voice-enabled UI

```bash
streamlit run app_with_voice.py
```

### Command-line Agent (optional)

```bash
python agent.py
```

---

## RAG Module

The RAG pipeline uses:

* **FAISS vector store** for semantic search
* **Google Generative AI embeddings** (`models/embedding-001`)
* **Gemini 2.5 Flash** for context-aware answer generation

Before use, ingest your knowledge base into:

```
faiss_store/
```

---

## Session Handling

CrediFlow manages individual user conversations using:

* Google ADK `Runner`
* `InMemorySessionService`
* Customer ID as the session key

Every message includes a context header containing the active customer ID to ensure correct tool routing and database operations.

---

## Database Structure

CrediFlow uses four SQLite databases:

### 1. `customers.db`

Stores:

* Customer profiles
* Account details
* Card metadata

### 2. `transactions.db`

Stores:

* Transaction logs
* Refunds
* Billing history

### 3. `delivery.db`

Stores:

* Card shipping and delivery information

### 4. `emi.db`

Stores:

* EMI creation data
* Schedules and due dates
* Payment logs

---

## Agent Tools

The agent uses tools defined in `tools.py`, each mapped to a real banking operation.

| Tool Name             | Purpose                               |
| --------------------- | ------------------------------------- |
| `fetch_details`       | Retrieve customer profile information |
| `transaction_details` | Fetch transaction logs                |
| `bank_statement`      | Generate bank statements              |
| `bill_details`        | Retrieve billing dues                 |
| `process_transaction` | Perform bank transfers                |
| `pay_bill`            | Process bill payments                 |
| `emi_creation`        | Create new EMIs                       |
| `emi_details`         | View EMI schedules                    |
| `emi_pay`             | Pay EMI installments                  |
| `block_account`       | Block cards/accounts                  |
| `delivery_status`     | Check card delivery status            |
| `request_card`        | Request new cards                     |
| `create_alert`        | Create reminders                      |
| `collection_alert`    | Notify about overdue payments         |
| `RAG_query`           | Perform knowledge-based RAG search    |

Each tool interacts with the relevant database and returns structured JSON.

---

## Architecture

![CrediFlow Architecture](./Architecture-diagram.png)

---

## Notes

* Requires a valid Google Gemini API key.
* Install `streamlit-mic-recorder` for voice-enabled features.
* Sessions persist until the user signs out.

---

## License

This project is licensed under the **MIT License**.

