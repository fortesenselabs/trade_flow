import numpy as np

from trade_flow.stochastic.helpers import ModelParameters, convert_to_prices


def brownian_motion_log_returns(params: "ModelParameters") -> "np.array":
    """Constructs a Wiener process (Brownian Motion).

    Parameters
    ----------
    params : `ModelParameters`
        The parameters for the stochastic model.

    Returns
    -------
    `np.array`
        Brownian motion log returns.

    References
    ----------
    [1] http://en.wikipedia.org/wiki/Wiener_process
    """
    sqrt_delta_sigma = np.sqrt(params.all_delta) * params.all_sigma
    return np.random.normal(loc=0, scale=sqrt_delta_sigma, size=params.all_time)


def brownian_motion_levels(params: "ModelParameters") -> "np.array":
    """Constructs a price sequence whose returns evolve according to brownian
    motion.

    Parameters
    ----------
    params : `ModelParameters`
        The parameters for the stochastic model.

    Returns
    -------
    `np.array`
        A price sequence which follows brownian motion.
    """
    return convert_to_prices(params, brownian_motion_log_returns(params))
