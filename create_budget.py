"""Streamlit page providing UI for budget creation."""

import datetime
from pprint import pprint

import pandas as pd
import streamlit as st

from budgeting.agents.safe_agent import (
    ConservativeCDBuyStrategy,
    CDFactory,
    ConservativeSellStrategy,
)
from budgeting.core.transactions import (
    TransactionType,
    RecurrenceType,
    ExpectedTransaction,
)
from budgeting.simulator import Simulation, Agent
from budgeting.visualization import FinancialVisualization


def transaction_component(index: int) -> dict:
    """Reusable function for transaction input."""
    # Retrieve transaction from session state
    transaction = st.session_state.transactions[index]

    with st.expander(f"Transaction {index + 1}"):
        # Text input for category, initial value from session state
        transaction.category = st.text_input(
            f"Category {index + 1}",
            value=transaction.category,
            key=f"category_{index}",
        )

        # Date input for initial and final date
        transaction.initial_date = st.date_input(
            f"Initial Date {index + 1}",
            value=transaction.initial_date,
            key=f"initial_date_{index}",
        )

        transaction.final_date = st.date_input(
            f"Final Date {index + 1}",
            value=transaction.final_date,
            key=f"final_date_{index}",
        )

        # Dropdowns for transaction type and recurrence
        transaction.transaction_type = st.selectbox(
            f"Transaction Type {index + 1}",
            list(TransactionType),
            index=list(TransactionType).index(transaction.transaction_type),
            key=f"type_{index}",
        )

        transaction.recurrence = st.selectbox(
            f"Recurrence {index + 1}",
            list(RecurrenceType),
            index=list(RecurrenceType).index(transaction.recurrence),
            key=f"recurrence_{index}",
        )

        # Number inputs for recurrence value and value
        transaction.recurrence_value = st.number_input(
            f"Recurrence Value {index + 1}",
            min_value=1,
            value=transaction.recurrence_value,
            key=f"recurrence_value_{index}",
        )

        transaction.value = st.number_input(
            f"Value {index + 1}",
            min_value=0.0,
            value=transaction.value,
            key=f"value_{index}",
        )
        
        if (err := transaction.validate()) is not None:
            st.error(f"Error in Transaction {index + 1}: {err}")
            st.session_state.continue_simulation = False

        if st.button(f"Delete Transaction {index + 1}", key=f"delete_{index}"):
            del st.session_state.transactions[index]
            st.rerun()

        return transaction


@st.cache_data
def run_simulation(
    expected_transactions: list[ExpectedTransaction],
    start_date: datetime.date,
    end_date: datetime.date,
    initial_balance: float,
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
            ConservativeCDBuyStrategy(
                30_000,
                25_000,
                cd_factory=CDFactory(
                    cd_args={
                        "interest_rate": 3.5,
                        "recurrence_type": RecurrenceType.MONTHLY,
                        "minimum_periods": 1,
                        "only_on_recurrence": True,
                    }
                ),
            ),
            ConservativeSellStrategy(10_000),
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

# Main app
st.title("Budget Creator")


cols = st.columns([1, 2])

if "transactions" not in st.session_state:
    st.session_state.transactions = []
    
    
if 'processed_file' not in st.session_state:
    st.session_state.processed_file = None

print("New script run")
pprint(st.session_state.transactions)


with cols[0]:
    # Display existing transactions
    subcol = st.columns(2)
    with subcol[0]:
        st.write("### Expected Transactions")

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
                value=0.0
            )
        )
        st.rerun()

    session_transactions = st.session_state.transactions

    with subcol[1]:
        if st.session_state.processed_file is None:
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
            if uploaded_file:
                transactions = ExpectedTransaction.df2transactions(
                    pd.read_csv(uploaded_file))
                st.success(f"Successfully imported {len(transactions)} transactions.")
                st.session_state.transactions.extend(transactions)
                st.session_state.processed_file = True
                st.rerun()
        elif st.button("Upload a New File"):
            st.session_state.processed_file = None
            st.rerun()
            
        st.download_button(
            "Download Transactions",
            data=ExpectedTransaction.transactions2df(
                session_transactions
            ).to_csv(index=False),
            file_name="expected_transactions.csv",
            mime="text/csv",
        )
        
        
            

# If an error is present in the input the simulation must NOT run.
if not st.session_state.continue_simulation:
    st.stop()

simulation = run_simulation(
    session_transactions,
    start_date,
    end_date,
    initial_balance,
)
analyzer = FinancialVisualization(simulation)


with cols[1]:
    st.plotly_chart(analyzer.plot_monthly_cashflow())
    st.plotly_chart(analyzer.plot_monthly_expenses_breakdown())
    st.plotly_chart(analyzer.plot_cash_in_hand_history())
    st.plotly_chart(analyzer.plot_asset_valuation_history())
    st.plotly_chart(analyzer.plot_net_worth_history())
