"""
Provides a default environment, can also be used as specification for writing custom environments.

Dependencies:
    - Generic Environment
"""



from . import actions
from . import rewards
from . import observers
from . import stoppers
from . import informers
from . import renderers
from .create import create
