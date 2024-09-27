import numpy as np
import pandas as pd

'''
This class is used to manage the portfolio of wealth and return and weights on each position
'''


class PortfolioManager:
    def __init__(self, symbols):
        self.symbols = symbols
        self.m = len(symbols)
        # initialize weights to equal weights of 1/m
        self.portfolio_weights = [np.ones(self.m) / self.m]
        # the total wealth at each time, assume we have 1m
        self.wealth = [1000000.0]

    def update_portfolio(self, b_t: np.ndarray):
        self.portfolio_weights.append(b_t)

    def update_wealth(self, b_t: np.ndarray, x_t: np.ndarray):
        """
        S_t = S_(t-1) x b_t⊤x_t

        :param b_t: np.ndarray
        :param x_t: np.ndarray
        """
        S_t = self.wealth[-1] * np.dot(b_t, x_t)
        self.wealth.append(S_t)

    def get_latest_weights(self):
        return self.portfolio_weights[-1]

    def get_portfolio_weights_df(self, index):
        return pd.DataFrame(self.portfolio_weights, index=index, columns=self.symbols)

    def get_wealth_series(self, index):
        return pd.Series(self.wealth, index=index)
