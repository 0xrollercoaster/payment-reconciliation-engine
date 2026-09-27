import csv

internal_db = {}
issues_report = []

# 1. Читаем внутреннюю базу
with open("internal.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        internal_db[row["tx_id"]] = row

# 2. Проходим по выписке банка
with open("bank.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        tx_id = row["internal_tx_id"]
        bank_amount = float(row["amount_charged"])

        if tx_id not in internal_db:
            issues_report.append(
                {
                    "tx_id": tx_id,
                    "issue_type": "NOT_IN_DB",
                    "action_required": "CREATE_TX_MANUALLY",  # Действие: Восстановить транзакцию вручную
                    "priority": "HIGH",
                }
            )

        elif internal_db[tx_id]["status"] == "PENDING":
            issues_report.append(
                {
                    "tx_id": tx_id,
                    "issue_type": "PENDING_STATUS",
                    "action_required": "AUTO_UPDATE_TO_SUCCESS",  # Действие: Авто-подтверждение
                    "priority": "MEDIUM",
                }
            )

        else:
            db_amount = float(internal_db[tx_id]["amount"])
            if bank_amount != db_amount:
                issues_report.append(
                    {
                        "tx_id": tx_id,
                        "issue_type": "AMOUNT_MISMATCH",
                        "action_required": "ADJUST_BALANCE",  # Действие: Скорректировать баланс
                        "priority": "HIGH",
                    }
                )

# 3. Проверяем неоплченные услуги
bank_tx_ids = set()
with open("bank.csv", mode="r", encoding="utf-8") as f:
    bank_tx_ids = {row["internal_tx_id"] for row in csv.DictReader(f)}

for tx_id, data in internal_db.items():
    if data["status"] == "SUCCESS" and tx_id not in bank_tx_ids:
        issues_report.append(
            {
                "tx_id": tx_id,
                "issue_type": "UNPAID_SERVICE",
                "action_required": "BLOCK_USER_AND_REVOKE",  # Действие: Заблокировать услугу/фрод
                "priority": "CRITICAL",
            }
        )

# 4. Сохраняем в расширенный отчет
with open(
    "discrepancies_report.csv", mode="w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=["tx_id", "issue_type", "action_required", "priority"]
    )
    writer.writeheader()
    writer.writerows(issues_report)

print("Обновленный отчет с приоритетами и действиями успешно сформирован!")