import pandas as pd
from typing import Dict

import ccxt
from ccxt.base.errors import InsufficientFunds


class Backtester(ccxt.Exchange):
    """
    A backtesting exchange class that inherits from the ccxt.Exchange base class
    and implements the ccxt.Exchange unified API.
    """

    def __init__(self, balances: Dict, fee=0):
        super().__init__()

        self._balances = pd.DataFrame(columns=["asset", "free", "used", "total"])
        self._fee = fee
        self.__init_balances(balances)

    def __init_balances(self, balances: Dict):
        """
        Initialize the balances of the backtesting exchange.

        balances: Dict, example: {"BTC": 1, "ETH": 10}
        """
        if not balances:
            return
        updates = pd.DataFrame(
            [
                {
                    "asset": asset,
                    "free": balance,
                    "used": 0,
                    "total": balance,
                }
                for asset, balance in balances.items()
            ]
        )
        if self._balances.empty:
            self._balances = updates
        else:
            self._balances = pd.concat([self._balances, updates], ignore_index=True)

    def _get_asset_balance(self, asset: str, column: str) -> float:
        """
        Helper method to get the balance of a specific asset by column (eg. free, used)

        :param asset: The asset to query.
        :param column: The column to retrieve ('free' or 'total').
        :return: The balance of the asset in the specified column.
        """
        return self._balances.loc[self._balances["asset"] == asset, column].values[0]

    def _update_asset_balance(self, asset: str, column: str, amount: float):
        """
        Helper method to update the balance of a specific asset and column.

        :param asset: The asset to update.
        :param column: The column to update ('free' or 'total').
        :param amount: The amount to add or subtract.
        """
        self._balances.loc[self._balances["asset"] == asset, column] += amount

    def deposit(self, asset: str, amount: float, id=None):
        """
        Deposit an asset to the backtesting exchange.
        """
        self._update_asset_balance(asset, "free", amount)
        self._update_asset_balance(asset, "total", amount)

    def withdraw(self, asset: str, amount: float, id=None, params={}):
        """
        Withdraw an asset from the backtesting exchange.
        """
        free_balance = self._get_asset_balance(asset, "free")
        if free_balance < amount:
            raise InsufficientFunds(
                f"Insufficient balance. {asset} balance: {free_balance}"
            )

        self._update_asset_balance(asset, "free", -amount)
        self._update_asset_balance(asset, "total", -amount)

    def fetch_balance(self, params={}):
        """
        Fetch the balance of the backtesting exchange.
        """
        return self._balances.set_index("asset").to_dict(orient="index")
