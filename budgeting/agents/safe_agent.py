from collections.abc import Callable

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


class CDFactory:
    """A credit deposit factory behaving like a bank."""

    def __init__(self, cd_args: dict) -> None:
        """Credit Deposit Factory."""
        self.cd_args = cd_args

    def __call__(self, value: float) -> BankAccount:
        """
        Return a bank account.

        :param value: The value to open.
        :return:
        """
        return BankAccount(value=value, **self.cd_args)


class ConservativeCDBuyStrategy(BuyStrategy):
    """Conservative Buying strategy."""

    def __init__(
        self,
        minimum_balance: float,
        minimum_investment: float,
        cd_factory: Callable[[float], BankAccount],
    ) -> None:
        """
        Initialize the conservative strategy.

        :param minimum_balance: Minimum balance to maintain.
        :param minimum_investment: Minimum investment required to buy a CD.
        :param cd_factory: A callable that returns a BankAccount (CD) when called with an investment amount.
        """
        self.cd_factory = cd_factory
        self.minimum_investment = minimum_investment
        self.minimum_balance = minimum_balance

    def buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Buy Credit Deposits when having enough money.

        :param balance: The cash in hand.
        :param assets: The assets held.
        :param simulation_day: The day of the simulation.
        :return: The list of Assets bought.
        """
        investable_amount = balance - self.minimum_balance

        if investable_amount >= self.minimum_investment:
            num_parts = investable_amount // self.minimum_investment
            remainder = investable_amount % self.minimum_investment

            # Adjust the last investment to include the remainder
            investments = [self.minimum_investment] * int(num_parts)

            if remainder > 0 and len(investments) > 0:
                investments[-1] += remainder  # Add remainder to the last part
            elif remainder > 0:
                # If there's no parts, invest the full amount as one CD
                investments.append(investable_amount)

            # Create assets using the cd_factory
            return [self.cd_factory(amount) for amount in investments]

        return []
