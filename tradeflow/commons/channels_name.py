import enum


class TradeFlowChannelsName(enum.Enum):
    """
    Evaluators channel names
    """

    TRADEFLOW_CHANNEL = "TradeFlow"


class TradeFlowUserChannelsName(enum.Enum):
    """
    Backtesting channel names
    """

    USER_COMMANDS_CHANNEL = "UserCommands"


class TradeFlowEvaluatorsChannelsName(enum.Enum):
    """
    -Evaluators channel names
    """

    MATRIX_CHANNEL = "Matrix"
    EVALUATORS_CHANNEL = "Evaluators"


class TradeFlowTradingChannelsName(enum.Enum):
    """
    Trading channel names
    """

    OHLCV_CHANNEL = "OHLCV"
    TICKER_CHANNEL = "Ticker"
    MINI_TICKER_CHANNEL = "MiniTicker"
    RECENT_TRADES_CHANNEL = "RecentTrade"
    ORDER_BOOK_CHANNEL = "OrderBook"
    ORDER_BOOK_TICKER_CHANNEL = "OrderBookTicker"
    KLINE_CHANNEL = "Kline"
    TRADES_CHANNEL = "Trades"
    LIQUIDATIONS_CHANNEL = "Liquidations"
    ORDERS_CHANNEL = "Orders"
    BALANCE_CHANNEL = "Balance"
    BALANCE_PROFITABILITY_CHANNEL = "BalanceProfitability"
    POSITIONS_CHANNEL = "Positions"
    MODE_CHANNEL = "Mode"
    MARK_PRICE_CHANNEL = "MarkPrice"
    FUNDING_CHANNEL = "Funding"
