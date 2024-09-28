"""Streamlit page providing UI for budget creation."""

import datetime
from pprint import pprint

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

st.set_page_config(layout="wide")
st.session_state.continue_simulation = True


# Function for creating a reusable transaction input component
def transaction_component(index: int) -> dict:
    """Reusable function for transaction input."""
    # Retrieve transaction from session state
    transaction = st.session_state.transactions[index]

    with st.expander(f"Transaction {index + 1}"):
        # Text input for category, initial value from session state
        transaction["category"] = st.text_input(
            f"Category {index + 1}",
            value=transaction["category"],
            key=f"category_{index}",
        )

        # Date input for initial and final date
        transaction["initial_date"] = st.date_input(
            f"Initial Date {index + 1}",
            value=transaction["initial_date"],
            key=f"initial_date_{index}",
        )

        transaction["final_date"] = st.date_input(
            f"Final Date {index + 1}",
            value=transaction["final_date"],
            key=f"final_date_{index}",
        )

        # Dropdowns for transaction type and recurrence
        transaction["transaction_type"] = st.selectbox(
            f"Transaction Type {index + 1}",
            list(TransactionType),
            index=list(TransactionType).index(transaction["transaction_type"]),
            key=f"type_{index}",
        )

        transaction["recurrence"] = st.selectbox(
            f"Recurrence {index + 1}",
            list(RecurrenceType),
            index=list(RecurrenceType).index(transaction["recurrence"]),
            key=f"recurrence_{index}",
        )

        # Number inputs for recurrence value and value
        transaction["recurrence_value"] = st.number_input(
            f"Recurrence Value {index + 1}",
            min_value=1,
            value=transaction["recurrence_value"],
            key=f"recurrence_value_{index}",
        )

        transaction["value"] = st.number_input(
            f"Value {index + 1}",
            min_value=0.0,
            value=transaction["value"],
            key=f"value_{index}",
        )

        try:
            _ = ExpectedTransaction(
                category=transaction["category"],
                initial_date=transaction["initial_date"],
                final_date=transaction["final_date"],
                transaction_type=transaction["transaction_type"],
                recurrence=transaction["recurrence"],
                recurrence_value=transaction["recurrence_value"],
                value=transaction["value"],
            )
            # Display success message (optional)
            st.success(f"Transaction {index + 1} is valid.")

        except Exception as e:
            # Catch the validation error and display it using Streamlit
            validation_error = str(e)
            st.error(f"Error in Transaction {index + 1}: {validation_error}")
            st.session_state.continue_simulation = False

        # Return updated transaction data
        return transaction


@st.cache_data
def run_simulation(expected_transactions: list[ExpectedTransaction]) -> Simulation:
    """Run the simulation given expected transactions."""
    simulation = Simulation(
        start_date=datetime.date(2024, 10, 1),
        end_date=datetime.date(2025, 10, 1),
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

    start_balance = 150_000
    simulation.simulate(start_balance=start_balance)

    return simulation


# Main app
st.title("Budget Creator")


cols = st.columns([1, 2])

if "transactions" not in st.session_state:
    st.session_state.transactions = []

print("New script run")
pprint(st.session_state.transactions)


with cols[0]:
    # Display existing transactions
    st.write("### Existing Transactions")
    for idx in range(len(st.session_state.transactions)):
        st.session_state.transactions[idx] = transaction_component(idx)

    # Form to add a new transaction
    if st.button("Add Expected Transaction"):
        # Create a new transaction with default values and add it to session state
        st.session_state.transactions.append(
            {
                "category": "New Category",
                "initial_date": datetime.date.today(),
                "final_date": datetime.date.today(),
                "transaction_type": TransactionType.EXPENSE,
                "recurrence": RecurrenceType.MONTHLY,
                "recurrence_value": 1,
                "value": 0.0,
            }
        )
        st.rerun()


# If an error is present in the input the simulation must NOT run.
if not st.session_state.continue_simulation:
    st.stop()

simulation = run_simulation(
    [
        ExpectedTransaction(**information)
        for information in st.session_state.transactions
    ]
)
analyzer = FinancialVisualization(simulation)


with cols[1]:
    st.plotly_chart(analyzer.plot_monthly_cashflow())
    st.plotly_chart(analyzer.plot_monthly_expenses_breakdown())
    st.plotly_chart(analyzer.plot_cash_in_hand_history())
    st.plotly_chart(analyzer.plot_asset_valuation_history())
    st.plotly_chart(analyzer.plot_net_worth_history())
