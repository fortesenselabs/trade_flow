"""
TODO: Map this to the MT5 equivalent 
"""
class AccountSummaryTags:
    AccountType = "AccountType"
    NetLiquidation = "NetLiquidation"
    TotalCashValue = "TotalCashValue"
    SettledCash = "SettledCash"
    AccruedCash = "AccruedCash"
    BuyingPower = "BuyingPower"
    EquityWithLoanValue = "EquityWithLoanValue"
    PreviousDayEquityWithLoanValue = "PreviousDayEquityWithLoanValue"
    GrossPositionValue = "GrossPositionValue"
    ReqTEquity = "ReqTEquity"
    ReqTMargin = "ReqTMargin"
    SMA = "SMA"
    InitMarginReq = "InitMarginReq"
    MaintMarginReq = "MaintMarginReq"
    AvailableFunds = "AvailableFunds"
    ExcessLiquidity = "ExcessLiquidity"
    Cushion = "Cushion"
    FullInitMarginReq = "FullInitMarginReq"
    FullMaintMarginReq = "FullMaintMarginReq"
    FullAvailableFunds = "FullAvailableFunds"
    FullExcessLiquidity = "FullExcessLiquidity"
    LookAheadNextChange = "LookAheadNextChange"
    LookAheadInitMarginReq = "LookAheadInitMarginReq"
    LookAheadMaintMarginReq = "LookAheadMaintMarginReq"
    LookAheadAvailableFunds = "LookAheadAvailableFunds"
    LookAheadExcessLiquidity = "LookAheadExcessLiquidity"
    HighestSeverity = "HighestSeverity"
    DayTradesRemaining = "DayTradesRemaining"
    Leverage = "Leverage"

    AllTags = ",".join((AccountType, NetLiquidation, TotalCashValue,
        SettledCash, AccruedCash, BuyingPower, EquityWithLoanValue,
        PreviousDayEquityWithLoanValue, GrossPositionValue, ReqTEquity,
        ReqTMargin, SMA, InitMarginReq, MaintMarginReq, AvailableFunds, 
        ExcessLiquidity , Cushion, FullInitMarginReq, FullMaintMarginReq, 
        FullAvailableFunds, FullExcessLiquidity,
        LookAheadNextChange, LookAheadInitMarginReq, LookAheadMaintMarginReq,
        LookAheadAvailableFunds, LookAheadExcessLiquidity, HighestSeverity,
        DayTradesRemaining, Leverage))