from typing import List

from trade_flow.feed import Stream
from trade_flow.feed.methods import Methods
from trade_flow.feed.mixins import DataTypeMixin


@Stream.register_accessor(name="str")
class StringMethods(Methods): ...


@Stream.register_mixin(dtype="string")
class StringMixin(DataTypeMixin): ...


class String:
    """A class to register accessor and instance methods."""

    @classmethod
    def register(cls, names: List[str]):
        """A function decorator that adds accessor and instance methods for
        specified data type.

        Parameters
        ----------
        names : `List[str]`
            A list of names used to register the function as a method.

        Returns
        -------
        Callable
            A decorated function.
        """

        def wrapper(func):
            StringMethods.register_method(func, names)
            StringMixin.register_method(func, names)
            return func

        return wrapper


from .operations import *
