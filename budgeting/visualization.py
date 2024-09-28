"""Module with the visualization classes."""

import pandas as pd
from plotly.graph_objs import Bar, Scatter

from .core.transactions import TransactionType
from .simulator import Simulation, AssetTransactionType
from plotly.graph_objs._figure import Figure
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class FinancialVisualization:
    """Visualiator of a single simulation."""

    def __init__(self, simulation: Simulation) -> None:
        """Initialize the visualizer."""
        self.simulation = simulation

    def plot_monthly_cashflow(self) -> Figure:
        """
        Plot the monthly cashflow.

        :return: The plotly figure.
        """
        # Check if there are any executed transactions
        if not self.simulation.executed_transactions:
            # Return an empty figure with a message when no transactions are available
            fig = Figure()
            fig.update_layout(
                title="Monthly Cash Flow Analysis",
                xaxis_title="Month",
                yaxis_title="Amount",
                annotations=[
                    {
                        "text": "No transactions were executed.",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20},
                    }
                ],
                template="plotly_white",
            )
            return fig
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
        Plot the net worth history over time with buy/sell transactions in a separate aligned graph below.

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
            }
        )

        # Calculate the net worth by summing cash and asset valuation
        net_worth_df["net_worth"] = (
            net_worth_df["cash_in_hand"] + net_worth_df["asset_valuation"]
        )

        # Create a subplot with 2 rows and 1 column, shared x-axis
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],  # Adjust heights to give more space to the top plot
            vertical_spacing=0.1,  # Space between the two plots
            subplot_titles=("Net Worth History", "Buy/Sell Transactions"),
        )

        # Add the net worth history to the first (top) subplot
        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["cash_in_hand"],
                mode="lines",
                name="Cash in Hand",
                line=dict(color="blue"),
                stackgroup="one",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["asset_valuation"],
                mode="lines",
                name="Asset Valuation",
                line=dict(color="green"),
                stackgroup="one",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=net_worth_df["date"],
                y=net_worth_df["net_worth"],
                mode="lines",
                name="Total Net Worth",
                line=dict(color="black", dash="dash"),
            ),
            row=1,
            col=1,
        )

        # Extract buy and sell transactions from the agent's transaction history
        buy_transactions = [
            t
            for t in self.simulation.agent_transactions_history
            if t.transaction_type == AssetTransactionType.BUY
        ]
        sell_transactions = [
            t
            for t in self.simulation.agent_transactions_history
            if t.transaction_type == AssetTransactionType.SELL
        ]

        def add_jitter(transactions, base_y):
            jittered_y = []
            day_transaction_count = {}

            for t in transactions:
                day = t.date
                # Keep track of the number of transactions for each day
                if day in day_transaction_count:
                    day_transaction_count[day] += 1
                else:
                    day_transaction_count[day] = 0
                # Add jitter by adding 0.5 to the y-axis if multiple transactions happen on the same day
                jittered_y.append(base_y + 0.5 * day_transaction_count[day])

            return jittered_y

        # Add buy/sell markers to the second (bottom) subplot
        fig.add_trace(
            go.Scatter(
                x=[t.date for t in buy_transactions],
                y=add_jitter(buy_transactions, 1),  # Jitter for buy markers
                mode="markers",
                name="Buys",
                marker=dict(color="green", symbol="triangle-up", size=10),
                text=[f"Buy: {t.asset_name} for {t.value}" for t in buy_transactions],
                hoverinfo="text",
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=[t.date for t in sell_transactions],
                y=add_jitter(sell_transactions, -1),  # Jitter for sell markers
                mode="markers",
                name="Sells",
                marker=dict(color="red", symbol="triangle-down", size=10),
                text=[f"Sell: {t.asset_name} for {t.value}" for t in sell_transactions],
                hoverinfo="text",
            ),
            row=2,
            col=1,
        )

        # Customize the layout
        fig.update_layout(
            height=600,  # Total height of the figure
            title_text="Net Worth and Buy/Sell Transactions Over Time",
            showlegend=False,  # Hide the legend if not needed
            template="plotly_white",
            xaxis=dict(tickformat="%b %Y"),  # Format the x-axis as Month Year
        )

        # Add y-axis labels to the subplots
        fig.update_yaxes(title_text="Net Worth", row=1, col=1)
        fig.update_yaxes(title_text="Transactions", row=2, col=1)

        # Adjust x-axis tick formatting to match both subplots
        fig.update_xaxes(tickformat="%b %Y", row=1, col=1)
        fig.update_xaxes(tickformat="%b %Y", row=2, col=1)

        return fig
