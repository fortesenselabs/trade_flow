import typing
from tradeflow.trading_backend import errors
from tradeflow.trading_backend import enums
from tradeflow.trading_backend import constants
from tradeflow.commons.logging import Logger


class Exchange:
    SPOT_ID = None
    MARGIN_ID = None
    FUTURE_ID = None
    CFD_ID = None
    IS_SPONSORING = False

    def __init__(self, exchange: typing.Callable):
        self._exchange = exchange

        # add backend headers
        self._exchange.connector.add_headers(self.get_headers())

    def stop(self):
        self._exchange = None

    @classmethod
    def get_name(cls):
        return "default"

    @classmethod
    def is_sponsoring(cls) -> bool:
        return cls.IS_SPONSORING

    async def initialize(self) -> str:
        default = f"{self.get_name().capitalize()} backend initialized."
        return (
            f"{default} {await self._ensure_broker_status()}"
            if self.is_sponsoring()
            else default
        )

    async def _ensure_broker_status(self):
        return f"Broker rebate is enabled."

    def get_headers(self) -> dict:
        return {}

    def get_orders_parameters(self, params=None) -> dict:
        if params is None:
            params = {}
        return params

    def _allow_withdrawal_right(self) -> bool:
        return constants.ALLOW_WITHDRAWAL_KEYS

    async def _inner_cancel_order(self):
        # use client api to avoid any ccxt call wrapping and error handling
        await self._exchange.connector.client.cancel_order("12345", symbol="BTC/USDT")

    async def _get_api_key_rights_using_order(self) -> list[enums.APIKeyRights]:
        rights = [enums.APIKeyRights.READING]
        try:
            await self._inner_cancel_order()
        except errors.AuthenticationError as err:
            if "permission" in str(err).lower():
                # does not have trading permission
                pass
            else:
                # another error
                raise
        except errors.ExchangeError as err:
            if not self._exchange.is_api_permission_error(err):
                # has trading permission
                rights.append(enums.APIKeyRights.SPOT_TRADING)
                rights.append(enums.APIKeyRights.MARGIN_TRADING)
                rights.append(enums.APIKeyRights.FUTURES_TRADING)
        return rights

    async def _get_api_key_rights(self) -> list[enums.APIKeyRights]:
        # default implementation: fetch portfolio and don't check
        # todo implementation for each exchange as long as it is not supported in unified api
        await self._exchange.connector.client.fetch_balance()
        return [
            enums.APIKeyRights.READING,
            enums.APIKeyRights.SPOT_TRADING,
            enums.APIKeyRights.FUTURES_TRADING,
            enums.APIKeyRights.MARGIN_TRADING,
        ]

    async def _ensure_api_key_rights(self):
        # raise trading_backend.errors.APIKeyPermissionsError on missing permissions
        rights = []
        try:
            rights = await self._get_api_key_rights()
        except errors.BaseError:
            raise
        except Exception as err:
            try:
                Logger(name=self.__class__.__name__).exception(
                    err,
                    True,
                    f"Error when getting {self.__class__.__name__} api key rights: {err}",
                )
            except ImportError:
                pass
            # non-exchange specific error: proceed to right checks and raise
        required_right = enums.APIKeyRights.SPOT_TRADING
        if self._exchange.exchange_manager.is_future:
            required_right = enums.APIKeyRights.FUTURES_TRADING
        if self._exchange.exchange_manager.is_margin:
            required_right = enums.APIKeyRights.MARGIN_TRADING
        if required_right not in rights:
            raise errors.APIKeyPermissionsError(
                f"{required_right.value} permission is required"
            )
        if (
            not self._allow_withdrawal_right()
            and enums.APIKeyRights.WITHDRAWALS in rights
        ):
            raise errors.APIKeyPermissionsError(
                f"This api key has withdrawal rights, please revoke it."
            )

    async def is_valid_account(self, always_check_key_rights=False) -> (bool, str):
        try:
            # 1. check account
            validity, message = await self._inner_is_valid_account()
            if not always_check_key_rights and not validity:
                return validity, message
            # 2. check api key right
            await self._ensure_api_key_rights()
            return validity, message
        except errors.APIKeyPermissionsError:
            # forward exception
            raise
        except errors.InvalidNonce as err:
            raise errors.TimeSyncError(err)
        except errors.ExchangeError as err:
            raise errors.ExchangeAuthError(err)

    async def _inner_is_valid_account(self) -> (bool, str):
        # check account validity regarding exchange requirements, exchange specific
        return True, None

    def _get_id(self):
        if self._exchange.exchange_manager.is_future:
            return self.FUTURE_ID
        if self._exchange.exchange_manager.is_margin:
            return self.MARGIN_ID
        if self._exchange.exchange_manager.is_spot:
            return self.SPOT_ID
        return self.CFD_ID  # Return CFD_ID for CFD exchanges
