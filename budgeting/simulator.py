"""Module with base class for agent and simulation."""

import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from itertools import chain, groupby
from operator import attrgetter


from budgeting.assets.asset import Asset
from budgeting.core.transactions import (
    ExpectedTransaction,
    Transaction,
    TransactionType,
)


class BuyStrategy(ABC):
    """Buying strategy base class."""

    @abstractmethod
    def buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Make buy decisions.

        :param balance: The agent's current liquid money.
        :param assets: The list of assets owned by the agent.
        :param simulation_day: The day of the simulation.
        :return: A list of actions with 'keep' or 'sell' instructions.
        """


class SellStrategy(ABC):
    """Selling strategy base class."""

    @abstractmethod
    def sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Make buy/sell decisions.

        :param balance: The agent's current liquid money.
        :param assets: The list of assets owned by the agent.
        :param simulation_day: The day of the simulation.
        :return: A list of actions with 'keep' or 'sell' instructions.
        """


class Agent:
    """Agent for decision-making."""

    def __init__(
        self, buying_strategy: BuyStrategy, selling_strategy: SellStrategy
    ) -> None:
        """
        Initialize the agent with its strategies.

        :param buying_strategy:
        :param selling_strategy:
        """
        self.selling_strategy = selling_strategy
        self.buying_strategy = buying_strategy

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
        return self.selling_strategy.sell(balance, assets, simulation_day)

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
        return self.buying_strategy.buy(balance, assets, simulation_day)


class AssetTransactionType(Enum):
    """Type of asset transaction."""

    BUY = "buy"
    SELL = "sell"


@dataclass
class AssetTransaction:
    """Transaction of an agent on an asset."""

    date: datetime
    asset_name: str
    value: float
    transaction_type: AssetTransactionType


class Simulation:
    """
    Simulation of projected finances.

    Attributes
    ----------
        executed_transactions: The expected transactions that were executed
        agent_transactions_history: Transactions executed by the agent



    """

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
        self.agent_transactions_history = []
        self.cash_in_hand_history = []
        self.asset_valuation_history = []
        self.assets = []

        self.sold_assets = []

    def simulate(self, start_balance: float) -> list[Transaction]:
        """
        Run the simulation.

        :param start_balance: Initial cash on hand for the simulations.
        :return: The executed transactions.
        """
        # TODO: Keep track of asset lifetime and accumulated value by the steps!
        # Generate all transactions
        all_expected_transactions = sorted(
            chain.from_iterable(
                expected_transaction.generate_transactions()
                for expected_transaction in self.expected_transactions
            ),
            key=lambda x: (x.date, x.category),
        )

        # Initialize tracking variables
        self.executed_transactions = []
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
            self.executed_transactions.extend(fixed_transactions)
            current_balance += cashflow

            # STEP 2: Allow agent to sell
            current_balance += self._agent_sell(
                current_balance, simulation_day, current_date
            )

            # STEP 3: Allow agent to buy
            current_balance -= self._agent_buy(
                current_balance, simulation_day, current_date
            )

            # STEP 4: Record and evolve
            self.asset_valuation_history.append(
                sum(asset.value for asset in self.assets)
            )
            # Evolve existing assets
            for asset in self.assets:
                asset.step()

            self.cash_in_hand_history.append(current_balance)
            current_date = current_date + timedelta(days=1)
            simulation_day += 1

        return self.executed_transactions

    def _agent_sell(
        self, cash_on_hand: float, simulation_day: int, simulation_date: datetime.date
    ) -> float:
        """Handle agent sell decisions."""
        cashflow = 0

        sell_decisions = self.agent.decide_sell(
            cash_on_hand, assets=self.assets, simulation_day=simulation_day
        )

        new_asset_set = []
        for i, sell in enumerate(sell_decisions):
            if sell:
                self.agent_transactions_history.append(
                    AssetTransaction(
                        date=simulation_date,
                        asset_name=self.assets[i].__class__.__name__,
                        transaction_type=AssetTransactionType.SELL,
                        value=self.assets[i].value,
                    )
                )
                self.sold_assets.append(self.assets[i])
                cashflow += self.assets[i].value
            else:
                new_asset_set.append(self.assets[i])

        self.assets = new_asset_set

        return cashflow

    def _agent_buy(
        self, cash_on_hand: float, simulation_day: int, simulation_date: datetime.date
    ) -> float:
        """
        Handle agent buy decisions.

        Handles the logic for buying new assets and logging it into the history.

        :param cash_on_hand: The cash on hand for the agent
        :param simulation_day: Tne day number of the simulation.
        :param simulation_date: The date of the simulation
        """
        cashflow = 0

        bought_assets = self.agent.decide_buy(
            cash_on_hand, assets=self.assets, simulation_day=simulation_day
        )

        # Assertion that agent didnt magically multiply money
        if (
            len(bought_assets) > 0
            and sum(asset.value for asset in bought_assets) > cash_on_hand
        ):
            raise RuntimeError("Agent attempted to buy without enough money")

        for asset in bought_assets:
            self.agent_transactions_history.append(
                AssetTransaction(
                    asset_name=asset.__class__.__name__,
                    transaction_type=AssetTransactionType.BUY,
                    value=asset.value,
                    date=simulation_date,
                )
            )

            cashflow += asset.value

        self.assets.extend(bought_assets)

        return cashflow

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
            if transaction.transaction_type == AssetTransactionType.INCOME:
                category_cashflow[transaction.category] += transaction.value
            elif transaction.transaction_type == AssetTransactionType.EXPENSE:
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

    def summary(self) -> dict[str, float]:
        """
        Compute and return the summary of executed transactions.

        :return: A dictionary with total income, total expenses, and net cash flow.
        """
        total_income = 0
        total_expenses = 0

        # Compute total income and total expenses
        for transaction in self.executed_transactions:
            if transaction.transaction_type == TransactionType.INCOME:
                total_income += transaction.value
            elif transaction.transaction_type == TransactionType.EXPENSE:
                total_expenses += transaction.value

        # Compute net cash flow (income - expenses)
        net_cash_flow = total_income - total_expenses

        # Return the summary as a dictionary
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_cash_flow": net_cash_flow,
        }
