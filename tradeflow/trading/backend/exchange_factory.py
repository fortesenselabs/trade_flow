import tradeflow.trading.backend.exchanges as exchanges


def create_exchange_backend(exchange) -> exchanges.Exchange:
    # use ccxt exchange id to find exchanges (ex kucoinfutures: id: kucoinfutures, name: "Kucoin Futures")
    return _get_exchanges().get(
        exchange.connector.client.id.lower(), exchanges.Exchange
    )(exchange)


def is_sponsoring(exchange_name) -> bool:
    return (
        _get_exchanges().get(exchange_name.lower(), exchanges.Exchange).is_sponsoring()
    )


def _get_exchanges() -> dict:
    return {
        exchange.get_name(): exchange
        for exchange in _get_subclasses(exchanges.Exchange)
    }


def _get_subclasses(parent) -> list:
    children = [parent]
    for child in parent.__subclasses__():
        children += _get_subclasses(child)
    return children
