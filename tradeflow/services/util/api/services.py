#  Drakkar-Software OctoBot-Services
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import tradeflow.services.managers as managers
import tradeflow.services.services as services
import tradeflow.services.interfaces as interfaces
import tradeflow.services.errors as errors
import tradeflow.commons.asyncio_tools as asyncio_tools


_SERVICE_ASYNC_LOCKS = {}


def _service_async_lock(service_class):
    try:
        return _SERVICE_ASYNC_LOCKS[service_class.__name__]
    except KeyError:
        _SERVICE_ASYNC_LOCKS[service_class.__name__] = asyncio_tools.RLock()
        return _SERVICE_ASYNC_LOCKS[service_class.__name__]


def get_available_services() -> list:
    return services.ServiceFactory.get_available_services()


async def get_service(service_class, is_backtesting, config=None):
    # prevent concurrent access when creating a service
    async with _service_async_lock(service_class):
        created, error_message = await create_service_factory(
            interfaces.get_startup_config(dict_only=True) if config is None else config
        ).create_or_get_service(
            service_class,
            is_backtesting,
            interfaces.get_edited_config(dict_only=True) if config is None else config,
        )
        if created:
            service = service_class.instance()
            if is_backtesting and not service.BACKTESTING_ENABLED:
                raise errors.UnavailableInBacktestingError(
                    f"{service_class.__name__} service is not available in backtesting"
                )
            return service
    raise errors.CreationError(
        f"{service_class.__name__} service is not initialized: {error_message}"
    )


def create_service_factory(config) -> services.ServiceFactory:
    return services.ServiceFactory(config)


async def stop_services() -> None:
    await managers.stop_services()
