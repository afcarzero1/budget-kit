import datetime

import plotly.express as px
import plotly.graph_objects as go

from budgeting.agents.base_agent import BaseAgent
from budgeting.core.transactions import (
    ExpectedTransaction,
    TransactionType,
    RecurrenceType,
)
from budgeting.simulator import Simulation


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
                value=10000,
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
                value=10000,
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
        agent=BaseAgent(),
    )

    executed_transactions = simulation.simulate(start_balance=100_000)


def plot_balance(summary_df):
    # Create a line plot of balance over time
    fig = px.line(summary_df, x="Date", y="Balance", title="Daily Balance Over Time")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Balance",
        xaxis=dict(rangeslider=dict(visible=True)),
    )
    fig.show()


def plot_monthly_financials(monthly_financials):
    # Create a bar chart for Income and Expenses
    fig = go.Figure(
        data=[
            go.Bar(
                name="Income",
                x=monthly_financials["Date"],
                y=monthly_financials["Income"],
                marker_color="green",
            ),
            go.Bar(
                name="Expense",
                x=monthly_financials["Date"],
                y=monthly_financials["Expense"],
                marker_color="red",
            ),
        ]
    )

    # Layout settings
    fig.update_layout(
        barmode="group",
        title="Monthly Income and Expenses",
        xaxis_title="Month",
        yaxis_title="Amount",
        xaxis=dict(tickformat="%b %Y"),
        annotations=[  # Adding annotations for Cash Flow
            dict(
                x=monthly_financials["Date"][i],
                y=max(
                    monthly_financials["Income"][i], monthly_financials["Expense"][i]
                ),
                text=f"{'+' if monthly_financials['Cash Flow'][i] > 0 else '-'}{monthly_financials['Cash Flow'][i]:,.2f}",
                showarrow=False,
                yshift=10,
            )
            for i in range(len(monthly_financials))
        ],
    )

    fig.show()


def plot_category_expenses(monthly_category_expenses):
    # Define a custom color sequence that avoids green and red
    custom_colors = [
        "#1f77b4",
        "#ff7f0e",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    # Create a bar chart for expenses by category and month
    fig = px.bar(
        monthly_category_expenses,
        x="Date",
        y="Expense",
        color="Category",  # Differentiate by category
        color_discrete_sequence=custom_colors,  # Use the custom color sequence
        barmode="group",  # Place bars next to each other
        title="Monthly Expenses by Category (Filtered, Custom Colors)",
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Total Expenses",
        xaxis=dict(tickformat="%b %Y"),
    )
    fig.show()


if __name__ == "__main__":
    main()
