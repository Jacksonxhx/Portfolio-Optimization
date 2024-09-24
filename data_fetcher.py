import pprint
from typing import List, Dict, Any
import pandas as pd
from ib_insync import util, Stock, IB
from pandas import DataFrame

'''
This class is aiming at collecting previous market data
'''


class DataFetcher:
    def __init__(self, ib):
        self.ib: IB = ib

    def fetch_historical_data(self, contract: Stock, duration: str = '2 Y', bar_size: str = '1 day') -> DataFrame:
        """
        Retrieve corresponding stock ticker close price for different timescale

        :param contract: str
        :param duration: str
        :param bar_size: str
        :return: DataFrame
        """
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='ADJUSTED_LAST',
            useRTH=True,
            formatDate=1)

        df = util.df(bars)
        df.set_index('date', inplace=True)

        # only needs close price
        return df['close']

    def get_current_prices(self, contracts: List[Stock]) -> Dict[str, float]:
        """
        Retrieve the daily close price for each ticker

        :param contracts: List[Stock]
        :return:
        """
        market_data = {}

        for contract in contracts:
            # get real time data for each ticker
            self.ib.reqMktData(contract, '', False, False)

        # wait for data updating
        self.ib.sleep(2)

        for contract in contracts:
            # get ticker and price
            ticker = self.ib.ticker(contract)
            price = ticker.marketPrice()

            # if no price, use the close price
            if pd.isna(price):
                price = ticker.close

            market_data[contract.symbol] = price

            self.ib.cancelMktData(contract)

        return market_data
