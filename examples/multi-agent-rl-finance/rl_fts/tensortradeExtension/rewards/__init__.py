from .proportional_short_net_worth_change import PSNWC
# from .proportional_reward import NWC
from .proportion_position_based_return import PPBR

from tensortrade.env.default.rewards import TensorTradeRewardScheme, PBR, SimpleProfit

_registry = {
    'simple-profit': SimpleProfit,
    'position-based-return': PBR,
    'proportion-short-networth-change': PSNWC,
    # 'net-worth-change': NWC,
    'proportion-position-based-return': PPBR
}

def get(identifier: str) -> 'TensorTradeRewardScheme':
    """Gets the `RewardScheme` that matches with the identifier.

    Parameters
    ----------
    identifier : str
        The identifier for the `RewardScheme`

    Returns
    -------
    `TensorTradeRewardScheme`
        The reward scheme associated with the `identifier`.

    Raises
    ------
    KeyError:
        Raised if identifier is not associated with any `RewardScheme`
    """
    if identifier not in _registry.keys():
        msg = f"Identifier {identifier} is not associated with any `RewardScheme`."
        raise KeyError(msg)
    return _registry[identifier]
