"""Module with the visualization classes."""

import pandas as pd
from plotly.graph_objs import Bar, Scatter

from .core.transactions import TransactionType
from .simulator import Simulation
from plotly.graph_objs._figure import Figure
import plotly.express as px
import plotly.graph_objects as go


class FinancialVisualization:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation

    def plot_monthly_cashflow(self) -> Figure:
        """
        Plot the monthly cashflow.

        :return: The plotly figure.
        """
        # Creating DataFrame from transactions
        executed_transactions_df = pd.DataFrame(
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

        executed_transactions_df["date"] = pd.to_datetime(
            executed_transactions_df["date"]
        )

        executed_transactions_df["month"] = executed_transactions_df[
            "date"
        ].dt.to_period("M")

        monthly_incomes = (
            executed_transactions_df[executed_transactions_df["value"] > 0]
            .groupby("month")["value"]
            .sum()
        )
        monthly_expenses = (
            executed_transactions_df[executed_transactions_df["value"] < 0]
            .groupby("month")["value"]
            .sum()
        )
        net_cash_flow = monthly_incomes + monthly_expenses

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

        fig.update_layout(
            title="Monthly Cash Flow Analysis",
            xaxis_title="Month",
            yaxis_title="Amount",
            barmode="group",
            template="plotly_white",
        )

        return fig

    def plot_monthly_expenses_breakdown(self) -> Figure:
        """Plot the breakdown of fixed expenses by month."""
        # Filter only expense transactions
        expenses = [
            t
            for t in self.simulation.executed_transactions
            if t.transaction_type == TransactionType.EXPENSE
        ]

        # Create a DataFrame for the filtered expenses
        df = pd.DataFrame(
            {
                "category": [t.category for t in expenses],
                "date": [t.date for t in expenses],
                "value": [t.value for t in expenses],
            }
        )

        # Add a column for year-month
        df["year_month"] = df["date"].apply(lambda x: x.strftime("%Y-%m"))

        # Group by year_month and category, and sum the values
        monthly_expenses = (
            df.groupby(["year_month", "category"])["value"].sum().reset_index()
        )

        # Plot using Plotly with side-by-side bars (barmode='group')
        fig = px.bar(
            monthly_expenses,
            x="year_month",
            y="value",
            color="category",
            barmode="group",
            title="Monthly Breakdown of Expenses by Category",
        )

        fig.update_layout(
            title={"x": 0.5, "xanchor": "center"},  # Center the title
            font=dict(size=14),
            legend_title_text="Categories",
            yaxis=dict(showgrid=False),  # Remove y-axis grid lines
            xaxis_tickformat="%b %Y",  # Format x-axis as Month Year
            legend=dict(
                orientation="h",  # Horizontal legend
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
            plot_bgcolor="white",  # Set background to white
        )
        return fig

    def plot_over_time(
        self, title: str, y_data: list[float], y_label: str
    ) -> go.Figure:
        """
        Plot values over time.

        :param title: The title of the plot.
        :param y_data: The data to plot on the y-axis.
        :param y_label: The label for the y-axis.
        :return: The Plotly figure.
        """
        # Create a DataFrame with the provided y_data
        data_df = pd.DataFrame(
            {
                "date": pd.date_range(
                    start=self.simulation.start_date,
                    end=self.simulation.end_date,
                    periods=len(y_data),
                ),
                "value": y_data,
            }
        )

        # Create the figure
        fig = go.Figure()

        # Add a trace for the y_data over time
        fig.add_trace(
            go.Scatter(
                x=data_df["date"],
                y=data_df["value"],
                mode="lines",
                name=y_label,
                line=dict(color="blue"),
            )
        )

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=y_label,
            template="plotly_white",
            xaxis=dict(tickformat="%d %b %Y"),  # Format the x-axis as Month Year
        )

        return fig

    def plot_cash_in_hand_history(self) -> go.Figure:
        """
        Plot the balance history over time.

        :return: The Plotly figure.
        """
        return self.plot_over_time(
            title="Balance History Over Time",
            y_data=self.simulation.cash_in_hand_history,
            y_label="Balance",
        )

    def plot_asset_valuation_history(self) -> go.Figure:
        """
        Plot the asset valuation history over time.

        :return: The Plotly figure.
        """
        return self.plot_over_time(
            title="Asset Valuation History Over Time",
            y_data=self.simulation.asset_valuation_history,  # Assuming this exists
            y_label="Asset Valuation",
        )

    def plot_net_worth_history(self) -> go.Figure:
        """
        Plot the net worth history over time, split between cash in hand and asset valuation.

        :return: The Plotly figure.
        """
        # Create a DataFrame with both cash in hand and asset valuation history
        net_worth_df = pd.DataFrame(
            {
                "date": pd.date_range(
                    start=self.simulation.start_date,
                    end=self.simulation.end_date,
                    periods=len(self.simulation.cash_in_hand_history),
                ),
                "cash_in_hand": self.simulation.cash_in_hand_history,
                "asset_valuation": self.simulation.asset_valuation_history,
                # Assuming this exists
            }
        )

        # Calculate the net worth by summing cash and asset valuation
        net_worth_df["net_worth"] = (
            net_worth_df["cash_in_hand"] + net_worth_df["asset_valuation"]
        )

        # Create the figure
        fig = go.Figure()

        # Add a trace for the cash in hand
        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["cash_in_hand"],
                mode="lines",
                name="Cash in Hand",
                line=dict(color="blue"),
                stackgroup="one",  # Stacking enabled
            )
        )

        # Add a trace for the asset valuation
        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["asset_valuation"],
                mode="lines",
                name="Asset Valuation",
                line=dict(color="green"),
                stackgroup="one",  # Stacking enabled
            )
        )

        # Add a trace for the total net worth (optional, as the stacking already shows this)
        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["net_worth"],
                mode="lines",
                name="Total Net Worth",
                line=dict(color="black", dash="dash"),
            )
        )

        # Update layout
        fig.update_layout(
            title="Net Worth History Over Time",
            xaxis_title="Date",
            yaxis_title="Net Worth",
            template="plotly_white",
            xaxis=dict(tickformat="%b %Y"),  # Format the x-axis as Month Year
        )

        return fig
