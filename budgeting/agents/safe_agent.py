from budgeting.core import RecurrenceType
from budgeting.simulator import Agent
from budgeting.assets.asset import Asset, BankAccount


class SafeAgent(Agent):
    def __init__(self, minimum_balance: float, minimum_cd_value: float) -> None:
        """
        Initialize the agent.

        :param minimum_balance: The minimum balance the agent must hold in hand.
        :param minimum_cd_value: The minimum credit deposit value that the agent can open.
        """
        self.minimum_cd_value = minimum_cd_value
        self.minimum_balance = minimum_balance

    def decide_sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Sell assets if under the expected minimum.

        :param balance: The cahsh on hand
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

    def decide_buy(
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
            balance - self.minimum_balance > self.minimum_cd_value
            and balance > self.minimum_balance
        ):
            return [
                BankAccount(
                    balance - self.minimum_balance,
                    interest_rate=3.5,
                    recurrence_type=RecurrenceType.MONTHLY,
                    only_on_recurrence=True,
                    minimum_periods=3,
                )
            ]

        return []
