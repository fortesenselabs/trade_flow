# ensure users can still use a non-torch version
try:
    from trade_flow.environments.generic.tensorboard.tensorboard import (
        TensorBoardCallback,
        TensorboardLogger,
    )

    TBLogger = TensorboardLogger
    TBCallback = TensorBoardCallback
except ModuleNotFoundError:
    from trade_flow.environments.generic.tensorboard.base_tensorboard import (
        BaseTensorBoardCallback,
        BaseTensorboardLogger,
    )

    TBLogger = BaseTensorboardLogger  # type: ignore
    TBCallback = BaseTensorBoardCallback  # type: ignore

__all__ = ("TBLogger", "TBCallback")