from budgeting.core.transactions import (
    TransactionType,
    RecurrenceType,
    ExpectedTransaction,
)

import streamlit as st


def transaction_component(index: int) -> ExpectedTransaction:
    """Reusable function for transaction input."""
    # Retrieve transaction from session state
    transaction = st.session_state.transactions[index]

    with st.expander(f"Transaction {transaction.category}"):
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
