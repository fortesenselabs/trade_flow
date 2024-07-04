from typing import List, Optional
from metatrader.request import RequestBuilder
from metatrader import client


# Data classes for account and snapshot structures
class Account:
    def __init__(
        self,
        name: str,
        uid: int,
        currency: str,
        leverage: int,
        free_margin: float,
        balance: float,
        equity: float,
        can_trade: bool,
        can_withdraw: bool,
        can_deposit: bool,
        update_time: int,
        balances: List["Balance"],
        account_type: str,
        permissions: List[str],
    ):
        self.name = name
        self.uid = uid
        self.currency = currency
        self.leverage = leverage
        self.free_margin = free_margin
        self.balance = balance
        self.equity = equity
        self.can_trade = can_trade
        self.can_withdraw = can_withdraw
        self.can_deposit = can_deposit
        self.update_time = update_time
        self.balances = balances
        self.account_type = account_type
        self.permissions = permissions


class Balance:
    def __init__(self, symbol: str, free: str, locked: str):
        self.symbol = symbol
        self.free = free
        self.locked = locked


class Snapshot:
    def __init__(self, code: int, msg: str, snapshot_vos: List["SnapshotVos"]):
        self.code = code
        self.msg = msg
        self.snapshot_vos = snapshot_vos


class SnapshotVos:
    def __init__(self, data: "SnapshotData", type: str, update_time: int):
        self.data = data
        self.type = type
        self.update_time = update_time


class SnapshotData:
    def __init__(
        self,
        margin_level: str,
        total_asset_of_btc: str,
        total_liability_of_btc: str,
        total_net_asset_of_btc: str,
        balances: List["SnapshotBalances"],
        user_assets: List["SnapshotUserAssets"],
        assets: List["SnapshotAssets"],
        positions: List["SnapshotPositions"],
    ):
        self.margin_level = margin_level
        self.total_asset_of_btc = total_asset_of_btc
        self.total_liability_of_btc = total_liability_of_btc
        self.total_net_asset_of_btc = total_net_asset_of_btc
        self.balances = balances
        self.user_assets = user_assets
        self.assets = assets
        self.positions = positions


class SnapshotBalances:
    def __init__(self, asset: str, free: str, locked: str):
        self.asset = asset
        self.free = free
        self.locked = locked


class SnapshotUserAssets:
    def __init__(
        self,
        asset: str,
        borrowed: str,
        free: str,
        interest: str,
        locked: str,
        net_asset: str,
    ):
        self.asset = asset
        self.borrowed = borrowed
        self.free = free
        self.interest = interest
        self.locked = locked
        self.net_asset = net_asset


class SnapshotAssets:
    def __init__(self, asset: str, margin_balance: str, wallet_balance: str):
        self.asset = asset
        self.margin_balance = margin_balance
        self.wallet_balance = wallet_balance


class SnapshotPositions:
    def __init__(
        self,
        entry_price: str,
        mark_price: str,
        position_amt: str,
        symbol: str,
        unrealized_profit: str,
    ):
        self.entry_price = entry_price
        self.mark_price = mark_price
        self.position_amt = position_amt
        self.symbol = symbol
        self.unrealized_profit = unrealized_profit


class APIKeyPermission:
    def __init__(
        self,
        ip_restrict: bool,
        create_time: int,
        enable_withdrawals: bool,
        enable_internal_transfer: bool,
        permits_universal_transfer: bool,
        enable_vanilla_options: bool,
        enable_reading: bool,
        enable_futures: bool,
        enable_margin: bool,
        enable_spot_and_margin_trading: bool,
        trading_authority_expiration_time: int,
    ):
        self.ip_restrict = ip_restrict
        self.create_time = create_time
        self.enable_withdrawals = enable_withdrawals
        self.enable_internal_transfer = enable_internal_transfer
        self.permits_universal_transfer = permits_universal_transfer
        self.enable_vanilla_options = enable_vanilla_options
        self.enable_reading = enable_reading
        self.enable_futures = enable_futures
        self.enable_margin = enable_margin
        self.enable_spot_and_margin_trading = enable_spot_and_margin_trading
        self.trading_authority_expiration_time = trading_authority_expiration_time


# GetAccountService for getting account info
class GetAccountService:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts: Optional[List[client.Client]] = None) -> Account:
        request = RequestBuilder("GET", "/api/account")
        response = self.client.call_api(request, opts)
        return Account(**response.json())


# GetAccountSnapshotService for getting account snapshots
class GetAccountSnapshotService:
    def __init__(self, client: client.Client):
        self.client = client
        self.account_type = None
        self.start_time = None
        self.end_time = None
        self.limit = None

    def set_type(self, account_type: str):
        self.account_type = account_type
        return self

    def set_start_time(self, start_time: int):
        self.start_time = start_time
        return self

    def set_end_time(self, end_time: int):
        self.end_time = end_time
        return self

    def set_limit(self, limit: int):
        self.limit = limit
        return self

    def do(self, opts: Optional[List[client.Client]] = None) -> Snapshot:
        request = RequestBuilder("GET", "/sapi/v1/accountSnapshot")
        request.set_param("type", self.account_type)
        if self.start_time:
            request.set_param("startTime", str(self.start_time))
        if self.end_time:
            request.set_param("endTime", str(self.end_time))
        if self.limit:
            request.set_param("limit", str(self.limit))

        response = self.client.call_api(request, opts)
        return Snapshot(**response.json())


# GetAPIKeyPermission for getting API key permissions
class GetAPIKeyPermission:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts: Optional[List[client.Client]] = None) -> APIKeyPermission:
        request = RequestBuilder("GET", "/sapi/v1/account/apiRestrictions")
        response = self.client.call_api(request, opts)
        return APIKeyPermission(**response.json())
