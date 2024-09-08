from abc import ABCMeta, abstractmethod
from typing import List

from trade_flow.core import Component


class Renderer(Component, metaclass=ABCMeta):
    """A component for rendering a view of the environment at each step of
    an episode."""

    registered_name = "renderer"

    @abstractmethod
    def render(self, env: "TradingEnvironment", **kwargs):
        """Renders a view of the environment at the current step of an episode.

        Parameters
        ----------
        env: 'TradingEnv'
            The trading environment.
        kwargs : keyword arguments
            Additional keyword arguments for rendering the environment.
        """
        raise NotImplementedError()

    def save(self) -> None:
        """Saves the rendered view of the environment."""
        pass

    def reset(self) -> None:
        """Resets the renderer."""
        pass

    def close(self) -> None:
        """Closes the renderer."""
        pass


class AggregateRenderer(Renderer):
    """A renderer that aggregates compatible renderers so they can all be used
    to render a view of the environment.

    Parameters
    ----------
    renderers : List[Renderer]
        A list of renderers to aggregate.

    Attributes
    ----------
    renderers : List[Renderer]
        A list of renderers to aggregate.
    """

    def __init__(self, renderers: List[Renderer]) -> None:
        super().__init__()
        self.renderers = renderers

    def render(self, env: "TradingEnvironment", **kwargs) -> None:
        for r in self.renderers:
            r.render(env, **kwargs)

    def save(self) -> None:
        for r in self.renderers:
            r.save()

    def reset(self) -> None:
        for r in self.renderers:
            r.reset()

    def close(self) -> None:
        for r in self.renderers:
            r.close()
