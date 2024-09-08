from .buy_sell_hold import BSH
from .proportion_buy_hold_sell import PBSH
from .buy_sell_short_hold import BSSH
from .short_hold import SH
from .proportion_short_hold import PSH
from .proportion_buy_sell_short_hold import PBSSH

from tensortrade.env.generic import ActionScheme

_registry = {
    'buy-sell-hold': BSH,
    'proportion-buy-hold-sell': PBSH,
    'buy-sell-short-hold': BSSH,
    'short-hold': SH,
    'proportion-short-hold': PSH,
    'proportion-buy-sell-short-hold': PBSSH,
}

def get(identifier: str) -> 'ActionScheme':
    """Gets the `ActionScheme` that matches with the identifier.

    Parameters
    ----------
    identifier : str
        The identifier for the `ActionScheme`.

    Returns
    -------
    'ActionScheme'
        The action scheme associated with the `identifier`.

    Raises
    ------
    KeyError:
        Raised if the `identifier` is not associated with any `ActionScheme`.
    """
    if identifier not in _registry.keys():
        raise KeyError(f"Identifier {identifier} is not associated with any `ActionScheme`.")
    return _registry[identifier]
