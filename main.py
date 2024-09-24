from ib_insync import Stock

from data_fetcher import DataFetcher
from ib_connector import IBConnection
from portfolio_manager import PortfolioManager
from portfolio_optimizer import PortfolioOptimizer
from strategy import StrategyRunner

'''Credentials'''
symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'META'
]


def main():
    # Initialize the ib connection and get instance
    ib_connection = IBConnection()
    ib_connection.connect()
    ib = ib_connection.get_ib()

    # SmartRouting help you to pick the best exchange
    contracts = [Stock(symbol, 'SMART', 'USD') for symbol in symbols]

    # Initialize the necessary components
    data_fetcher = DataFetcher(ib)
    optimizer = PortfolioOptimizer(symbols)
    portfolio_manager = PortfolioManager(symbols)
    strategy_runner = StrategyRunner(
        ib_connection,
        data_fetcher,
        optimizer,
        portfolio_manager,
        contracts,
        symbols
    )

    # run
    strategy_runner.run()

    # Run daily
    strategy_runner.run_live(interval=86400)

    ib_connection.disconnect()


if __name__ == "__main__":
    main()

