import pprint
import time
import pandas as pd
from ib_insync import MarketOrder
from matplotlib import pyplot as plt


class StrategyRunner:
    def __init__(self, ib_connection, data_fetcher, optimizer, portfolio_manager, contracts, symbols):
        self.ib_connection = ib_connection
        self.ib = ib_connection.get_ib()
        self.data_fetcher = data_fetcher
        self.optimizer = optimizer
        self.portfolio_manager = portfolio_manager
        self.contracts = contracts
        self.symbols = symbols
        self.prices = None
        self.price_relatives = None

    def initialize_prices(self):
        # obtain historical price for each ticker
        price_data = {}
        for contract in self.contracts:
            df = self.data_fetcher.fetch_historical_data(contract)
            price_data[contract.symbol] = df
        # make a historical price dataframe
        self.prices = pd.DataFrame(price_data)
        # calculate the historical price change x_t = P_t/P_(t-1)
        self.price_relatives = self.prices.pct_change().fillna(0) + 1

    def run(self):
        '''
        Implement FTL algorithm b_t = argmax(b∈Δm) ∑(j=1) to (t-1) ln(b⊤x_j)
        '''
        self.initialize_prices()
        # days
        T = len(self.price_relatives)
        # relative prices
        X = self.price_relatives.values

        for t in range(1, T):
            # relative prices from 0 to t - 1
            X_t = X[:t]
            b_init = self.portfolio_manager.get_latest_weights()
            # use previous price to optimize to make sure the b_t is the best option in time t
            b_t = self.optimizer.optimize(X_t, b_init)
            # update weights
            self.portfolio_manager.update_portfolio(b_t)
            # calculate the current wealth use current price at time t and update wealth: S_t = S_(t-1) x b_t⊤x_t
            x_t = X[t]
            self.portfolio_manager.update_wealth(b_t, x_t)

        # plot
        self.plot_results()

    def plot_results(self):
        index = self.price_relatives.index[:len(self.portfolio_manager.wealth)]
        portfolio_df = self.portfolio_manager.get_portfolio_weights_df(index)
        wealth_series = self.portfolio_manager.get_wealth_series(index)

        # plot wealth
        plt.figure(figsize=(10, 6))
        plt.plot(wealth_series)
        plt.title('Wealth Over Time Using FTL Algorithm')
        plt.xlabel('Date')
        plt.ylabel('Wealth')
        plt.grid(True)
        plt.show()

        # plot weights
        portfolio_df.plot(kind='line', figsize=(10, 6))
        plt.title('Portfolio Weights Over Time')
        plt.xlabel('Date')
        plt.ylabel('Weight')
        plt.legend()
        plt.grid(True)
        plt.show()

    def execute_trades(self):
        # obtain the current market price
        current_prices: dict[str, float] = self.data_fetcher.get_current_prices(self.contracts)
        current_prices_series = pd.Series(current_prices)

        # retrieve the current relative price
        last_close_prices = self.prices.iloc[-1]    # price obtain by self.initialize_prices()
        x_t = (current_prices_series / last_close_prices).values

        # update price and relative price dict
        self.prices.loc[pd.Timestamp.now()] = current_prices_series
        self.price_relatives.loc[pd.Timestamp.now()] = x_t

        # update FTL algo with the current data
        X_t = self.price_relatives.values
        b_init = self.portfolio_manager.get_latest_weights()
        b_t = self.optimizer.optimize(X_t, b_init)
        self.portfolio_manager.update_portfolio(b_t)

        # live trading part
        self.ib.reqPositions()
        self.ib.sleep(2)

        # obtain the current positions
        positions = {pos.contract.symbol: pos.position for pos in self.ib.positions()}

        # get net asset
        account_values = self.ib.accountValues()
        net_liquidation = float([v for v in account_values if v.tag == 'NetLiquidation' and v.currency == 'USD'][0].value)

        # live trading
        target_positions_value = b_t * net_liquidation  # get weights for each ticker and we get how much money needed to be spent on each ticker
        target_positions_qty = {}
        for symbol, target_value in zip(self.symbols, target_positions_value):
            price = current_prices[symbol]
            qty = int(target_value / price)
            target_positions_qty[symbol] = qty

        # do re-balancing
        self.rebalance_portfolio(target_positions_qty, positions)

    def rebalance_portfolio(self, target_positions_qty, current_positions):
        for contract in self.contracts:
            symbol = contract.symbol
            target_qty = target_positions_qty.get(symbol, 0)
            current_qty = current_positions.get(symbol, 0)

            # calculate how many needed to be brought
            order_qty = target_qty - current_qty

            if order_qty == 0:
                # no need to trade
                continue
            elif order_qty > 0:
                # buy
                order = MarketOrder('BUY', order_qty)
            else:
                # sell, no short
                sell_qty = min(-order_qty, current_qty)
                if sell_qty > 0:
                    order = MarketOrder('SELL', sell_qty)
                else:
                    continue

            # make the order
            self.ib.placeOrder(contract, order)
            self.ib.sleep(2)

    def run_live(self, interval=86400):
        """
        Run the algorithm in daily
        TODO:
            need to consider when to buy within a day, is it at the end or at the beginning?
            it's possible that the price fluctuation within the day might lead to better
            performance and improve the return rate.

        :param interval: int
        """
        while True:
            try:
                self.execute_trades()
                # wait for a day
                time.sleep(interval)
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)
