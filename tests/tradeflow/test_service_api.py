import pytest

from tradeflow.services.api.services import stop_services, get_available_services
from tradeflow.services.api.service_feeds import create_service_feed_factory


@pytest.mark.asyncio
async def test_init_services():
    get_available_services()
    await stop_services()


def test_init_service_feeds():
    factory = create_service_feed_factory({}, None, "")
    factory.get_available_service_feeds(True)
