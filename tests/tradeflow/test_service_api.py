import pytest

from trade_flow.services.api.services import stop_services, get_available_services
from trade_flow.services.api.service_feeds import create_service_feed_factory


@pytest.mark.asyncio
async def test_init_services():
    get_available_services()
    await stop_services()


def test_init_service_feeds():
    factory = create_service_feed_factory({}, None, "")
    factory.get_available_service_feeds(True)
