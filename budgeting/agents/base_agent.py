from ..assets.asset import Asset
from ..simulator import Agent


class BaseAgent(Agent):
    def decide_buy(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[Asset]:
        """
        Buy strategy of not buying assets.

        :param balance:
        :param assets:
        :param simulation_day:
        :return:
        """
        return []

    def decide_sell(
        self, balance: float, assets: list[Asset], simulation_day: int
    ) -> list[bool]:
        """
        Sell strategy of not selling assets.

        :param balance:
        :param assets:
        :param simulation_day:
        :return:
        """
        return [False for _ in range(len(assets))]
