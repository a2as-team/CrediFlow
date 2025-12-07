import sqlite3
import bcrypt
import json
from datetime import datetime, timedelta
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


def make_con():
    conn_cust = sqlite3.connect('customers.db')
    cursor_cust = conn_cust.cursor()

    conn_trans = sqlite3.connect('transactions.db')
    cursor_trans = conn_trans.cursor()

    conn_del = sqlite3.connect('delivery.db')
    cursor_del = conn_del.cursor()

    conn_emi = sqlite3.connect('emi.db')
    cursor_emi = conn_emi.cursor()
    return cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def login(cust_id, password):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT password_hash FROM customer_logins WHERE customer_id=?", (cust_id,))
    row = cursor_cust.fetchone()
    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return True
    return False


def signup(name, phone, email, password):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT email FROM customer_logins WHERE email=?", (email,))
    if cursor_cust.fetchone():
        return True

    cursor_cust.execute(
        "SELECT customer_id FROM customers ORDER BY customer_id DESC LIMIT 1")
    last = cursor_cust.fetchone()
    next_id = f"CUST{(int(last[0][4:]) + 1 if last else 1):03d}"
    pw_hash = hash_password(password)

    try:
        cursor_cust.execute("INSERT INTO customer_logins VALUES (?, ?, ?, ?)",
                            (next_id, phone, email, pw_hash))

        cursor_cust.execute("INSERT INTO customers VALUES (?, ?, ?, 50000, 50000, 'active')",
                            (next_id, name, f"CARD{next_id[-3:]}"))

        conn_cust.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn_cust.rollback()
        return False


