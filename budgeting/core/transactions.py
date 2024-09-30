from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum

import pandas as pd
from dateutil.relativedelta import relativedelta


class TransactionType(Enum):
    """Transaction type."""

    EXPENSE = "EXPENSE"
    INCOME = "INCOME"


class RecurrenceType(Enum):
    """Recurrence type."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


@dataclass
class Transaction:
    """Transaction."""

    category: str
    date: datetime.date
    transaction_type: TransactionType
    value: float


@dataclass
class ExpectedTransaction:
    """Expected transaction."""

    category: str
    initial_date: datetime.date
    final_date: datetime.date
    transaction_type: TransactionType
    recurrence: RecurrenceType
    recurrence_value: int
    value: float

    def validate(self) -> str | None:
        """Validate whether data is correct."""
        if self.final_date < self.initial_date:
            return (
                f"Final date {self.final_date} is before initial date {self.initial_date}."
            )

        if self.value < 0:
            return "Value cannot be negative"

        if self.recurrence not in (RecurrenceType.WEEKLY, RecurrenceType.MONTHLY):
            return "Recurrence must be weekly or monthly"

        return None
    
    def generate_transactions(self) -> list[Transaction]:
        """
        Generate all the expected transactions.

        :return: The list with expected transactions.
        """
        transactions = []
        current_date = self.initial_date
        while current_date < self.final_date:
            transactions.append(
                Transaction(
                    category=self.category,
                    date=current_date,
                    transaction_type=self.transaction_type,
                    value=self.value,
                )
            )

            current_date += (
                relativedelta(weeks=self.recurrence_value)
                if self.recurrence == RecurrenceType.WEEKLY
                else relativedelta(months=self.recurrence_value)
            )

        return transactions

    @staticmethod
    def transactions2df(
        expected_transactions: list[ExpectedTransaction],
    ) -> pd.DataFrame:
        """
        Convert a list of ExpectedTransaction objects to a DataFrame.

        :param expected_transactions: List with expected transactions.
        """
        columns = [
            "Category",
            "Initial Date",
            "Final Date",
            "Transaction Type",
            "Recurrence",
            "Recurrence Value",
            "Value",
        ]
        if not expected_transactions:
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(
            [
                {
                    "Category": transaction.category,
                    "Initial Date": transaction.initial_date,
                    "Final Date": transaction.final_date,
                    "Transaction Type": transaction.transaction_type.name,
                    "Recurrence": transaction.recurrence.name,
                    "Recurrence Value": transaction.recurrence_value,
                    "Value": transaction.value,
                }
                for transaction in expected_transactions
            ],
            columns=columns,
        )

    @staticmethod
    def df2transactions(df: pd.DataFrame) -> list[ExpectedTransaction]:
        """Read a CSV and convert it back to a list of ExpectedTransaction objects."""
        return [
            ExpectedTransaction(
                category=row["Category"],
                initial_date=pd.to_datetime(row["Initial Date"]).date(),
                final_date=pd.to_datetime(row["Final Date"]).date(),
                transaction_type=TransactionType[row["Transaction Type"]],
                recurrence=RecurrenceType[row["Recurrence"]],
                recurrence_value=int(row["Recurrence Value"]),
                value=float(row["Value"]),
            )
            for _, row in df.iterrows()
        ]
