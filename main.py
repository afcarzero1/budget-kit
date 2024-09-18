import datetime


from budgeting.agents.safe_agent import (
    ConservativeSellStrategy,
    ConservativeBuyStrategy,
)
from budgeting.core.transactions import (
    ExpectedTransaction,
    TransactionType,
    RecurrenceType,
)
from budgeting.simulator import Simulation, Agent
from budgeting.visualization import FinancialVisualization


def main():
    """Simulation runner."""
    simulation = Simulation(
        start_date=datetime.date(2024, 10, 1),
        end_date=datetime.date(2025, 10, 1),
        expected_transactions=[
            ExpectedTransaction(
                category="Rent",
                initial_date=datetime.date(2024, 10, 1),
                final_date=datetime.date(2025, 10, 1),
                transaction_type=TransactionType.EXPENSE,
                recurrence=RecurrenceType.MONTHLY,
                recurrence_value=1,
                value=10_000,
            ),
            ExpectedTransaction(
                category="Groceries",
                initial_date=datetime.date(2024, 10, 1),
                final_date=datetime.date(2025, 10, 1),
                transaction_type=TransactionType.EXPENSE,
                recurrence=RecurrenceType.WEEKLY,
                recurrence_value=1,
                value=650,
            ),
            ExpectedTransaction(
                category="Salary",
                initial_date=datetime.date(2024, 10, 1),
                final_date=datetime.date(2025, 10, 1),
                transaction_type=TransactionType.INCOME,
                recurrence=RecurrenceType.MONTHLY,
                recurrence_value=1,
                value=18_000,
            ),
            ExpectedTransaction(
                category="Fun",
                initial_date=datetime.date(2024, 10, 4),
                final_date=datetime.date(2025, 10, 2),
                transaction_type=TransactionType.EXPENSE,
                recurrence=RecurrenceType.WEEKLY,
                recurrence_value=1,
                value=1000,
            ),
        ],
        agent=Agent(
            ConservativeBuyStrategy(15_000, 25_000), ConservativeSellStrategy(15_000)
        ),
    )

    executed_transactions = simulation.simulate(start_balance=100_000)

    analyzer = FinancialVisualization(simulation)

    fig = analyzer.plot_monthly_cashflow()
    fig.show()

    fig = analyzer.plot_monthly_expenses_breakdown()
    fig.show()

    fig = analyzer.plot_cash_in_hand_history()
    fig.show()

    fig = analyzer.plot_asset_valuation_history()
    fig.show()

    fig = analyzer.plot_net_worth_history()
    fig.show()


if __name__ == "__main__":
    main()
