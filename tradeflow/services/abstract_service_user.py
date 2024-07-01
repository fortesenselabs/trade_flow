import abc

import tradeflow.commons.logging as logging
import tradeflow.services.util as util
from tradeflow.services import ServiceFactory


class AbstractServiceUser(util.InitializableWithPostAction):
    __metaclass__ = abc.ABCMeta

    # The service required to run this user
    REQUIRED_SERVICES = None

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.paused = False

    async def _initialize_impl(self, backtesting_enabled, edited_config) -> bool:
        # init associated service if not already init
        service_list = ServiceFactory.get_available_services()
        if self.REQUIRED_SERVICES:
            for service in self.REQUIRED_SERVICES:
                if service in service_list:
                    if not await self._create_or_get_service_instance(
                        service, backtesting_enabled, edited_config
                    ):
                        return False
                else:
                    self.get_logger().error(
                        f"Required service {self.REQUIRED_SERVICES} is not an available service"
                    )
            return True
        elif self.REQUIRED_SERVICES is None:
            self.get_logger().error(
                f"Required service is not set, set it at False if no service is required"
            )
        return False

    async def _create_or_get_service_instance(
        self, service, backtesting_enabled, edited_config
    ):
        service_factory = ServiceFactory(self.config)
        created, error_message = await service_factory.create_or_get_service(
            service, backtesting_enabled, edited_config
        )
        if created:
            return True
        else:
            log_func = self.get_logger().debug
            # log error when the issue is not related to configuration
            if service.instance().has_required_configuration():
                log_func = self.get_logger().warning
            log_func(
                f"Impossible to start {self.get_name()}: required service {service.get_name()} "
                f"is not available ({error_message})."
            )
            return False

    def has_required_services_configuration(self):
        return all(
            service.instance().has_required_configuration()
            for service in self.REQUIRED_SERVICES
        )

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def get_logger(cls):
        return logging.Logger(name=cls.get_name())
