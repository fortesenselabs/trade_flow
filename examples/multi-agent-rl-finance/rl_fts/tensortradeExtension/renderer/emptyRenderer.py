from tensortrade.env.generic import Renderer

class EmptyRenderer(Renderer):
    """A renderer that does renders nothing.

    Needed to make sure that environment can function without requiring a
    renderer.
    """

    def render(self, env, **kwargs):
        pass

    def close(self, _):
        pass