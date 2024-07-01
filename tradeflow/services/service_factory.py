import tradeflow.commons.logging as logging
import tradeflow.services.constants as constants
from tradeflow.services import AbstractService


class ServiceFactory:
    def __init__(self, config):
        self.logger = logging.Logger(name=self.__class__.__name__)
        self.config = config

    @staticmethod
    def get_available_services() -> list:
        return [service_class for service_class in AbstractService.__subclasses__()]

    async def create_or_get_service(
        self, service_class, backtesting_enabled, edited_config
    ) -> (bool, str):
        """
        create_or_get_service will create a service instance if it doesn't exist, check the existing one otherwise
        :param service_class: the class of the service to create
        :return: True if the created service is working properly, False otherwise
        """
        service_instance = service_class.instance()
        if service_instance.get_has_been_created():
            return (
                service_instance.is_healthy(),
                service_instance.creation_error_message,
            )
        else:
            return (
                await self._create_service(
                    service_instance, backtesting_enabled, edited_config
                ),
                service_instance.creation_error_message,
            )

    async def _create_service(
        self, service, backtesting_enabled, edited_config
    ) -> bool:
        service.is_backtesting_enabled = backtesting_enabled
        service.set_has_been_created(True)
        service.logger = logging.Logger(name=service.get_name())
        service.config = self.config
        service.edited_config = edited_config
        if service.has_required_configuration():
            return await self._perform_checkup(service)
        else:
            if service.get_should_warn():
                service.creation_error_message = f"Invalid configuration, visit {service.get_help_page()} for more details."
                self.logger.info(
                    f"{service.get_name()} can't be initialized: {service.creation_error_message}"
                )
        return False

    async def _perform_checkup(self, service) -> bool:
        try:
            await service.prepare()
            if self.config:
                if constants.CONFIG_CATEGORY_SERVICES not in self.config:
                    self.config[constants.CONFIG_CATEGORY_SERVICES] = {}
                if (
                    service.get_type()
                    not in self.config[constants.CONFIG_CATEGORY_SERVICES]
                ):
                    self.config[constants.CONFIG_CATEGORY_SERVICES][
                        service.get_type()
                    ] = {}
                self.config[constants.CONFIG_CATEGORY_SERVICES][service.get_type()][
                    constants.CONFIG_SERVICE_INSTANCE
                ] = service
            if await service.say_hello():
                return service.is_healthy()
            else:
                self.logger.warning(f"{service.get_name()} initial checkup failed.")
        except Exception as e:
            self.logger.exception(
                e,
                True,
                f"{service.get_name()} preparation produced the following error: {e}",
            )
        return False

    @staticmethod
    def has_already_been_created(service_class):
        return service_class.instance().get_has_been_created()
