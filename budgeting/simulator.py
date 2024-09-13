"""
1. Expected expenses and incomes
2. Decide what to sell
3. Decide what to buy

"""
import datetime
from abc import ABC, abstractmethod
from itertools import chain, groupby
from operator import attrgetter

import pandas as pd

from budgeting.assets.asset import Asset
from budgeting.core.transactions import ExpectedTransaction, TransactionType


    

class Agent(ABC):
    """Abstract agent interface for decision-making."""

    @abstractmethod
    def decide_sell(self, balance: float, assets: list[Asset]) -> list[bool]:
        """
        Make buy/sell decisions.

        :param balance: The agent's current liquid money.
        :param assets: The list of assets owned by the agent.
        :return: A list of actions with 'keep' or 'sell' instructions.
        """
        pass
    


class Simulation:
    """Simulation of projected finances."""

    def __init__(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        expected_transactions: list[ExpectedTransaction],
    ) -> None:
        """
        Initialize the simulation.

        :param start_date: Starting date of the simulation.
        :param end_date: End date of the simulation.
        :param expected_transactions: The expected transactions.
        """
        self.expected_transactions = expected_transactions
        self.end_date = end_date
        self.start_date = start_date

    def simulate(self, start_balance: int) -> (pd.DataFrame, pd.DataFrame):
        """
        Run the simulation.

        :param start_balance:
        :return:
        """
        # Generate all transactions
        all_expected_transactions = sorted(
            chain.from_iterable(
                expected_transaction.generate_transactions()
                for expected_transaction in self.expected_transactions
            ),
            key=lambda x: (x.date, x.category),
        )

        # Initialize tracking variables
        current_balance = start_balance
        summary_data = []
        category_data = []

        # Group transactions by date using groupby
        for date_key, date_group in groupby(
            all_expected_transactions, key=attrgetter("date")
        ):
            if date_key < self.start_date or date_key > self.end_date:
                continue  # Skip transactions outside the simulation period

            daily_income = 0
            daily_expense = 0

            # Process grouped transactions by date
            for category_key, category_group in groupby(
                date_group, key=attrgetter("category")
            ):
                category_income = 0
                category_expense = 0

                # Process each transaction in category group
                for transaction in category_group:
                    if transaction.transaction_type == TransactionType.INCOME:
                        category_income += transaction.value
                        daily_income += transaction.value
                    elif transaction.transaction_type == TransactionType.EXPENSE:
                        category_expense += transaction.value
                        daily_expense += transaction.value

                # Record category-specific data
                category_data.append(
                    {
                        "Date": date_key,
                        "Category": category_key,
                        "Income": category_income,
                        "Expense": category_expense,
                    }
                )

            current_balance += daily_income - daily_expense
            # Record the daily summary data
            summary_data.append(
                {
                    "Date": date_key,
                    "Balance": current_balance,
                    "Income": daily_income,
                    "Expense": daily_expense,
                }
            )

        # Convert data to DataFrames
        summary_df = pd.DataFrame(summary_data)
        category_df = pd.DataFrame(category_data)

        return summary_df, category_df

    def _run_agent(self):
        pass
