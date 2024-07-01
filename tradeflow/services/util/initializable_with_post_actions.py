import abc


class InitializableWithPostAction:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.is_initialized = False

    # calls initialize_impl if not initialized
    async def initialize(self, *args) -> bool:
        if not self.is_initialized:
            if await self._initialize_impl(*args):
                await self._post_initialize(args)
                self.is_initialized = True
                return True
            return False
        return False

    @abc.abstractmethod
    async def _initialize_impl(self, *args) -> bool:
        raise NotImplementedError("initialize_impl not implemented")

    # Implement _post_initialize if anything specific has to be done after initialize and before start
    async def _post_initialize(self, *args) -> bool:
        return True
