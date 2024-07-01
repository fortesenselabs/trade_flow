class ExchangeWatcher:
    """
    ExchangeWatcher is used as a superclass for elements that require to interact with exchanges.
    register_new_exchange_impl(self, exchange_id) will be called whenever a new exchange is ready.
    Registered exchange ids are stored in self.registered_exchanges_ids
    """

    def __init__(self):
        self.registered_exchanges_ids = set()

    async def register_new_exchange(self, exchange_id):
        try:
            await self.register_new_exchange_impl(exchange_id)
        finally:
            self.registered_exchanges_ids.add(exchange_id)

    async def register_new_exchange_impl(self, exchange_id):
        pass
