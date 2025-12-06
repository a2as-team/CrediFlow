import sqlite3


def run_sql(db_name, sql_commands):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.executescript(sql_commands)
    conn.commit()
    conn.close()
    print(f"Database created: {db_name}")


customers_sql = """
DROP TABLE IF EXISTS customer_logins;
DROP TABLE IF EXISTS customers;

CREATE TABLE customer_logins (
    customer_id TEXT PRIMARY KEY,
    phone TEXT,
    email TEXT UNIQUE,
    password_hash TEXT
);

INSERT INTO customer_logins VALUES
("CUST001", "9000000001", "rahul.singh@example.com", "hash_pw_rahul"),
("CUST002", "9000000002", "neha.sharma@example.com", "hash_pw_neha"),
("CUST003", "9000000003", "arjun.mehta@example.com", "hash_pw_arjun"),
("CUST004", "9000000004", "priya.verma@example.com", "hash_pw_priya"),
("CUST005", "9000000005", "amit.jain@example.com", "hash_pw_amit"),
("CUST006", "9000000006", "sara.khan@example.com", "hash_pw_sara"),
("CUST007", "9000000007", "vikram.rao@example.com", "hash_pw_vikram"),
("CUST008", "9000000008", "kavita.yadav@example.com", "hash_pw_kavita"),
("CUST009", "9000000009", "dev.patel@example.com", "hash_pw_dev"),
("CUST010", "9000000010", "isha.malhotra@example.com", "hash_pw_isha"),
("CUST011", "9000000011", "varun.sethi@example.com", "hash_pw_varun"),
("CUST012", "9000000012", "meera.nair@example.com", "hash_pw_meera");

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT,
    card_id TEXT,
    credit_limit INTEGER,
    available_limit INTEGER,
    card_status TEXT
);

INSERT INTO customers VALUES
("CUST001", "Rahul Singh", "CARD001", 120000, 85000, "active"),
("CUST002", "Neha Sharma", "CARD002", 100000, 45000, "active"),
("CUST003", "Arjun Mehta", "CARD003", 90000, 20000, "active"),
("CUST004", "Priya Verma", "CARD004", 70000, 50000, "active"),
("CUST005", "Amit Jain", "CARD005", 150000, 100000, "active"),
("CUST006", "Sara Khan", "CARD006", 130000, 30000, "blocked"),
("CUST007", "Vikram Rao", "CARD007", 80000, 60000, "active"),
("CUST008", "Kavita Yadav", "CARD008", 110000, 90000, "active"),
("CUST009", "Dev Patel", "CARD009", 95000, 75000, "active"),
("CUST010", "Isha Malhotra", "CARD010", 125000, 85000, "active"),
("CUST011", "Varun Sethi", "CARD011", 50000, 20000, "delinquent"),
("CUST012", "Meera Nair", "CARD012", 60000, 40000, "active");
"""

delivery_sql = """
DROP TABLE IF EXISTS card_delivery;

CREATE TABLE card_delivery (
    card_id TEXT PRIMARY KEY,
    courier TEXT,
    tracking_number TEXT,
    delivery_status TEXT,
    expected_delivery_date TEXT
);

INSERT INTO card_delivery VALUES
("CARD001", "BlueDart", "BD123001", "Delivered", "2025-01-10"),
("CARD002", "Delhivery", "DLV223002", "Out for Delivery", "2025-01-14"),
("CARD003", "EcomExpress", "ECX553003", "In Transit", "2025-01-17"),
("CARD004", "BlueDart", "BD183004", "Shipped", "2025-01-18"),
("CARD005", "Delhivery", "DLV443005", "Delivered", "2025-01-08"),
("CARD006", "EcomExpress", "ECX983006", "Returned", "2025-01-12"),
("CARD007", "BlueDart", "BD663007", "Delivered", "2025-01-11"),
("CARD008", "Delhivery", "DLV223008", "Shipped", "2025-01-19"),
("CARD009", "BlueDart", "BD873009", "In Transit", "2025-01-16"),
("CARD010", "EcomExpress", "ECX743010", "Out for Delivery", "2025-01-14"),
("CARD011", "Delhivery", "DLV128011", "Delayed", "2025-01-20"),
("CARD012", "BlueDart", "BD999012", "Delivered", "2025-01-09");
"""

