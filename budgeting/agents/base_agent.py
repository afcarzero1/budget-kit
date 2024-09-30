from ..assets.asset import Asset
from ..simulator import SellStrategy, BuyStrategy


class NoSellStrategy(SellStrategy):
    """Simple strategy of no selling."""

    def sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Not sell any asset.

        :param balance: Current cash on hand
        :param assets: Current assets.
        :param simulation_day: Current simulation day.
        :return: Selling decisions
        """
        return [False for _ in range(len(assets))]


class NoBuyStrategy(BuyStrategy):
    """Simple strategy of no buying."""

    def buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Not buying any asset.

        :param balance: Current cash on hand
        :param assets: Current assets.
        :param simulation_day: Current simulation day.
        :return: Buying decisions.
        """
        return []
