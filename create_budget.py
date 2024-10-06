"""Streamlit page providing UI for budget creation."""

import datetime
from enum import Enum
from pprint import pprint

import pandas as pd
import streamlit as st

from budgeting.agents.base_agent import NoBuyStrategy, NoSellStrategy
from budgeting.core.transactions import (
    TransactionType,
    RecurrenceType,
    ExpectedTransaction,
)
from budgeting.simulator import Simulation, Agent, BuyStrategy
from budgeting.visualization import FinancialVisualization
from components.strategy_components import get_conservative_cd_buy_strategy

from components.transaction_component import transaction_component


class BuyStrategyEnum(Enum):
    CONSERVATIVE_CD = "Conservative Buy"
    NO_BUY = "No Buy"


class SellStrategyEnum(Enum):
    CONSERVATIVE_CD = "Conservative Sell"
    NO_SELL = "No Sell"


def run_simulation(
    expected_transactions: list[ExpectedTransaction],
    start_date: datetime.date,
    end_date: datetime.date,
    initial_balance: float,
    buy_strategy: BuyStrategy,
) -> Simulation:
    """
    Run the simulation given expected transactions.

    :param expected_transactions: Expected transactions.
    :param start_date: Start date of simulation.
    :param end_date: End date of simulation.
    :param initial_balance: The balance of the start.
    :return:
    """
    simulation = Simulation(
        start_date=start_date,
        end_date=end_date,
        expected_transactions=expected_transactions,
        agent=Agent(
            buy_strategy,
            NoSellStrategy(),
        ),
    )
    simulation.simulate(start_balance=initial_balance)

    return simulation


st.set_page_config(layout="wide")
st.session_state.continue_simulation = True

st.sidebar.header("Simulation Configuration")
start_date = st.sidebar.date_input("Start Date", datetime.date(2024, 10, 1))
end_date = st.sidebar.date_input("End Date", datetime.date(2025, 10, 1))
initial_balance = st.sidebar.number_input("Initial Balance", min_value=0, value=150_000)

# Buy strategy
st.sidebar.subheader("Buy Strategy Configuration")
buy_strategy_option = st.sidebar.selectbox(
    "Select Buy Strategy", [strategy.value for strategy in BuyStrategyEnum]
)

if buy_strategy_option == BuyStrategyEnum.CONSERVATIVE_CD.value:
    buy_strategy = get_conservative_cd_buy_strategy()
elif buy_strategy_option == BuyStrategyEnum.NO_BUY.value:
    buy_strategy = NoBuyStrategy()
else:
    st.error("A buy strategy must be selected")


# Main app
st.title("Budget Creator")

st.write(
    """
    Welcome to the Budget Creator! Use this tool to define your expected financial transactions,
    simulate your financial future, and visualize the outcomes. You can start by adding transactions below
    or uploading a CSV file with your expected transactions. Once your data is input, you can run the simulation
    to view your projected finances.
    """
)

cols = st.columns([1, 2])

if "transactions" not in st.session_state:
    st.session_state.transactions = []


if "processed_file" not in st.session_state:
    st.session_state.processed_file = None

print("New script run")
pprint(st.session_state.transactions)


with cols[0]:
    # Display existing transactions
    st.write(
        """
        ### Expected Transactions
        Below are the financial transactions that you expect to occur during the simulation period.
        You can add new transactions, edit existing ones, or upload a file to bulk import transactions.
        """
    )
    for idx in range(len(st.session_state.transactions)):
        st.session_state.transactions[idx] = transaction_component(idx)

    # Form to add a new transaction

    if st.button("Add Expected Transaction"):
        # Create a new transaction with default values and add it to session state
        st.session_state.transactions.append(
            ExpectedTransaction(
                category="New Category",
                initial_date=datetime.date.today(),
                final_date=datetime.date.today(),
                transaction_type=TransactionType.EXPENSE,
                recurrence=RecurrenceType.MONTHLY,
                recurrence_value=1,
                value=0.0,
            )
        )
        st.rerun()

    st.download_button(
        "Download Transactions",
        data=ExpectedTransaction.transactions2df(st.session_state.transactions).to_csv(
            index=False
        ),
        file_name="expected_transactions.csv",
        mime="text/csv",
    )

    if st.session_state.processed_file is None:
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            transactions = ExpectedTransaction.df2transactions(
                pd.read_csv(uploaded_file)
            )
            st.success(f"Successfully imported {len(transactions)} transactions.")
            st.session_state.transactions.extend(transactions)
            st.session_state.processed_file = True
            st.rerun()
    elif st.button("Upload a New File"):
        st.session_state.processed_file = None
        st.rerun()


# If an error is present in the input the simulation must NOT run.
if not st.session_state.continue_simulation:
    st.stop()

simulation = run_simulation(
    st.session_state.transactions, start_date, end_date, initial_balance, buy_strategy
)

baseline = run_simulation(
st.session_state.transactions, start_date, end_date, initial_balance, NoBuyStrategy()
)




analyzer = FinancialVisualization(simulation)


with cols[1]:
    st.write(
        """
        ### Simulation Results
        Below is the summary of your projected finances based on the expected transactions you've inputted.
        This includes the total income, total expenses, and net cash flow over the simulation period.
        """
    )

    simulation_summary = simulation.summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Income", value=f"{simulation_summary['total_income']:,.2f}"
        )

    with col2:
        st.metric(
            label="Total Expenses",
            value=f"{simulation_summary['total_expenses']:,.2f}",
        )

    with col3:
        st.metric(
            label="Net Cash Flow", value=f"{simulation_summary['net_cash_flow']:,.2f}"
        )

    st.plotly_chart(analyzer.plot_monthly_cashflow())
    st.plotly_chart(analyzer.plot_monthly_expenses_breakdown())
    st.plotly_chart(analyzer.plot_cash_in_hand_history())
    st.plotly_chart(analyzer.plot_asset_valuation_history())
    st.plotly_chart(analyzer.plot_net_worth_history())


with cols[0]:
    monthly_summary = simulation.monthly_summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Average Monthly Expenditure",
            value=f"{monthly_summary['average_monthly_expenditure']:,.2f}",
        )

    with col2:
        st.metric(
            label="Max Monthly Expenditure",
            value=f"{monthly_summary['max_monthly_expenditure']:,.2f}",
        )

    with col3:
        st.metric(
            label="Average Monthly Cashflow",
            value=f"{monthly_summary['average_monthly_cashflow']:,.2f}",
        )

    st.plotly_chart(analyzer.plot_total_expenses_breakdown())
