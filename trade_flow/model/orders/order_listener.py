from abc import ABCMeta


class OrderListener(object, metaclass=ABCMeta):
    """A callback class for an order."""

    def on_execute(self, order: "Order") -> None:
        """Callback for an order after execution.

        Parameters
        ----------
        order : `Order`
            The executed order.
        """
        pass

    def on_cancel(self, order: "Order") -> None:
        """Callback for an order after cancellation.

        Parameters
        ----------
        order : `Order`
            The cancelled order.
        """
        pass

    def on_fill(self, order: "Order", trade: "Trade") -> None:
        """Callback for an order after being filled.

        Parameters
        ----------
        order : `Order`
            The order being filled.
        trade : `Trade`
            The trade that is filling the order.
        """
        pass

    def on_complete(self, order: "Order") -> None:
        """Callback for an order after being completed.

        Parameters
        ----------
        order : `Order`
            The completed order.
        """
        pass
