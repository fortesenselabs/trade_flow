#  This folder was adapted from OctoBot-Services (github.com/Drakkar-Software/OctoBot-Services)

"""
This module for everything related to interfaces: graphic (web) and text(telegram), 
notifications push and social analysis data management: update engine to handle new data from an external feed (ex: reddit) when it gets available.
"""

from tradeflow.services import service_factory
from tradeflow.services import abstract_service

from tradeflow.services.service_factory import (
    ServiceFactory,
)
from tradeflow.services.abstract_service import (
    AbstractService,
)

__all__ = [
    "ServiceFactory",
    "AbstractService",
]
