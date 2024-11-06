from abc import ABCMeta
from datetime import datetime

from trade_flow.core.identifiers import Identifiable


class Clock(object):
    """A class to track the time for a process.

    Attributes
    ----------
    start : int
        The time of start for the clock.
    step : int
        The time of the process the clock is at currently.

    Methods
    -------
    now(format=None)
        Gets the current time in the provided format.
    increment()
        Increments the clock by specified time increment.
    reset()
        Resets the clock.
    """

    def __init__(self):
        self.start = 0
        self.step = self.start

    def now(self, format: str = None) -> datetime:
        """Gets the current time in the provided format.
        Parameters
        ----------
        format : str or None, optional
            The format to put the current time into.

        Returns
        -------
        datetime
            The current time.
        """
        return datetime.now().strftime(format) if format else datetime.now()

    def increment(self) -> None:
        """Increments the clock by specified time increment."""
        self.step += 1

    def reset(self) -> None:
        """Resets the clock."""
        self.step = self.start


global_clock = Clock()


class TimeIndexed:
    """A class for objects that are indexed by time."""

    _clock = global_clock

    @property
    def clock(self) -> Clock:
        """Gets the clock associated with this object.

        Returns
        -------
        `Clock`
            The clock associated with this object.
        """
        return self._clock

    @clock.setter
    def clock(self, clock: Clock) -> None:
        """Sets the clock associated with this object.

        Parameters
        ----------
        clock : `Clock`
            The clock to be associated with this object.
        """
        self._clock = clock


class TimedIdentifiable(Identifiable, TimeIndexed, metaclass=ABCMeta):
    """A class an identifiable object embedded in a time process.

    Attributes
    ----------
    created_at : `datetime.datetime`
        The time at which this object was created according to its associated
        clock.
    """

    def __init__(self) -> None:
        self.created_at = self._clock.now()

    @property
    def clock(self) -> "Clock":
        """Gets the clock associated with the object.

        Returns
        -------
        `Clock`
            The clock associated with the object.
        """
        return self._clock

    @clock.setter
    def clock(self, clock: "Clock") -> None:
        """Sets the clock associated with this object.

        In addition, the `created_at` attribute is set according to the new clock.

        Parameters
        ----------
        clock : `Clock`
            The clock to be associated with this object.
        """
        self._clock = clock
        self.created_at = self._clock.now()
