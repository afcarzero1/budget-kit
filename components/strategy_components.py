import streamlit as st

from budgeting.agents.safe_agent import ConservativeCDBuyStrategy
from budgeting.assets.asset import BankAccount
from budgeting.core import RecurrenceType


def get_conservative_cd_buy_strategy() -> ConservativeCDBuyStrategy:
    """Create a ConservativeCDBuyStrategy."""
    st.sidebar.markdown("#### Conservative Buy Strategy Parameters")
    minimum_balance = st.sidebar.number_input(
        "Minimum Cash on Hand",
        min_value=0.0,
        value=10_000.0,
        help="The minimum cash-on-hand required before buying a fixed deposit (CD).",
    )
    minimum_investment = st.sidebar.number_input(
        "Minimum Investment",
        min_value=0.0,
        value=5_000.0,
        help="The minimum amount required to invest in a fixed deposit (CD).",
    )

    # Parameters for BankAccount (CD) instantiation
    interest_rate = st.sidebar.number_input(
        "Interest Rate (%)",
        min_value=0.0,
        value=1.5,
        help="The annual interest rate for the fixed deposit (CD).",
    )
    recurrence_type = st.sidebar.selectbox(
        "Recurrence Type",
        [RecurrenceType.MONTHLY.value, RecurrenceType.WEEKLY.value],
        help="The compounding frequency of interest.",
    )
    minimum_periods = st.sidebar.number_input(
        "Minimum Periods",
        min_value=1,
        value=12,
        help="The minimum number of periods that the investment is locked for.",
    )

    def cd_factory(investment_amount: float) -> BankAccount:
        recurrence_type_enum = RecurrenceType[recurrence_type.upper()]
        return BankAccount(
            value=investment_amount,
            interest_rate=interest_rate,
            recurrence_type=recurrence_type_enum,
            minimum_periods=minimum_periods,
            only_on_recurrence=True,
        )

    return ConservativeCDBuyStrategy(
        minimum_balance=minimum_balance,
        minimum_investment=minimum_investment,
        cd_factory=cd_factory,
    )
