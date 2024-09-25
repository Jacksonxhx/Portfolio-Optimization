from typing import List, Union

import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint

'''
This class is aiming at optimize the FTL algorithm
'''


class PortfolioOptimizer:
    def __init__(self, symbols: List[str]):
        """
        Initialize a optimizer

        :param symbols: List[str]
        """
        self.symbols = symbols
        self.m = len(symbols)
        # limiting b_i within [0, 1]
        self.bounds = Bounds(0, 1)
        # make sure the sum of b_i == 1
        self.linear_constraint = LinearConstraint(np.ones(self.m), 1, 1)

    def ftl_objective(self, b: np.ndarray, X: np.ndarray):
        """
        Calculate the log sum BCRP

        :param b: np.ndarray
        :param X: np.ndarray
        :return: Union[float, np.inf]
        """
        # check the sum  of b_i == 1 and the weights b_i > 0
        if np.any(b < 0) or np.abs(np.sum(b) - 1) > 1e-6:
            return np.inf

        # calculate the log return log_returns == [ln(b⊤x_1, ln(b⊤x_2)...]
        log_returns = np.log(np.dot(X, b))

        if np.any(np.isinf(log_returns)) or np.any(np.isnan(log_returns)):
            return np.inf

        # return the min to realize max the log return
        return -np.sum(log_returns)

    def optimize(self, X_t: np.ndarray, b_init: np.ndarray) -> np.ndarray:
        '''
        Optimizes the portfolio weights given historical data and initial weights

        :param X_t: np.ndarray
        :param b_init: np.ndarray
        :return: np.ndarray
        '''
        res = minimize(
            self.ftl_objective,
            b_init,
            args=(X_t,),
            # suitable for the one with limits
            method='SLSQP',
            bounds=self.bounds,
            constraints=[self.linear_constraint],
            # tolerance
            options={'ftol': 1e-9, 'disp': False}
        )
        if res.success:
            b_t = res.x
            # ensure the weights sum to 1
            b_t /= np.sum(b_t)
            return b_t
        else:
            print("Optimization failed. Using previous weights.")
            return b_init



