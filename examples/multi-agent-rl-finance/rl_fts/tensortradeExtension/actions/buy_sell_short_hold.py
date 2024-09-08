from tensortrade.env.default.actions import TensorTradeActionScheme
from gym.spaces import Discrete
from tensortrade.oms.wallets import Wallet, Portfolio
from tensortrade.oms.instruments import Quantity, ExchangePair, TradingPair
from tensortrade.env.generic import TradingEnv

import logging

from typing import Any

from tensortrade.oms.orders import (
    Order,
    proportion_order,
    TradeSide,
    TradeType
)

class BSSH(TensorTradeActionScheme):
    """
        A simple discrete action scheme where the action options available are to:
            - buy
            - sell
            - short
            - hold

        Parameters
        ----------
        cash : `Wallet`
            The wallet to hold funds in the base intrument.
        asset : `Wallet`
            The wallet to hold funds in the quote instrument.
        margin : `Wallet`
            The wallet to hold funds in the margin account.
        borrow_requirement : `float`
            A limit specifying the amount that the agent can borrow as
            a percentage of the security's purchased price.
        maintenance_margin : `float`
            The percentage of borrowed funds that has to be available in the margin account
        margin_interest : `float`
            The interest applied per time step for this short position
        Dependancies:
            
        Notes:
            we need to update the stopper to stop if 
    """

    registered_name = "bssh"

    def __init__(self,
            cash: 'Wallet',
            asset: 'Wallet',
            profit_wallet: 'Wallet',
            portfolio: 'Portfolio',
            broker_asset: 'Wallet',
            broker_cash: 'Wallet',
            deposit_margin: 'Wallet',
            borrow_requirement: 'float' = 1.5,
            maintenance_margin: 'float' = 0.25,
            margin_interest: 'float' = (0.06/365),
            broker_fee: 'float' = 0.01,
            minimum_short_deposit: 'float' = 1
        ):
        super().__init__()
        # parameters
        self.cash = cash
        self.asset = asset
        self.profit_wallet = profit_wallet
        self.portfolio = portfolio
        self.broker_asset = broker_asset
        self.broker_cash = broker_cash
        self.deposit_margin = deposit_margin
        self.borrow_requirement = borrow_requirement
        self.maintenance_margin = maintenance_margin
        self.margin_interest = margin_interest
        self.minimum_short_deposit = minimum_short_deposit
        self.broker_fee = broker_fee
        # private variables
        self.commission = cash.exchange.options.commission
        self.borrow_quantity: Quantity =  0 * self.asset.instrument
        # flags
        self.complete_exit_order = False
        # track short
        self.short_tracker = None
        # USD-TTC
        traing_pair = TradingPair(self.cash.balance.instrument, self.broker_asset.balance.instrument)
        # sine-wave-USD-TTC
        self.exchange_pair = ExchangePair(self.cash.exchange, traing_pair)

        self.listeners = []
        self.action = -1
        self.currently_in_short = False

    @property
    def action_space(self):
        """
            0 -> Enter buy position (convert all cash to asset)
            1 -> Enter a sell position (convert all asset to cash)
            2 -> Enter short position
            3 -> Exit short position
          Note:
            - If the action is the same as the previous action, we implement a hold.
            - If the action is to enter a short position and the previous position was a buy,
                we first implement a sell order, then enter the short
            - If the action is a sell order and the previous action was to enter a short, 
                we first exit the short, then create a sell order
            - If the action is a sell order and the previous action was to exit the short,
                we do nothing
            - If the action is a buy order and the previous action was to enter a short,
                we first exit the short, then create the buy order
        """
        return Discrete(4)

    def attach(self, listener):
        self.listeners += [listener]
        return self

    def perform(self, env: 'TradingEnv', action: 'Any') -> None:
        """Performs the action on the given environment.

        Under the TT action scheme, the subclassed action scheme is expected
        to provide a method for getting a list of orders to be submitted to
        the broker for execution in the OMS.

        Parameters
        ----------
        env : 'TradingEnv'
            The environment to perform the action on.
        action : Any
            The specific action selected from the action space.
        """
        orders = self.get_orders(action)

        for order in orders:
            if order:
                logging.info('Step {}: {} {}'.format(order.step, order.side, order.quantity))
                self.broker.submit(order)

        self.broker.update()

        # If the last action created an exit order
        if self.complete_exit_order:
            # complete the short transfers
            self.completeShort()

    def get_orders(self, action: int) -> 'Order':
        """Gets the list of orders to be submitted for the given action.

        Parameters
        ----------
        action : Any
            The action to be interpreted.

        Returns
        -------
        List[Order]
            A list of orders to be submitted to the broker.
        """
        order = None

        # only place an order if the action has changed (if the action hasn't changed, then we are holding the position)
        if abs(action - self.action) > 0:
            # buy all
            if action == 0:
                order = self.buyOrder()
            # sell all
            elif action == 1:
                # sell
                order = self.sellOrder()
            # Entering short position
            elif action == 2:
                order = self.enterShort()
            # Exit a short
            elif action == 3 and self.currently_in_short:
                # create a market order to buy back the same quantity of stock with cash (from cash to asset)
                order = self.exitShort()
            self.action = action
        else:
            # if we are currently in a short position
            if self.action == 2:
                order = self.maintainShort()

        return [order]

    def enterShort(self):
        # if the previous position was a buy
        if self.action == 0:
            sell_order = self.sellOrder()
            self.broker.submit(sell_order)
            self.broker.update()
            
        # requirements for entering a short
        if self.cash.balance < self.minimum_short_deposit:
            return None

        # The borrowed asset must be created and placed in the brokers wallet
        borrow_size = self.cash.balance.as_float() / self.borrow_requirement
        borrow_cash = Quantity(self.cash.balance.instrument, borrow_size)
        # remove commision from the borrow quantity (commision charged to the agent)
        borrow_commision = borrow_cash * self.commission
        borrow_cash: Quantity = borrow_cash - borrow_commision
        self.borrow_quantity = borrow_cash.convert(self.exchange_pair)
        # When the agent enters the short position, the borrow limit must be transfered (cash -> deposit_margin)
        self.transfer(
            source=self.cash,
            target=self.deposit_margin,
            quantity=self.cash.balance,
            commission=self.cash.balance * self.commission,
            reason="SHORT - BORROW DEPOSIT"
        )
        # Add the funds to the broker wallet (deposit)
        self.broker_asset.deposit(
            self.borrow_quantity,
            "Adding security to brokers wallet so that it can be \
            transfered to us to sell in a short position"
        )
        # transfer the borrowed funds from the broker (broker_asset -> asset)
        self.transfer(
            source=self.broker_asset,
            target=self.asset,
            quantity=self.borrow_quantity,
            commission=0 * self.commission,
            reason="SHORT - BORROWED ASSET"
        )
        # broker fee for entering short
        self.transfer(
            source=self.deposit_margin,
            target=self.broker_cash,
            quantity=self.deposit_margin.balance * self.broker_fee,
            commission=0,
            reason="SHORT - BROKER FEE"
        )
        # The borrowed asset must be sold (asset -> cash)
        short_enter_order = proportion_order(
            self.portfolio,
            source=self.asset,
            target=self.cash,
            proportion=1
        )
        self.currently_in_short = True
        return short_enter_order

    def exitShort(self):
        short_exit_order = None
        current_asset_quantity = self.cash.balance.convert(self.exchange_pair)
        # we need to check if we have enough cash to cover the borrow quantity
        if  current_asset_quantity > self.borrow_quantity: 
            # our cash is worth more than the origional asset (we've made money)
            # The short must be exited (cash -> asset)
            cash_quantity: Quantity = self.borrow_quantity.convert(self.exchange_pair)
            short_exit_order = Order(
                step=self.portfolio.clock.step,
                side=TradeSide.BUY,
                trade_type=TradeType.MARKET,
                exchange_pair=self.exchange_pair,
                price=self.exchange_pair.price,
                quantity=cash_quantity.quantize(), # borrow_quantity
                portfolio=self.portfolio,
            )
        else:
            # our cash is worth less than the borrowed quantity
            # transfer from deposit margin (deposit_margin -> cash)
            borrow_remainder_cash = (self.borrow_quantity - current_asset_quantity).convert(self.exchange_pair)
            # we need to make sure that the broker gets the exact quantity back that we borrowed,
            # Therefore we need to deduct any commision fees on transfers from the deposit margin
            # add them to the transfer amount
            short_exit_commission = self.borrow_quantity.convert(self.exchange_pair) * self.commission
            # infalte the transfer quantity to accomidate commision on order
            borrow_remainder_cash += short_exit_commission
            # inflate the transfer quantity to accomidate commision on transfer
            borrow_remainder_cash += borrow_remainder_cash * self.commission
            self.transfer(
                source=self.deposit_margin,
                target=self.cash,
                quantity=borrow_remainder_cash,
                commission=borrow_remainder_cash * self.commission,
                reason="SHORT - BORROW REMAINDER"
            )
            # exit the short with our total cash value (cash -> asset)
            short_exit_order = Order(
                step=self.portfolio.clock.step,
                side=TradeSide.BUY,
                trade_type=TradeType.MARKET,
                exchange_pair=self.exchange_pair,
                price=self.exchange_pair.price,
                quantity=self.cash.balance.quantize(),
                portfolio=self.portfolio,
            )
        # complete the exit order wallet transfers after the order is complete
        self.complete_exit_order = True
        self.currently_in_short = False
        return short_exit_order

    def completeShort(self):
        # transfer asset to broker (asset -> broker_asset)
        self.transfer(
            source=self.asset,
            target=self.broker_asset,
            quantity=self.asset.balance,
            commission=0,
            reason="SHORT - RETURN ASSET"
        )
        # broker fee for exiting short
        self.transfer(
            source=self.deposit_margin,
            target=self.broker_cash,
            quantity=self.deposit_margin.balance * self.broker_fee,
            commission=0,
            reason="SHORT - BROKER FEE"
        )
        # claim back deposit (transfer into cash)
        self.transfer(
            source=self.deposit_margin,
            target=self.cash,
            quantity=self.deposit_margin.balance,
            commission=self.deposit_margin.balance * self.commission,
            reason="SHORT - RETURN DEPOSIT"
        )
        # clear the brokers wallet
        self.broker_asset.reset()
        self.borrow_quantity =  0 * self.asset.instrument
        self.complete_exit_order = False

    def maintainShort(self):
        """ 
            A function used to deduct interest from the short, check that the short is still 
            valid and exit the short if the margin balance drops below the maintenance margin
        """
        # cash value of the borrow quantity
        borrow_cash_qauntity = self.borrow_quantity.convert(self.exchange_pair)
        # interest must be deducted from the short value
        interest: Quantity = borrow_cash_qauntity * self.margin_interest
        # if the deposit value is less than maintenance_margin % of the borrowed assets value
        margin_value = self.deposit_margin.total_balance - interest
        # calculate the threshold value which must be maintained
        borrow_threshold_cash = self.maintenance_margin * self.borrow_quantity.convert(self.exchange_pair)
        if margin_value < borrow_threshold_cash:
            return self.exitShort()
        else:
            # deduct interest from margin account
            self.transfer(
                source=self.deposit_margin,
                target=self.broker_cash,
                quantity=interest,
                commission=0,
                reason="SHORT - BORROWED INTEREST"
            )
        return None

    def buyOrder(self):
        """execute a buy order"""
        order = None
        # if we are currently in a short
        if self.currently_in_short:
            # we need to exit the short, then make the buy order
            exit_short_order = self.exitShort()
            self.broker.submit(exit_short_order)
            self.broker.update()
            self.completeShort()
        if self.cash.balance.as_float() > 0:
            # self.borrow_quantity: Quantity =  0 * self.asset.instrument
            order = proportion_order(self.portfolio, self.cash, self.asset, 1.0)
        return order

    def sellOrder(self):
        """execute a sell order"""
        order = None
        # if we are currently in a short
        if self.currently_in_short:
            # we need to exit the short, then make the buy order
            order = self.exitShort()
        elif self.asset.balance.as_float() > 0:
            order = proportion_order(self.portfolio, self.asset, self.cash, 1.0)
        return order

    def transfer(self, 
        source: Wallet, 
        target: Wallet, 
        quantity: Quantity, 
        commission: Quantity, 
        reason: str):
        '''
            A function used to tranfer funds from one wallet to another by calling 
            withdraw and deposit on each.
        '''
        quantity = quantity.quantize()
        if commission:
            # round commision (2 decimal places)
            commission = commission.quantize()
            # withdraw the commision
            source.withdraw(quantity=commission, reason=reason+" COMMISSION")
        # withdraw transfer quantity from source
        source.withdraw(quantity=quantity-commission, reason=reason)
        # deposit transfer qxuantity to target
        target.deposit(quantity=quantity-commission, reason=reason)

    def reset(self):
        super().reset()
        self.cash.reset()
        self.asset.reset()
        self.broker_asset.reset()
        self.broker_cash.reset()
        self.deposit_margin.reset()
        self.borrow_quantity =  0 * self.asset.instrument
        self.action = -1
        self.currently_in_short = False
