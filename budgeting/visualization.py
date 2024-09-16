"""Module with the visualization classes."""

import pandas as pd
from plotly.graph_objs import Bar, Scatter

from .core.transactions import TransactionType
from .simulator import Simulation
from plotly.graph_objs._figure import Figure


class FinancialVisualization:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation

    def plot_monthly_cashflow(self) -> Figure:
        # Creating DataFrame from transactions
        df = pd.DataFrame(
            [
                {
                    "date": trans.date,
                    "value": trans.value
                    if trans.transaction_type == TransactionType.INCOME
                    else -trans.value,
                }
                for trans in self.simulation.executed_transactions
            ]
        )

        # Ensure 'date' is a datetime type
        df["date"] = pd.to_datetime(df["date"])

        # Extracting month from date
        df["month"] = df["date"].dt.to_period("M")

        # Aggregating positive (income) and negative (expenses) values by month
        monthly_incomes = df[df["value"] > 0].groupby("month")["value"].sum()
        monthly_expenses = df[df["value"] < 0].groupby("month")["value"].sum()
        net_cash_flow = (
            monthly_incomes + monthly_expenses
        )  # This automatically aligns on the index

        # Convert 'month' from Period to datetime for plotting
        monthly_incomes.index = monthly_incomes.index.to_timestamp()
        monthly_expenses.index = monthly_expenses.index.to_timestamp()
        net_cash_flow.index = net_cash_flow.index.to_timestamp()

        # Create the figure
        fig = Figure()

        # Adding plots
        fig.add_trace(
            Bar(
                x=monthly_expenses.index,
                y=monthly_expenses,
                name="Expenses",
                marker_color="red",
            )
        )
        fig.add_trace(
            Bar(
                x=monthly_incomes.index,
                y=monthly_incomes,
                name="Incomes",
                marker_color="green",
            )
        )
        fig.add_trace(
            Scatter(
                x=net_cash_flow.index,
                y=net_cash_flow,
                mode="lines+markers",
                name="Net Cash Flow",
            )
        )

        # Update layout
        fig.update_layout(
            title="Monthly Cash Flow Analysis",
            xaxis_title="Month",
            yaxis_title="Amount",
            barmode="group",
            # Use 'group' for side-by-side bars, 'overlay' to see overlap
            template="plotly_white",
        )

        return fig
