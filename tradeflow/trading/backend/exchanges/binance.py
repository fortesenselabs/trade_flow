import ccxt
import aiohttp.streams

import tradeflow.trading.backend.exchanges as exchanges
from tradeflow.trading.backend import enums


class Binance(exchanges.Exchange):
    LEGACY_SPOT_ID = "T9698EB7"
    SPOT_ID = "HR452G85"
    MARGIN_ID = None
    LEGACY_FUTURE_ID = "uquVg2pc"
    FUTURE_ID = "uquVg2pc"
    LEGACY_REF_ID = "135007948"
    REF_ID = "528112221"
    IS_SPONSORING = True

    @classmethod
    def get_name(cls):
        return "binance"

    def _get_order_custom_id(self):
        return f"x-{self._get_id()}{self._exchange.connector.client.uuid22()}"

    @classmethod
    def use_legacy_ids(cls):
        cls.SPOT_ID = cls.LEGACY_SPOT_ID
        cls.FUTURE_ID = cls.LEGACY_FUTURE_ID

    def _get_broker_dict(self, current_broker_params):
        current_broker_params.update(
            {
                "spot": f"x-{self.__class__.SPOT_ID}",
                "swap": f"x-{self.__class__.FUTURE_ID}",  # used in stop orders
                "future": f"x-{self.__class__.FUTURE_ID}",
            }
        )
        return current_broker_params

    def get_orders_parameters(self, params=None) -> dict:
        current_broker_params = self._exchange.connector.client.options.get(
            "broker", {}
        )
        if current_broker_params != self._get_broker_dict(current_broker_params):
            self._exchange.connector.client.options["broker"] = self._get_broker_dict(
                current_broker_params
            )
        return super().get_orders_parameters(params)

    async def _ensure_broker_status(self):
        try:
            details = await self._get_account_referral_details()
            if not details.get("rebateWorking", False):
                if (
                    ref_id := details.get("referrerId", None)
                ) and ref_id == self.LEGACY_REF_ID:
                    self.use_legacy_ids()
                    details = await self._get_account_referral_details()
                    if details.get("rebateWorking", False):
                        return "Using legacy broker id"
                return f"Broker rebate not working: {details}"
            return f"Broker rebate is enabled."
        except Exception as err:
            return f"Broker rebate check error: {err}"

    async def _get_account_referral_details(self) -> dict:
        return await self._exchange.connector.client.sapi_get_apireferral_ifnewuser(
            params={"apiAgentCode": self._get_id()}
        )

    async def _get_api_key_rights(self) -> list[enums.APIKeyRights]:
        try:
            restrictions = (
                await self._exchange.connector.client.sapi_get_account_apirestrictions()
            )
        except ValueError as err:
            raise ccxt.AuthenticationError(f"Invalid key format ({err})")
        rights = []
        if restrictions.get("enableReading"):
            rights.append(enums.APIKeyRights.READING)
        if restrictions.get("enableSpotAndMarginTrading"):
            rights.append(enums.APIKeyRights.SPOT_TRADING)
            rights.append(enums.APIKeyRights.MARGIN_TRADING)
            rights.append(enums.APIKeyRights.FUTURES_TRADING)
        if restrictions.get("enableWithdrawals"):
            rights.append(enums.APIKeyRights.WITHDRAWALS)
        return rights

    async def _inner_is_valid_account(self) -> (bool, str):
        details = None
        try:
            details = await self._get_account_referral_details()
            if not details.get("rebateWorking", False):
                ref_id = details.get("referrerId", None)
                if ref_id is not None:
                    return (
                        False,
                        f"This account has a referral id equal to {ref_id} "
                        f"which is incompatible ({self.REF_ID} as referral id or no referral id is required)",
                    )
                return (
                    False,
                    f"This account is incompatible, details: {details}. Please report this message to "
                    f"admins for investigation. "
                    f"An account with {self.REF_ID} as referral id or no referral id is required.",
                )
            if not details.get("ifNewUser", False):
                return (
                    False,
                    "Binance requires accounts that were created after july 1st 2021, "
                    "this account is too old.",
                )
        except AttributeError:
            if isinstance(details, aiohttp.streams.StreamReader):
                return False, "Error when fetching exchange data (unreadable response)"
            return False, "Invalid request parameters"
        return True, None
