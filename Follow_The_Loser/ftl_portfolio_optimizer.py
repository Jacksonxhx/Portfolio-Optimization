import numpy as np
from scipy.optimize import Bounds, LinearConstraint


class FTLPortfolioOptimizer:
    def __init__(self, symbols, epsilon=0.5):
        self.symbols = symbols
        self.m = len(symbols)
        # mean reversion threshold ε
        self.epsilon = epsilon
        self.bounds = Bounds(0, 1)
        self.linear_constraint = LinearConstraint(np.ones(self.m), 1, 1)
        # initialize portfolio weights equally
        self.b_t = np.ones(self.m) / self.m

    def pamr_update(self, x_t: np.ndarray) -> np.ndarray:
        '''
        Update portfolio weights using the PAMR algorithm

        :param x_t: np.ndarray
        :return: np.ndarray
        '''
        b_t = self.b_t.copy()
        x_bar = np.mean(x_t)
        # loss function max(0,b_t⊤x_t − ϵ)
        loss = max(0, np.dot(b_t, x_t) - self.epsilon)
        if loss == 0:
            # Passive: Keep the current portfolio
            self.b_t = b_t
            return self.b_t
        else:
            # Aggressive: Update the portfolio
            # The squared Euclidean norm of deviations from the mean
            denominator = np.linalg.norm(x_t - x_bar)**2
            if denominator == 0:
                tau = 0
            else:
                # τ_t = ℓ(b_t;x_t)/D_t
                tau = loss / denominator
            # update portfolio weight
            b = b_t - tau * (x_t - x_bar)
            # ensure that the updated weights are valid probabilities
            b = self.simplex_projection(b)
            self.b_t = b
            return self.b_t

    def simplex_projection(self, b: np.ndarray) -> np.ndarray:
        '''
        Projects a point onto the simplex domain.

        :param b: np.ndarray
        :return: np.ndarray
        '''
        # positive
        b = np.maximum(b, 0)
        total = np.sum(b)
        # judge total weight sum
        if total == 0:
            return np.ones(self.m) / self.m
        else:
            return b / total

    def optimize(self, x_t):
        return self.pamr_update(x_t)
