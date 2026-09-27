import sqlite3

# 1. Создаем базу данных прямо в оперативной памяти (без сохранения на диск)
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# 2. Создаем таблицы базы данных на языке SQL (DDL)
cursor.execute("""
CREATE TABLE internal_transactions (
    tx_id TEXT PRIMARY KEY,
    user_id TEXT,
    amount REAL,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE bank_settlements (
    internal_tx_id TEXT PRIMARY KEY,
    amount_charged REAL,
    fee REAL
)
""")

# 3. Заполняем таблицы тестовыми данными (DML)
internal_data = [
    ("TX1001", "usr_1", 1000.0, "SUCCESS"),
    ("TX1002", "usr_2", 500.0, "PENDING"),
    ("TX1003", "usr_3", 1500.0, "SUCCESS"),
    ("TX1004", "usr_4", 2000.0, "SUCCESS"),
]

bank_data = [
    ("TX1001", 1000.0, 30.0),
    ("TX1002", 500.0, 15.0),
    ("TX1003", 1400.0, 42.0),
    ("TX1005", 800.0, 24.0),
]

cursor.executemany(
    "INSERT INTO internal_transactions VALUES (?, ?, ?, ?)", internal_data
)
cursor.executemany("INSERT INTO bank_settlements VALUES (?, ?, ?)", bank_data)
conn.commit()

# 4. Главный SQL-запрос сверки (Reconciliation Query)
sql_reconciliation_query = """
SELECT 
    COALESCE(t.tx_id, b.internal_tx_id) AS transaction_id,
    COALESCE(t.amount, 0) AS db_amount,
    COALESCE(b.amount_charged, 0) AS bank_amount,
    CASE 
        WHEN b.internal_tx_id IS NULL THEN 'UNPAID_SERVICE'
        WHEN t.tx_id IS NULL THEN 'NOT_IN_DB'
        WHEN t.status = 'PENDING' THEN 'PENDING_STATUS'
        WHEN t.amount != b.amount_charged THEN 'AMOUNT_MISMATCH'
        ELSE 'OK'
    END AS issue_type
FROM internal_transactions t
LEFT JOIN bank_settlements b ON t.tx_id = b.internal_tx_id

UNION ALL

SELECT 
    b.internal_tx_id AS transaction_id,
    0 AS db_amount,
    b.amount_charged AS bank_amount,
    'NOT_IN_DB' AS issue_type
FROM bank_settlements b
LEFT JOIN internal_transactions t ON b.internal_tx_id = t.tx_id
WHERE t.tx_id IS NULL;
"""

# 5. Выполняем SQL-запрос и выводим результаты
cursor.execute(sql_reconciliation_query)
rows = cursor.fetchall()

print("=========================================================")
print("          РЕЗУЛЬТАТ SQL-СВЕРКИ (SQL RECONCILIATION)      ")
print("=========================================================")
print(f"{'TX_ID':<10} | {'DB_AMT':<8} | {'BANK_AMT':<8} | {'ISSUE_TYPE'}")
print("-" * 57)

for row in rows:
    tx_id, db_amt, bank_amt, issue = row
    # Выводим только аномалии (игнорируем OK)
    if issue != "OK":
        print(f"{tx_id:<10} | {db_amt:<8.1f} | {bank_amt:<8.1f} | {issue}")

print("=========================================================")

# Закрываем соединение
conn.close()