transactions_sql = """
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS billing_dues;

CREATE TABLE transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT,
    card_id TEXT,
    amount REAL,
    merchant TEXT,
    date TEXT,
    txn_type TEXT,
    status TEXT
);

INSERT INTO transactions (customer_id, card_id, amount, merchant, date, txn_type, status) VALUES
("CUST001", "CARD001", 2499, "Amazon", "2025-01-02", "purchase", "posted"),
("CUST001", "CARD001", 1199, "Swiggy", "2025-01-03", "purchase", "posted"),
("CUST001", "CARD001", 49999, "Croma", "2025-01-06", "purchase", "posted"),
("CUST001", "CARD001", 1500, "Uber", "2025-01-07", "purchase", "posted"),
("CUST001", "CARD001", 799, "Zomato", "2025-01-08", "purchase", "posted"),

("CUST002", "CARD002", 3500, "Amazon", "2025-01-01", "purchase", "posted"),
("CUST002", "CARD002", 899, "Blinkit", "2025-01-04", "purchase", "posted"),
("CUST002", "CARD002", 22000, "MakeMyTrip", "2025-01-05", "purchase", "posted"),
("CUST002", "CARD002", 699, "Zomato", "2025-01-06", "purchase", "posted"),
("CUST002", "CARD002", 1500, "Uber", "2025-01-09", "purchase", "posted"),

("CUST003", "CARD003", 900, "Swiggy", "2025-01-03", "purchase", "posted"),
("CUST003", "CARD003", 1299, "Amazon", "2025-01-04", "purchase", "posted"),
("CUST003", "CARD003", 4000, "Myntra", "2025-01-05", "purchase", "posted"),
("CUST003", "CARD003", 21000, "Croma", "2025-01-07", "purchase", "posted"),
("CUST003", "CARD003", 500, "Uber", "2025-01-08", "purchase", "posted"),

("CUST004", "CARD004", 550, "Blinkit", "2025-01-02", "purchase", "posted"),
("CUST004", "CARD004", 1200, "Swiggy", "2025-01-04", "purchase", "posted"),
("CUST004", "CARD004", 6000, "ShoppersStop", "2025-01-05", "purchase", "posted"),
("CUST004", "CARD004", 400, "Uber", "2025-01-06", "purchase", "posted"),
("CUST004", "CARD004", 1800, "Amazon", "2025-01-09", "purchase", "posted"),

("CUST005", "CARD005", 15000, "Apple Store", "2025-01-01", "purchase", "posted"),
("CUST005", "CARD005", 999, "Swiggy", "2025-01-03", "purchase", "posted"),
("CUST005", "CARD005", 20000, "MakeMyTrip", "2025-01-06", "purchase", "posted"),
("CUST005", "CARD005", 450, "Uber", "2025-01-07", "purchase", "posted"),
("CUST005", "CARD005", 1300, "Myntra", "2025-01-09", "purchase", "posted"),

("CUST006", "CARD006", 3000, "Amazon", "2025-01-02", "purchase", "declined"),
("CUST006", "CARD006", 800, "Zomato", "2025-01-03", "purchase", "posted"),
("CUST006", "CARD006", 12000, "Croma", "2025-01-04", "purchase", "declined"),
("CUST006", "CARD006", 500, "Uber", "2025-01-05", "purchase", "posted"),
("CUST006", "CARD006", 700, "Blinkit", "2025-01-08", "purchase", "posted"),

("CUST007", "CARD007", 2500, "Amazon", "2025-01-01", "purchase", "posted"),
("CUST007", "CARD007", 999, "Swiggy", "2025-01-03", "purchase", "posted"),
("CUST007", "CARD007", 5600, "Myntra", "2025-01-05", "purchase", "posted"),
("CUST007", "CARD007", 300, "Uber", "2025-01-06", "purchase", "posted"),
("CUST007", "CARD007", 1500, "Blinkit", "2025-01-09", "purchase", "posted"),

("CUST008", "CARD008", 4200, "Nykaa", "2025-01-01", "purchase", "posted"),
("CUST008", "CARD008", 899, "Swiggy", "2025-01-02", "purchase", "posted"),
("CUST008", "CARD008", 24500, "MakeMyTrip", "2025-01-04", "purchase", "posted"),
("CUST008", "CARD008", 750, "Uber", "2025-01-06", "purchase", "posted"),
("CUST008", "CARD008", 1999, "Amazon", "2025-01-08", "purchase", "posted"),

("CUST009", "CARD009", 350, "Uber", "2025-01-02", "purchase", "posted"),
("CUST009", "CARD009", 999, "Zomato", "2025-01-03", "purchase", "posted"),
("CUST009", "CARD009", 16000, "Croma", "2025-01-06", "purchase", "posted"),
("CUST009", "CARD009", 1300, "Myntra", "2025-01-07", "purchase", "posted"),
("CUST009", "CARD009", 2450, "Amazon", "2025-01-09", "purchase", "posted"),

("CUST010", "CARD010", 1150, "Amazon", "2025-01-01", "purchase", "posted"),
("CUST010", "CARD010", 890, "Zomato", "2025-01-02", "purchase", "posted"),
("CUST010", "CARD010", 30000, "MakeMyTrip", "2025-01-04", "purchase", "posted"),
("CUST010", "CARD010", 500, "Uber", "2025-01-06", "purchase", "posted"),
("CUST010", "CARD010", 1200, "Blinkit", "2025-01-08", "purchase", "posted"),

("CUST011", "CARD011", 4500, "Amazon", "2025-01-01", "purchase", "posted"),
("CUST011", "CARD011", 700, "Swiggy", "2025-01-02", "purchase", "posted"),
("CUST011", "CARD011", 14500, "MakeMyTrip", "2025-01-03", "purchase", "posted"),
("CUST011", "CARD011", 400, "Uber", "2025-01-06", "purchase", "posted"),
("CUST011", "CARD011", 3200, "Myntra", "2025-01-07", "purchase", "posted"),

("CUST012", "CARD012", 900, "Uber", "2025-01-01", "purchase", "posted"),
("CUST012", "CARD012", 1350, "Amazon", "2025-01-02", "purchase", "posted"),
("CUST012", "CARD012", 6000, "Croma", "2025-01-04", "purchase", "posted"),
("CUST012", "CARD012", 850, "Swiggy", "2025-01-05", "purchase", "posted"),
("CUST012", "CARD012", 4500, "ShoppersStop", "2025-01-06", "purchase", "posted");

CREATE TABLE billing_dues (
    customer_id TEXT,
    current_due REAL,
    minimum_due REAL,
    due_date TEXT
);

INSERT INTO billing_dues VALUES
("CUST001", 18000, 2500, "2025-02-10"),
("CUST002", 22000, 3200, "2025-02-11"),
("CUST003", 9000, 1500, "2025-02-12"),
("CUST004", 11000, 2000, "2025-02-11"),
("CUST005", 40000, 6000, "2025-02-10"),
("CUST006", 7000, 1200, "2025-02-09"),
("CUST007", 8000, 1600, "2025-02-12"),
("CUST008", 25000, 3500, "2025-02-13"),
("CUST009", 12000, 1800, "2025-02-11"),
("CUST010", 30000, 5000, "2025-02-10"),
("CUST011", 15000, 2400, "2025-02-09"),
("CUST012", 9000, 1500, "2025-02-10");
"""

run_sql("customers.db", customers_sql)
run_sql("delivery.db", delivery_sql)
run_sql("transactions.db", transactions_sql)

print("All databases created successfully.")
