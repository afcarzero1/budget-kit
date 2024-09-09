from dataclasses import dataclass
import datetime
from enum import Enum

from dateutil.relativedelta import relativedelta


class TransactionType(Enum):
    """Transaction type."""

    EXPENSE = ("EXPENSE",)
    INCOME = "INCOME"


class RecurrenceType(Enum):
    """Recurrence type."""

    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


@dataclass
class Transaction:
    """Transaction."""

    category: str
    date: datetime.date
    transaction_type: TransactionType
    value: float


@dataclass(frozen=True)
class ExpectedTransaction:
    """Expected transaction."""

    category: str
    initial_date: datetime.date
    final_date: datetime.date | None
    transaction_type: TransactionType
    recurrence: RecurrenceType
    recurrence_value: int
    value: float

    def __post_init__(self):
        """Ensure data is correct."""
        if self.final_date < self.initial_date:
            raise ValueError(
                f"Final date {self.final_date} is before initial date {self.initial_date}."
            )

        if self.value < 0:
            raise ValueError("Value cannot be negative")

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