def fetch_details(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT * FROM customers WHERE customer_id=?", (cust_id,))
    cust = cursor_cust.fetchone()

    cursor_trans.execute(
        "SELECT * FROM billing_dues WHERE customer_id=?", (cust_id,))
    bills = cursor_trans.fetchall()

    cursor_emi.execute(
        "SELECT * FROM loan_master WHERE customer_id=?", (cust_id,))
    loans = cursor_emi.fetchall()

    return json.dumps({"customer": cust, "bills": bills, "loans": loans})


def block_account(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_trans.execute(
        "SELECT current_due FROM billing_dues WHERE customer_id=?", (cust_id,))
    dues = cursor_trans.fetchall()
    total_due = sum(d[0] for d in dues)

    if total_due > 0:
        return json.dumps({
            "status": "payment_required",
            "customer_id": cust_id,
            "total_due": total_due,
            "message": "Outstanding dues detected. Please pay before account can be blocked."
        })

    cursor_cust.execute(
        "UPDATE customers SET card_status='blocked' WHERE customer_id=?", (cust_id,))
    conn_cust.commit()
    return json.dumps({"status": "blocked", "customer_id": cust_id})


def request_card(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT card_id FROM customers WHERE customer_id=?", (cust_id,))
    card_id = cursor_cust.fetchone()[0]

    cursor_del.execute(
        "INSERT INTO card_delivery VALUES (?, ?, ?, ?, ?)",
        (card_id, "CourierX",
         f"TRK{datetime.now().strftime('%f')}",
         "Shipped",
         (datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d"))
    )
    conn_del.commit()

    return json.dumps({"card_id": card_id, "status": "Shipped"})


def delivery_status(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT card_id FROM customers WHERE customer_id=?", (cust_id,))
    card_id = cursor_cust.fetchone()[0]

    cursor_del.execute(
        "SELECT * FROM card_delivery WHERE card_id=?", (card_id,))
    delivery = cursor_del.fetchone()

    return json.dumps({"delivery": delivery})


def transaction_details(cust_id, trans_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_trans.execute(
        "SELECT * FROM transactions WHERE customer_id=? AND txn_id=?",
        (cust_id, trans_id)
    )
    txn = cursor_trans.fetchone()
    return json.dumps({"transaction": txn})


def process_transaction(cust_id, card_id, amount, merchant, txn_type="purchase"):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT available_limit, card_status FROM customers WHERE customer_id=?",
        (cust_id,)
    )
    result = cursor_cust.fetchone()

    if not result:
        return json.dumps({"status": "declined", "reason": "customer_not_found"})

    available, card_status = result

    if card_status != 'active':
        return json.dumps({"status": "declined", "reason": "card_not_active"})

    if txn_type == "purchase" or txn_type == "fee":
        if available < amount:
            status = "declined"
            cursor_trans.execute(
                "INSERT INTO transactions (customer_id, card_id, amount, merchant, date, txn_type, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cust_id, card_id, float(amount), merchant,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"), txn_type, status)
            )
            conn_trans.commit()
            return json.dumps({"status": "declined", "reason": "insufficient_limit"})
        else:
            status = "posted"
            cursor_cust.execute(
                "UPDATE customers SET available_limit = available_limit - ? WHERE customer_id=?",
                (int(amount), cust_id)
            )

            cursor_trans.execute(
                "SELECT current_due FROM billing_dues WHERE customer_id=?", (
                    cust_id,)
            )
            existing = cursor_trans.fetchone()

            if existing:
                cursor_trans.execute(
                    "UPDATE billing_dues SET current_due = current_due + ? WHERE customer_id=?",
                    (float(amount), cust_id)
                )
            else:
                due_date = (datetime.today() + timedelta(days=30)
                            ).strftime("%Y-%m-%d")
                minimum = round(float(amount) * 0.05, 2)
                cursor_trans.execute(
                    "INSERT INTO billing_dues VALUES (?, ?, ?, ?)",
                    (cust_id, float(amount), minimum, due_date)
                )

            conn_cust.commit()

    elif txn_type == "refund":
        status = "posted"
        cursor_cust.execute(
            "UPDATE customers SET available_limit = available_limit + ? WHERE customer_id=?",
            (int(amount), cust_id)
        )

        cursor_trans.execute(
            "UPDATE billing_dues SET current_due = MAX(0, current_due - ?) WHERE customer_id=?",
            (float(amount), cust_id)
        )

        conn_cust.commit()

    cursor_trans.execute(
        "INSERT INTO transactions (customer_id, card_id, amount, merchant, date, txn_type, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (cust_id, card_id, float(amount), merchant,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), txn_type, status)
    )
    conn_trans.commit()

    txn_id = cursor_trans.lastrowid
    return json.dumps({"status": status, "txn_id": txn_id, "amount": amount})


def pay_bill(cust_id, amount):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_trans.execute(
        "SELECT current_due FROM billing_dues WHERE customer_id=?", (cust_id,)
    )
    result = cursor_trans.fetchone()

    if not result:
        return json.dumps({"status": "no_dues_found"})

    current_due = result[0]

    if amount > current_due:
        return json.dumps({"status": "overpayment", "max_amount": current_due})

    cursor_trans.execute(
        "UPDATE billing_dues SET current_due = current_due - ? WHERE customer_id=?",
        (float(amount), cust_id)
    )

    cursor_cust.execute(
        "UPDATE customers SET available_limit = available_limit + ? WHERE customer_id=?",
        (int(amount), cust_id)
    )

    conn_trans.commit()
    conn_cust.commit()

    return json.dumps({"status": "success", "amount_paid": amount, "remaining_due": current_due - amount})


def emi_creation(cust_id, amount, months=12, rate=12.0):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_cust.execute(
        "SELECT available_limit FROM customers WHERE customer_id=?", (cust_id,)
    )
    result = cursor_cust.fetchone()

    if not result:
        return json.dumps({"status": "customer_not_found"})

    available = result[0]

    if available < amount:
        return json.dumps({"status": "insufficient_limit", "available": available, "required": amount})

    loan_id = f"LOAN{datetime.now().strftime('%f')}"
    start_date = datetime.today().strftime("%Y-%m-%d")

    cursor_emi.execute(
        "INSERT INTO loan_master VALUES (?, ?, ?, ?, ?, ?, ?)",
        (loan_id, cust_id, float(amount), float(
            rate), int(months), start_date, "active")
    )

    emi_amount = round(float(amount) * (1 + float(rate) /
                       100 * int(months)/12) / int(months), 2)
    cursor_emi.execute("PRAGMA table_info(emi_schedule)")
    emi_schedule_info = cursor_emi.fetchall()
    emi_schedule_columns = [row[1] for row in emi_schedule_info]

    for i in range(months):
        due = (datetime.today() + timedelta(days=30*(i+1))).strftime("%Y-%m-%d")

        if 'principal_part' in emi_schedule_columns and 'interest_part' in emi_schedule_columns:
            principal = round(float(amount) / int(months), 2)
            interest = round(emi_amount - principal, 2)
            cursor_emi.execute(
                "INSERT INTO emi_schedule (loan_id, due_date, emi_amount, principal_part, interest_part, status) VALUES (?, ?, ?, ?, ?, ?)",
                (loan_id, due, float(emi_amount), float(
                    principal), float(interest), "pending")
            )
        elif 'principal' in emi_schedule_columns and 'interest' in emi_schedule_columns:
            principal = round(float(amount) / int(months), 2)
            interest = round(emi_amount - principal, 2)
            cursor_emi.execute(
                "INSERT INTO emi_schedule (loan_id, due_date, emi_amount, principal, interest, status) VALUES (?, ?, ?, ?, ?, ?)",
                (loan_id, due, float(emi_amount), float(
                    principal), float(interest), "pending")
            )
        else:
            cursor_emi.execute(
                "INSERT INTO emi_schedule (loan_id, due_date, emi_amount, status) VALUES (?, ?, ?, ?)",
                (loan_id, due, float(emi_amount), "pending")
            )

    cursor_cust.execute(
        "UPDATE customers SET available_limit = available_limit - ? WHERE customer_id=?",
        (int(amount), cust_id)
    )

    conn_cust.commit()
    conn_emi.commit()

    return json.dumps({"loan_id": loan_id, "emi_amount": emi_amount, "months": months, "status": "active"})


def emi_pay(cust_id, loan_id, schedule_id, amount, mode="manual"):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_emi.execute(
        "SELECT * FROM emi_schedule WHERE schedule_id=? AND loan_id=?",
        (int(schedule_id), loan_id)
    )
    row = cursor_emi.fetchone()

    if not row:
        return json.dumps({"status": "invalid_schedule"})

    cursor_emi.execute("PRAGMA table_info(emi_schedule)")
    columns = [col[1] for col in cursor_emi.fetchall()]
    row_dict = dict(zip(columns, row))

    emi_due = row_dict.get('emi_amount', 0)
    status = row_dict.get('status', '')

    principal_part = row_dict.get(
        'principal_part') or row_dict.get('principal', 0)

    if status == "paid":
        return json.dumps({"status": "already_paid"})

    pay_status = "success" if amount >= emi_due else "failed"

    cursor_emi.execute(
        "INSERT INTO emi_payments (loan_id, schedule_id, amount_paid, paid_date, mode, status) VALUES (?, ?, ?, ?, ?, ?)",
        (loan_id, int(schedule_id), float(amount),
         datetime.today().strftime("%Y-%m-%d"), mode, pay_status)
    )

    if pay_status == "success":
        cursor_emi.execute(
            "UPDATE emi_schedule SET status='paid' WHERE schedule_id=? AND loan_id=?",
            (int(schedule_id), loan_id)
        )

        if principal_part > 0:
            cursor_cust.execute(
                "UPDATE customers SET available_limit = available_limit + ? WHERE customer_id=?",
                (int(principal_part), cust_id)
            )
            conn_cust.commit()

        cursor_emi.execute(
            "SELECT COUNT(*) FROM emi_schedule WHERE loan_id=? AND status != 'paid'",
            (loan_id,)
        )
        pending_count = cursor_emi.fetchone()[0]

        if pending_count == 0:
            cursor_emi.execute(
                "UPDATE loan_master SET status='closed' WHERE loan_id=?",
                (loan_id,)
            )

    conn_emi.commit()
    return json.dumps({"status": pay_status, "schedule_id": schedule_id, "amount_paid": amount})


def emi_details(cust_id, loan_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_emi.execute(
        "SELECT * FROM emi_schedule WHERE loan_id=?", (loan_id,))
    schedules = cursor_emi.fetchall()

    cursor_emi.execute(
        "SELECT * FROM emi_payments WHERE loan_id=?", (loan_id,))
    payments = cursor_emi.fetchall()

    return json.dumps({"schedules": schedules, "payments": payments})


def bill_details(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_trans.execute(
        "SELECT * FROM billing_dues WHERE customer_id=?", (cust_id,))
    bills = cursor_trans.fetchall()
    return json.dumps({"bills": bills})


def bank_statement(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_trans.execute(
        "SELECT * FROM transactions WHERE customer_id=?", (cust_id,))
    transactions = cursor_trans.fetchall()

    cursor_trans.execute(
        "SELECT * FROM billing_dues WHERE customer_id=?", (cust_id,))
    bills = cursor_trans.fetchall()

    return json.dumps({"transactions": transactions, "bills": bills})


def create_alert(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_emi.execute(
        "SELECT loan_id, due_date FROM emi_schedule "
        "WHERE status='pending' AND loan_id IN (SELECT loan_id FROM loan_master WHERE customer_id=?)",
        (cust_id,)
    )
    alerts = cursor_emi.fetchall()
    return json.dumps({"emi_alerts": alerts})


def collection_alert(cust_id):
    cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
    cursor_emi.execute(
        "SELECT loan_id, amount_paid FROM emi_payments "
        "WHERE status='success' AND loan_id IN (SELECT loan_id FROM loan_master WHERE customer_id=?)",
        (cust_id,)
    )
    collections = cursor_emi.fetchall()
    return json.dumps({"collected_emis": collections})


def RAG_query(question, db):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vector_store = FAISS.load_local(
        "faiss_store",
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    prompt = PromptTemplate(
        input_variables=["context", "user_question"],
        template="""
        You are a helpful banking assistant. Users are asking about banking terms, policies, and procedures.

        - Answer accurately and clearly.
        - If the question is outside banking, reply "I am not aware of this."
        - Keep the answer concise and professional.

        Context:
        {context}

        Question:
        {user_question}

        Answer:
        """
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.3
    )

    # Build the RAG pipeline
    rag_chain = (
        {
            "context": retriever,
            "user_question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain.invoke(question)
