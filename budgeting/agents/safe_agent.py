from budgeting.core import RecurrenceType
from budgeting.simulator import SellStrategy, BuyStrategy
from budgeting.assets.asset import Asset, BankAccount


class ConservativeSellStrategy(SellStrategy):
    """Sell assets to keep a minimum balance."""

    def __init__(self, minimum_balance: float) -> None:
        """
        Initialize the conservative strategy.

        :param minimum_balance: The minimum balance an agent must have.
        """
        self.minimum_balance = minimum_balance

    def sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Sell assets if under the expected minimum.

        :param balance: The cash on hand
        :param assets: The assets.
        :param simulation_day:
        :return:
        """
        target = self.minimum_balance - balance

        if target <= 0:
            # No need to sell any assets
            return [False] * len(assets)

        # Filter and sort assets that are sellable by value in ascending order
        sellable_assets_with_indices = sorted(
            [(idx, asset) for idx, asset in enumerate(assets) if asset.is_sellable()],
            key=lambda x: x[1].value,
        )

        total_value = 0
        selected_indices = []

        # Greedily select sellable assets with the smallest value first
        for idx, asset in sellable_assets_with_indices:
            total_value += asset.value
            selected_indices.append(idx)
            if total_value >= target:
                break

        # If the target is not reachable, sell all sellable assets
        sell_decisions = [False] * len(assets)
        if total_value < target:
            for idx, _ in sellable_assets_with_indices:
                sell_decisions[idx] = True
        else:
            # Mark the selected sellable assets for sale
            for idx in selected_indices:
                sell_decisions[idx] = True

        return sell_decisions


class ConservativeBuyStrategy(BuyStrategy):
    """Conservative Buying strategy."""

    def __init__(self, minimum_balance: float, minimum_investment: float):
        self.minimum_investment = minimum_investment
        self.minimum_balance = minimum_balance

    def buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Buy Credit Deposits when having enough money.

        :param balance: The cash in hand.
        :param assets: The assets hold.
        :param simulation_day: The day of the simulation.
        :return: The list of Assets bought.
        """
        if (
            balance - self.minimum_balance > self.minimum_investment
            and balance > self.minimum_balance
        ):
            return [
                BankAccount(
                    balance - self.minimum_balance,
                    interest_rate=3.5,
                    recurrence_type=RecurrenceType.MONTHLY,
                    only_on_recurrence=False,
                    minimum_periods=3,
                )
            ]

        return []
