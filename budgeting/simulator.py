"""Module with base class for agent and simulation."""

import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import timedelta
from itertools import chain, groupby
from operator import attrgetter


from budgeting.assets.asset import Asset
from budgeting.core.transactions import (
    ExpectedTransaction,
    TransactionType,
    Transaction,
)


class Agent(ABC):
    """Abstract agent interface for decision-making."""

    @abstractmethod
    def decide_sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Make buy/sell decisions.

        :param balance: The agent's current liquid money.
        :param assets: The list of assets owned by the agent.
        :param simulation_day: The day of the simulation.
        :return: A list of actions with 'keep' or 'sell' instructions.
        """

    @abstractmethod
    def decide_buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Make buy decisions.

        :param balance: The agent's current liquid money.
        :param assets: The list of assets owned by the agent.
        :param simulation_day: The day of the simulation.
        :return: A list of actions with 'keep' or 'sell' instructions.
        """


class Simulation:
    """Simulation of projected finances."""

    def __init__(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        expected_transactions: list[ExpectedTransaction],
        agent: Agent,
    ) -> None:
        """
        Initialize the simulation.

        :param start_date: Starting date of the simulation.
        :param end_date: End date of the simulation.
        :param expected_transactions: The expected transactions.
        :param agent: The agent that operates the simulation
        """
        self.expected_transactions = expected_transactions
        self.end_date = end_date
        self.start_date = start_date
        self.agent = agent

        self.executed_transactions = []
        self.balance_history = []
        self.net_valuation_history = []
        self.assets = []

    def simulate(self, start_balance: int) -> list[Transaction]:
        """
        Run the simulation.

        :param start_balance:
        :return: The executed transactions.
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
        executed_transactions = []
        current_balance = start_balance

        transactions_by_date = [
            (key, list(group))  # Convert each group (sub-iterator) to a list
            for key, group in groupby(all_expected_transactions, key=attrgetter("date"))
        ]

        current_date = self.start_date
        simulation_day = 0
        transaction_index = 0
        while current_date < self.end_date:
            # Retrieve the transactions relevant
            fixed_transactions, transaction_index = self._get_next_transactions(
                transactions_by_date,
                max_date=current_date,
                current_index=transaction_index,
            )

            # STEP 1: Execute the fixed transactions
            cashflow = self._execute_transactions(fixed_transactions)
            executed_transactions.extend(fixed_transactions)
            current_balance += cashflow

            # STEP 2: Allow agent to sell
            sell_decisions = self.agent.decide_sell(
                current_balance, assets=self.assets, simulation_day=simulation_day
            )

            new_asset_set = []
            for i, sell in enumerate(sell_decisions):
                if sell:
                    current_balance += self.assets[i].value
                else:
                    new_asset_set.append(self.assets[i])

            self.assets = new_asset_set

            # TODO: Add borrowing here if balance is negative!

            # STEP 3: Allow agent to buy
            bought_assets = self.agent.decide_buy(
                current_balance, assets=self.assets, simulation_day=simulation_day
            )

            # Assertion that agent didnt magically multiply money
            if sum(asset.value for asset in bought_assets) > current_balance:
                raise RuntimeError("Agent attempted to buy without money")

            for asset in bought_assets:
                current_balance -= asset.value

            self.assets.extend(bought_assets)

            self.net_valuation_history.append(sum(asset.value for asset in self.assets))
            # Evolve existing assets
            for asset in self.assets:
                asset.step()

            self.balance_history.append(current_balance)
            current_date = current_date + timedelta(days=1)
            simulation_day += 1

        return executed_transactions

    def _get_next_transactions(
        self,
        expected_transactions: list[tuple[datetime.date, Transaction]],
        current_index: int,
        max_date: datetime.date,
    ) -> tuple[list[Transaction], int]:
        """
        Get all transactions before the maximum date given.

        :param expected_transactions: Iterable with grouped transactions.
        :param max_date: The date until which transaction are to be given (included)
        :return:
        """
        # TODO: THis function can be optimized using "tee" of itertools and iterators
        # to loop only once. Not needed for now.
        next_transactions = []
        while current_index < len(expected_transactions):
            date, transactions = expected_transactions[current_index]

            if self.start_date <= date <= max_date:
                transactions = [transaction for transaction in transactions]

                next_transactions.extend(transactions)
            elif date < self.start_date:
                pass
            else:
                break
            current_index += 1

        return next_transactions, current_index

    @staticmethod
    def _get_cashflow(transactions: list[Transaction]) -> dict[str, float]:
        """
        Get the cashflow by category from a list of transactions.

        :param transactions: Transactions
        :return: Dictionary mapping categories to cashflow
        """
        category_cashflow = defaultdict(float)

        for transaction in transactions:
            if transaction.transaction_type == TransactionType.INCOME:
                category_cashflow[transaction.category] += transaction.value
            elif transaction.transaction_type == TransactionType.EXPENSE:
                category_cashflow[transaction.category] -= transaction.value

        return category_cashflow

    @staticmethod
    def _execute_transactions(transactions: list[Transaction]) -> float:
        """
        Obtain cashflow after transactions.

        :param transactions: List of transactions to execute.
        :return:
        """
        cashflow = 0

        for transaction in transactions:
            if transaction.transaction_type == TransactionType.INCOME:
                cashflow += transaction.value
            elif transaction.transaction_type == TransactionType.EXPENSE:
                cashflow -= transaction.value

        return cashflow
