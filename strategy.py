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
        # 获取历史价格数据
        price_data = {}
        for contract in self.contracts:
            df = self.data_fetcher.fetch_historical_data(contract)
            price_data[contract.symbol] = df
        # 合并为 DataFrame
        self.prices = pd.DataFrame(price_data)
        # 计算价格相对变化
        self.price_relatives = self.prices.pct_change().fillna(0) + 1

    def run(self):
        self.initialize_prices()
        T = len(self.price_relatives)
        X = self.price_relatives.values

        for t in range(1, T):
            # 获取历史数据
            X_t = X[:t]
            b_init = self.portfolio_manager.get_latest_weights()
            # 优化投资组合
            b_t = self.optimizer.optimize(X_t, b_init)
            # 更新投资组合权重
            self.portfolio_manager.update_portfolio(b_t)
            # 计算本期财富
            x_t = X[t]
            self.portfolio_manager.update_wealth(b_t, x_t)

        # 可视化结果
        self.plot_results()

    def plot_results(self):
        index = self.price_relatives.index[:len(self.portfolio_manager.wealth)]
        portfolio_df = self.portfolio_manager.get_portfolio_weights_df(index)
        wealth_series = self.portfolio_manager.get_wealth_series(index)

        # 绘制财富曲线
        plt.figure(figsize=(10, 6))
        plt.plot(wealth_series)
        plt.title('Wealth Over Time Using FTL Algorithm')
        plt.xlabel('Date')
        plt.ylabel('Wealth')
        plt.grid(True)
        plt.show()

        # 绘制投资组合权重
        portfolio_df.plot(kind='line', figsize=(10, 6))
        plt.title('Portfolio Weights Over Time')
        plt.xlabel('Date')
        plt.ylabel('Weight')
        plt.legend()
        plt.grid(True)
        plt.show()

    def execute_trades(self):
        # 获取最新价格
        current_prices = self.data_fetcher.get_current_prices(self.contracts)
        current_prices_series = pd.Series(current_prices)

        # 更新价格相对变化
        last_close_prices = self.prices.iloc[-1]
        x_t = (current_prices_series / last_close_prices).values

        # 更新价格数据
        self.prices.loc[pd.Timestamp.now()] = current_prices_series
        self.price_relatives.loc[pd.Timestamp.now()] = x_t

        # 更新 FTL 算法
        X_t = self.price_relatives.values
        b_init = self.portfolio_manager.get_latest_weights()
        b_t = self.optimizer.optimize(X_t, b_init)
        self.portfolio_manager.update_portfolio(b_t)

        # 获取账户信息
        self.ib.reqPositions()
        self.ib.sleep(1)
        positions = {pos.contract.symbol: pos.position for pos in self.ib.positions()}
        account_values = self.ib.accountValues()
        net_liquidation = float([v for v in account_values if v.tag == 'NetLiquidation' and v.currency == 'USD'][0].value)

        # 计算目标持仓并执行交易
        target_positions_value = b_t * net_liquidation
        target_positions_qty = {}
        for symbol, target_value in zip(self.symbols, target_positions_value):
            price = current_prices[symbol]
            qty = int(target_value / price)
            target_positions_qty[symbol] = qty

        self.rebalance_portfolio(target_positions_qty, positions)

    def rebalance_portfolio(self, target_positions_qty, current_positions):
        for contract in self.contracts:
            symbol = contract.symbol
            target_qty = target_positions_qty.get(symbol, 0)
            current_qty = current_positions.get(symbol, 0)
            order_qty = target_qty - current_qty
            if order_qty == 0:
                continue  # 不需要交易
            elif order_qty > 0:
                # 生成买入订单
                order = MarketOrder('BUY', order_qty)
            else:
                # 生成卖出订单
                order = MarketOrder('SELL', -order_qty)
            # 下达订单
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(1)  # 等待订单处理

    def run_live(self, interval=86400):
        while True:
            try:
                self.execute_trades()
                # 等待下一个周期
                time.sleep(interval)
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)  # 出现错误时等待一段时间
