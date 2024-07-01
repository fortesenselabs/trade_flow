#  This file was adapted from OctoBot (https://github.com/Drakkar-Software/OctoBot)
"""
This module is used by TradeFlow as a base framework for every data transfer within the bot. 
This allows a highly optimized and scalable architecture that adapts to any system while using a very low amount of CPU and RAM.
"""

from tradeflow.channels import tradeflow_channel
from tradeflow.channels.tradeflow_channel import (
    TradeFlowChannelConsumer,
    TradeFlowChannelProducer,
    TradeFlowChannel,
)

__all__ = [
    "TradeFlowChannelConsumer",
    "TradeFlowChannelProducer",
    "TradeFlowChannel",
]
