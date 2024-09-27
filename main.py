from ib_insync import Stock

from Follow_The_Loser.ftl_portfolio_optimizer import FTLPortfolioOptimizer
from data_fetcher import DataFetcher
from ib_connector import IBConnection
from portfolio_manager import PortfolioManager
from Follow_The_Winner.ftw_portfolio_optimizer import FTWPortfolioOptimizer
from strategy import StrategyRunner

'''Credentials, the market pools'''
symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'META'
]


def winner_main():
    # Initialize the ib connection and get instance
    ib_connection = IBConnection()
    ib_connection.connect()
    ib = ib_connection.get_ib()

    # SmartRouting help you to pick the best exchange
    contracts = [Stock(symbol, 'SMART', 'USD') for symbol in symbols]

    # Initialize the necessary components
    data_fetcher = DataFetcher(ib)
    optimizer = FTWPortfolioOptimizer(symbols)
    portfolio_manager = PortfolioManager(symbols)
    strategy_runner = StrategyRunner(
        ib_connection,
        data_fetcher,
        optimizer,
        portfolio_manager,
        contracts,
        symbols,
        'Follow The Winner'
    )

    # run
    strategy_runner.run_ftw()
    # run daily
    strategy_runner.run_live(interval=86400)

    ib_connection.disconnect()


def loser_main():
    ib_connection = IBConnection()
    ib_connection.connect()
    ib = ib_connection.get_ib()

    contracts = [Stock(symbol, 'SMART', 'USD') for symbol in symbols]

    # Initialize the optimizer with PAMR
    data_fetcher = DataFetcher(ib)
    epsilon = 0.5  # Adjust epsilon as needed
    optimizer = FTLPortfolioOptimizer(symbols, epsilon=epsilon)
    portfolio_manager = PortfolioManager(symbols)
    strategy_runner = StrategyRunner(
        ib_connection,
        data_fetcher,
        optimizer,
        portfolio_manager,
        contracts,
        symbols,
        'Follow The Loser'
    )

    # run
    strategy_runner.run_ftl()
    # run daily
    strategy_runner.run_live(interval=86400)

    ib_connection.disconnect()


if __name__ == "__main__":
    # follow the winner
    winner_main()
    # follow the loser
    # loser_main()

