from deprecated import deprecated
import multiprocessing as mp

from multiprocessing.queues import Queue


@deprecated(
    version="1.0.4",
    reason="Builtin agents are being deprecated in favor of external implementations (ie: Ray)",
)
class SharedCounter(object):
    """A synchronized shared counter.

    The locking done by multiprocessing.Value ensures that only a single
    process or thread may read or write the in-memory ctypes object. However,
    in order to do n += 1, Python performs a read followed by a write, so a
    second process may read the old value before the new one is written by the
    first process. The solution is to use a multiprocessing.Lock to guarantee
    the atomicity of the modifications to Value.

    Parameters
    ----------
    n : int
        The count to start at.

    References
    ----------
    .. [1] http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/
    """

    def __init__(self, n: int = 0) -> None:
        self.count = mp.Value("i", n)

    def increment(self, n: int = 1) -> None:
        """Increment the counter by n.

        Parameters
        ----------
        n : int
            The amount to increment the counter by.
        """
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self) -> int:
        """The value of the counter. (int, read-only)"""
        return self.count.value


@deprecated(
    version="1.0.4",
    reason="Builtin agents are being deprecated in favor of external implementations (ie: Ray)",
)
class ParallelQueue(Queue):
    """A portable implementation of multiprocessing.Queue.

    Because of multithreading / multiprocessing semantics, Queue.qsize() may
    raise the NotImplementedError exception on Unix platforms like Mac OS X
    where sem_getvalue() is not implemented. This subclass addresses this
    problem by using a synchronized shared counter (initialized to zero) and
    increasing / decreasing its value every time the put() and get() methods
    are called, respectively. This not only prevents NotImplementedError from
    being raised, but also allows us to implement a reliable version of both
    qsize() and empty().
    """

    def __init__(self):
        super().__init__(ctx=mp.get_context())
        self.size = SharedCounter(0)

    def put(self, *args, **kwargs) -> None:
        self.size.increment(1)
        super().put(*args, **kwargs)

    def get(self, *args, **kwargs) -> object:
        self.size.increment(-1)
        return super().get(*args, **kwargs)

    def qsize(self) -> int:
        """Reliable implementation of multiprocessing.Queue.qsize()."""
        return self.size.value

    def empty(self) -> bool:
        """Reliable implementation of multiprocessing.Queue.empty()."""
        return not self.qsize()
