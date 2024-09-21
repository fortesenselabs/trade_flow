from abc import ABC
from typing import Any

from trade_flow.core import registry
from trade_flow.core.uuid import Identifiable
from trade_flow.core.context import ContextualizedMixin, InitContextMeta


class Component(ABC, ContextualizedMixin, Identifiable, metaclass=InitContextMeta):
    """The main class for setting up components to be used in the `TradingEnv`.

    This class if responsible for providing a common way in which different
    components of the library can be created. Specifically, it enables the
    creation of components from a `TradingContext`. Therefore making the creation
    of complex environments simpler where there are only a few things that
    need to be changed from case to case.

    Attributes
    ----------
    registered_name : str
        The name under which constructor arguments are to be given in a dictionary
        and passed to a `TradingContext`.
    """

    registered_name = None

    def __init_subclass__(cls, **kwargs) -> None:
        """Constructs the concrete subclass of `Component`.

        In constructing the subclass, the concrete subclass is also registered
        into the project level registry.

        Parameters
        ----------
        kwargs : keyword arguments
            The keyword arguments to be provided to the concrete subclass of `Component`
            to create an instance.
        """
        super().__init_subclass__(**kwargs)

        if cls not in registry.registry():
            registry.register(cls, cls.registered_name)

    def default(self, key: str, value: Any, kwargs: dict = None) -> Any:
        """Resolves which defaults value to use for construction.

        A concrete subclass will use this method to resolve which default value
        it should use when creating an instance. The default value should go to
        the value specified for the variable within the `TradingContext`. If that
        one is not provided it will resolve to `value`.

        Parameters
        ----------
        key : str
            The name of the attribute to be resolved for the class.
        value : any
            The `value` the attribute should be set to if not provided in the
            `TradingContext`.
        kwargs : dict, optional
            The dictionary to search through for the value associated with `key`.
        """
        if not kwargs:
            return self.context.get(key, None) or value
        return self.context.get(key, None) or kwargs.get(key, value)


class Observable:
    """An object with some value that can be observed.

    An object to which a `listener` can be attached to and be alerted about on
    an event happening.

    Attributes
    ----------
    listeners : list of listeners
        A list of listeners that the object will alert on events occurring.

    Methods
    -------
    attach(listener)
        Adds a listener to receive alerts.
    detach(listener)
        Removes a listener from receiving alerts.
    """

    def __init__(self):
        self.listeners = []

    def attach(self, listener) -> "Observable":
        """Adds a listener to receive alerts.

        Parameters
        ----------
        listener : a listener object

        Returns
        -------
        `Observable` :
            The observable being called.
        """
        self.listeners += [listener]
        return self

    def detach(self, listener) -> "Observable":
        """Removes a listener from receiving alerts.

        Parameters
        ----------
        listener : a listener object

        Returns
        -------
        `Observable`
            The observable being called.
        """
        self.listeners.remove(listener)
        return self
